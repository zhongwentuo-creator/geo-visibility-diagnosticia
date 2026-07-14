"""Stage 6: 舆情健康度扫描 (Sentiment Health Scanner)

stages/s6_sentiment.py

多平台舆情抓取与情感分析，计算品牌负面率、风险等级与情感分布。

功能:
1. 通过通用搜索 API 获取品牌在各平台的舆情内容
2. 基于关键词库对内容进行情感分类（正面 / 中性 / 负面）
3. 计算负面率、风险等级、情感分布
4. 提取 Top 负面问题与来源平台
5. 搜索 API 不可用时降级为 LLM 分析，LLM 也不可用时返回标记为数据缺失的默认值

输出格式:
{
    "negativeRate": float,          # 0-100，-1 表示数据缺失
    "riskLevel": str,               # "低风险" | "中低风险" | "中风险" | "高风险" | "极高风险" | "数据缺失"
    "sentimentDistribution": {
        "positive": float,          # 百分比
        "neutral": float,
        "negative": float
    },
    "topIssues": [...],             # {"issue": str, "platform": str, "severity": str}
    "negativeSources": [...],       # {"platform": str, "content": str}
    "positiveSources": [...],       # {"platform": str, "content": str}
    "stageStatus": str,             # "completed" | "degraded"
    "elapsedMs": int,
    "recordCount": int,
    "dataQuality": str              # "full" | "degraded"
}
"""

from __future__ import annotations

import asyncio
import json
import os
import time
from collections import Counter
from typing import Any

import httpx


# ═══════════════════════════════════════════════════════════════
# 环境配置
# ═══════════════════════════════════════════════════════════════

# 环境变量在函数内动态读取，避免 .env 加载顺序问题
# 同上
# 同上

# 搜索并发控制
MAX_CONCURRENT_SEARCHES: int = int(os.environ.get("MAX_CONCURRENT_SEARCHES", "2"))


# ═══════════════════════════════════════════════════════════════
# 情感关键词库
# ═══════════════════════════════════════════════════════════════

NEGATIVE_KEYWORDS: list[str] = [
    # 通用负面
    "投诉", "维权", "售后差", "质量差", "假货", "欺骗", "虚假宣传", "坑", "骗",
    "问题", "差评", "后悔", "失望", "不好用", "不推荐", "踩雷", "拔草", "避雷",
    "吐槽", "负面", "曝光", "丑闻", "危机", "处罚", "违规", "召回", "故障",
    "破损", "过期", "欺诈", "侵权", "诉讼", "仲裁", "退款", "退货", "赔偿",
    "恶心", "垃圾", "烂", "差劲", "糟糕", "恶劣", "不靠谱", "不值得", "别买",
    "千万别买", "上当", "受骗", "黑心", "无良", "倒闭", "跑路", "拉黑",
    # 产品质量
    "品控差", "容易坏", "用不了", "卡顿", "死机", "发热", "漏电", "异味",
    # 服务体验
    "客服不理", "推诿", "拖延", "敷衍", "态度差", "不给退", "拒赔",
]

POSITIVE_KEYWORDS: list[str] = [
    # 通用正面
    "推荐", "好评", "满意", "不错", "好用", "值得", "喜欢", "优秀",
    "性价比高", "给力", "惊喜", "良心", "种草", "安利", "好评如潮", "赞",
    "完美", "出色", "领先", "首选", "优质", "可靠", "放心", "省心", "值得信赖",
    "再买", "回购", "强烈推荐", "必买", "五星", "好评", "给力", "真香",
    # 产品质量
    "质量好", "做工精细", "用料足", "耐用", "稳定", "流畅", "清晰",
    # 服务体验
    "服务好", "发货快", "包装好", "售后无忧", "客服耐心",
]

ISSUE_TYPE_MAP: dict[str, list[str]] = {
    "售后问题": ["售后", "客服", "维修", "保修", "服务", "退换", "退款", "拒赔"],
    "质量问题": ["质量", "品控", "故障", "损坏", "瑕疵", "容易坏", "卡顿", "死机"],
    "虚假宣传": ["虚假宣传", "夸大", "误导", "欺骗", "不实", "图文不符"],
    "价格争议": ["贵", "涨价", "不值", "性价比低", "降价", "割韭菜"],
    "物流问题": ["物流", "快递", "发货", "配送", "慢", "丢件", "破损"],
    "安全问题": ["安全", "漏电", "爆炸", "自燃", "中毒", "伤害", "隐患"],
}


# ═══════════════════════════════════════════════════════════════
# 主入口
# ═══════════════════════════════════════════════════════════════

async def scan(brand: str) -> dict:
    """舆情健康度扫描主函数。

    并行搜索品牌在多平台的舆情内容，进行情感分析并汇总。
    搜索失败时自动降级为 LLM 分析，LLM 也不可用时返回数据缺失标记。

    Args:
        brand: 品牌名称，如 "听力熊"。

    Returns:
        舆情扫描结果字典，包含负面率、风险等级、情感分布、
        Top 问题、正负来源等字段。
    """
    start_ts = time.time()
    record_count = 0

    async with httpx.AsyncClient(timeout=30.0) as client:
        # 1️⃣ 尝试通过搜索 API 获取真实舆情数据
        search_items = await _fetch_search_results(brand, client)
        record_count = len(search_items)

        if search_items:
            # 搜索成功 → 关键词情感分析 → 汇总
            for item in search_items:
                text = f"{item.get('title', '')} {item.get('content', '')}"
                item["sentiment"] = _keyword_sentiment(text)
                item.setdefault("platform", _infer_platform(item.get("url", ""), item.get("title", "")))

            result = _aggregate_results(search_items)
            result["dataQuality"] = "full"
            result["stageStatus"] = "completed"
        else:
            # 2️⃣ 搜索失败 → 尝试 LLM Fallback
            llm_result = await _llm_sentiment_fallback(brand, client)
            if llm_result:
                result = llm_result
                result["dataQuality"] = "degraded"
                result["stageStatus"] = "completed"
            else:
                # 3️⃣ 最终降级 → 返回默认值
                result = _default_result()
                result["dataQuality"] = "degraded"
                result["stageStatus"] = "degraded"

    elapsed_ms = int((time.time() - start_ts) * 1000)
    result["elapsedMs"] = elapsed_ms
    result["recordCount"] = record_count

    return result


# ═══════════════════════════════════════════════════════════════
# 数据获取层
# ═══════════════════════════════════════════════════════════════

async def _fetch_search_results(brand: str, client: httpx.AsyncClient) -> list[dict]:
    """获取搜索舆情数据。

    通过 2-3 个通用搜索查询覆盖品牌的正面与负面信息，
    按 URL 去重后推断来源平台。

    Args:
        brand: 品牌名称。
        client: httpx 异步客户端实例。

    Returns:
        搜索结果列表，每项包含 title、content、url、platform。
    """
    # 无可用搜索 API 时直接返回空列表
    if not os.environ.get("SERPAPI_KEY") and not os.environ.get("BING_SEARCH_KEY"):
        return []

    queries: list[str] = [
        f'"{brand}" 投诉 OR "{brand}" 负面 OR "{brand}" 问题',
        f'"{brand}" 评测 OR "{brand}" 体验 OR "{brand}" 推荐',
        f'"{brand}" 黑猫投诉 OR "{brand}" 小红书 OR "{brand}" 微博',
    ]

    semaphore = asyncio.Semaphore(MAX_CONCURRENT_SEARCHES)

    async def _search_with_limit(query: str) -> list[dict]:
        async with semaphore:
            try:
                return await _execute_search(query, client)
            except Exception:
                # 单个查询失败不影响其他查询
                return []

    search_tasks = [_search_with_limit(q) for q in queries]
    platform_results = await asyncio.gather(*search_tasks, return_exceptions=True)

    # 合并并去重
    all_items: list[dict] = []
    seen_urls: set[str] = set()

    for result in platform_results:
        if isinstance(result, list):
            for item in result:
                url = item.get("url", "")
                if url and url in seen_urls:
                    continue
                if url:
                    seen_urls.add(url)
                all_items.append(item)

    return all_items


async def _execute_search(query: str, client: httpx.AsyncClient) -> list[dict]:
    """执行单次搜索，按优先级尝试 SerpAPI → Bing Search API。

    Args:
        query: 搜索查询字符串。
        client: httpx 异步客户端实例。

    Returns:
        搜索结果列表。无可用 API 或请求失败时返回空列表。
    """
    # 优先级 1: SerpAPI (Google Search)
    if os.environ.get("SERPAPI_KEY"):
        try:
            return await _serpapi_search(query, client)
        except Exception:
            pass  # 降级到下一个 API

    # 优先级 2: Bing Search API
    if os.environ.get("BING_SEARCH_KEY"):
        try:
            return await _bing_search(query, client)
        except Exception:
            pass

    return []


async def _serpapi_search(query: str, client: httpx.AsyncClient) -> list[dict]:
    """通过 SerpAPI 执行 Google 搜索。

    Args:
        query: 搜索查询。
        client: httpx 异步客户端。

    Returns:
        解析后的搜索结果列表。
    """
    url = "https://serpapi.com/search"
    params: dict[str, Any] = {
        "q": query,
        "api_key": os.environ.get("SERPAPI_KEY"),
        "engine": "google",
        "num": 10,
        "hl": "zh-CN",
        "gl": "cn",
    }

    resp = await client.get(url, params=params)
    resp.raise_for_status()
    data = resp.json()

    items: list[dict] = []
    for result in data.get("organic_results", []):
        items.append({
            "title": result.get("title", ""),
            "content": result.get("snippet", ""),
            "url": result.get("link", ""),
        })
    return items


async def _bing_search(query: str, client: httpx.AsyncClient) -> list[dict]:
    """通过 Bing Search API 执行搜索。

    Args:
        query: 搜索查询。
        client: httpx 异步客户端。

    Returns:
        解析后的搜索结果列表。
    """
    url = "https://api.bing.microsoft.com/v7.0/search"
    headers = {"Ocp-Apim-Subscription-Key": os.environ.get("BING_SEARCH_KEY")}
    params: dict[str, Any] = {"q": query, "count": 10, "mkt": "zh-CN"}

    resp = await client.get(url, headers=headers, params=params)
    resp.raise_for_status()
    data = resp.json()

    items: list[dict] = []
    for result in data.get("webPages", {}).get("value", []):
        items.append({
            "title": result.get("name", ""),
            "content": result.get("snippet", ""),
            "url": result.get("url", ""),
        })
    return items


# ═══════════════════════════════════════════════════════════════
# 情感分析层
# ═══════════════════════════════════════════════════════════════

def _keyword_sentiment(text: str) -> str:
    """基于关键词库的轻量情感分析。

    统计文本中正面与负面关键词出现次数，以多数决定情感倾向。
    正负关键词数量相等时返回中性。

    Args:
        text: 待分析的文本（标题 + 摘要拼接）。

    Returns:
        "positive" | "neutral" | "negative"。
    """
    if not text:
        return "neutral"

    text_lower = text.lower()

    neg_count = sum(1 for kw in NEGATIVE_KEYWORDS if kw in text_lower)
    pos_count = sum(1 for kw in POSITIVE_KEYWORDS if kw in text_lower)

    if neg_count > pos_count:
        return "negative"
    if pos_count > neg_count:
        return "positive"
    return "neutral"


def _infer_platform(url: str, title: str) -> str:
    """根据 URL 域名或标题关键词推断内容来源平台。

    Args:
        url: 搜索结果链接。
        title: 搜索结果标题。

    Returns:
        平台名称，如 "黑猫投诉"、"小红书"、"新闻媒体" 等。
    """
    url_lower = url.lower()
    title_lower = title.lower()

    platform_rules: list[tuple[str, list[str]]] = [
        ("黑猫投诉", ["tousu.sina", "黑猫投诉"]),
        ("什么值得买", ["smzdm", "什么值得买"]),
        ("小红书", ["xiaohongshu", "小红书"]),
        ("微博", ["weibo", "微博"]),
        ("知乎", ["zhihu", "知乎"]),
        ("B站", ["bilibili", "b23.tv", "哔哩哔哩"]),
        ("抖音", ["douyin", "抖音"]),
        ("百度贴吧", ["tieba.baidu", "贴吧"]),
        ("新闻媒体", ["36kr", "donews", "geekpark", "极客公园", "虎嗅", "钛媒体"]),
    ]

    for platform, keywords in platform_rules:
        if any(kw in url_lower for kw in keywords):
            return platform
        if any(kw in title_lower for kw in keywords):
            return platform

    return "其他"


# ═══════════════════════════════════════════════════════════════
# 汇总与计算层
# ═══════════════════════════════════════════════════════════════

def _aggregate_results(items: list[dict]) -> dict:
    """汇总舆情分析结果。

    基于情感分类统计负面率、正面率、中性率，计算风险等级，
    提取 Top 问题与正负来源。

    Args:
        items: 已标注 sentiment 的搜索结果列表。

    Returns:
        汇总后的舆情结果字典。
    """
    total = len(items)
    if total == 0:
        return _default_result()

    negative = sum(1 for i in items if i.get("sentiment") == "negative")
    positive = sum(1 for i in items if i.get("sentiment") == "positive")
    neutral = total - negative - positive

    negative_rate = round(negative / total * 100, 1)
    positive_rate = round(positive / total * 100, 1)
    # 中性率通过 100 减去其他两项，避免浮点舍入误差
    neutral_rate = round(100.0 - negative_rate - positive_rate, 1)

    risk_level = _calculate_risk_level(negative_rate)
    top_issues = _extract_top_issues(items)

    negative_sources = [
        {
            "platform": i.get("platform", "未知"),
            "content": (i.get("title", "") + " — " + i.get("content", ""))[:150],
        }
        for i in items if i.get("sentiment") == "negative"
    ][:5]

    positive_sources = [
        {
            "platform": i.get("platform", "未知"),
            "content": (i.get("title", "") + " — " + i.get("content", ""))[:150],
        }
        for i in items if i.get("sentiment") == "positive"
    ][:5]

    return {
        "negativeRate": negative_rate,
        "riskLevel": risk_level,
        "sentimentDistribution": {
            "positive": positive_rate,
            "neutral": neutral_rate,
            "negative": negative_rate,
        },
        "topIssues": top_issues,
        "negativeSources": negative_sources,
        "positiveSources": positive_sources,
    }


def _calculate_risk_level(negative_rate: float) -> str:
    """根据负面率计算风险等级。

    阈值依据 PRD 定义:
        < 10%   → 低风险
        10-20%  → 中低风险
        20-30%  → 中风险
        30-50%  → 高风险
        ≥ 50%   → 极高风险

    Args:
        negative_rate: 负面率百分比 (0-100)。

    Returns:
        风险等级字符串。
    """
    if negative_rate < 0:
        return "数据缺失"
    if negative_rate < 10:
        return "低风险"
    if negative_rate < 20:
        return "中低风险"
    if negative_rate < 30:
        return "中风险"
    if negative_rate < 50:
        return "高风险"
    return "极高风险"


def _extract_top_issues(items: list[dict]) -> list[dict]:
    """从负面内容中提取 Top 问题列表。

    按问题类型和来源平台聚合，去重后返回最多 5 条。

    Args:
        items: 已标注 sentiment 的搜索结果列表。

    Returns:
        Top 问题列表，每项包含 issue、platform、severity。
    """
    negative_items = [i for i in items if i.get("sentiment") == "negative"]
    if not negative_items:
        return []

    issues: list[dict] = []
    seen: set[tuple[str, str]] = set()

    for item in negative_items:
        text = f"{item.get('title', '')} {item.get('content', '')}"
        platform = item.get("platform", "未知")

        # 匹配问题类型
        issue_type = "其他"
        for issue_name, keywords in ISSUE_TYPE_MAP.items():
            if any(kw in text for kw in keywords):
                issue_type = issue_name
                break

        key = (issue_type, platform)
        if key in seen:
            continue
        seen.add(key)

        # 严重性：黑猫投诉/安全问题 → 高；新闻媒体曝光 → 高；其他 → 中
        severity = "中"
        if platform == "黑猫投诉" or issue_type == "安全问题":
            severity = "高"
        elif platform in ("新闻媒体", "知乎") and issue_type != "其他":
            severity = "高"

        issues.append({
            "issue": issue_type,
            "platform": platform,
            "severity": severity,
        })

        if len(issues) >= 5:
            break

    return issues


def _default_result() -> dict:
    """返回默认降级结果。

    当搜索 API 与 LLM Fallback 均不可用时使用，
    负面率标记为 -1 表示数据缺失。

    Returns:
        带数据缺失标记的舆情结果字典。
    """
    return {
        "negativeRate": -1.0,
        "riskLevel": "数据缺失",
        "sentimentDistribution": {
            "positive": -1.0,
            "neutral": -1.0,
            "negative": -1.0,
        },
        "topIssues": [],
        "negativeSources": [],
        "positiveSources": [],
    }


# ═══════════════════════════════════════════════════════════════
# LLM Fallback
# ═══════════════════════════════════════════════════════════════

async def _llm_sentiment_fallback(brand: str, client: httpx.AsyncClient) -> dict | None:
    """当搜索 API 不可用时，调用 LLM 生成舆情分析结果。

    优先尝试调用 utils.api_client.llm_chat；若该模块不存在，
    则直接使用 httpx 请求 OpenAI API。

    Args:
        brand: 品牌名称。
        client: httpx 异步客户端。

    Returns:
        解析后的舆情字典；LLM 调用失败或返回格式不符时返回 None。
    """
    prompt = f'''请基于公开信息，分析品牌"{brand}"的网络舆情状况。

请严格按以下 JSON 格式输出（仅输出 JSON，不要 Markdown 代码块或其他文字）：
{{
  "negativeRate": 数字(0-100),
  "riskLevel": "低风险"|"中低风险"|"中风险"|"高风险"|"极高风险",
  "sentimentDistribution": {{
    "positive": 数字(0-100),
    "neutral": 数字(0-100),
    "negative": 数字(0-100)
  }},
  "topIssues": [
    {{"issue": "问题描述", "platform": "来源平台", "severity": "高"|"中"|"低"}}
  ],
  "negativeSources": [
    {{"platform": "平台名", "content": "负面内容摘要（50字内）"}}
  ],
  "positiveSources": [
    {{"platform": "平台名", "content": "正面内容摘要（50字内）"}}
  ]
}}

注意：
- 如果你不了解该品牌或没有检索到明显负面信息，请返回负面率 0、风险等级"低风险"、正面率 70、中性率 30、负面率 0，topIssues 为空数组。
- 确保三个情感百分比之和为 100。
- 确保 JSON 格式合法，键名与上述完全一致。'''

    # 尝试 1: 使用 utils.api_client (项目统一封装)
    try:
        from utils.api_client import llm_chat

        # 检测可用 API：有 Kimi/OpenAI Key 时用 gpt-4o-mini，否则回退到豆包
        import os
        has_openai_key = bool(
            os.environ.get("OPENAI_API_KEY") or os.environ.get("KIMI_API_KEY")
        )
        model = "gpt-4o-mini" if has_openai_key else "doubao-pro-32k"

        response_text = await llm_chat(
            prompt=prompt,
            model=model,
            response_format="text",
            temperature=0.3,
        )
        parsed = json.loads(response_text)
        if _validate_sentiment_result(parsed):
            return parsed
    except Exception:
        pass  # 降级到直接调用

    # 尝试 2: 直接调用 Kimi/OpenAI API
    api_key = os.environ.get("OPENAI_API_KEY") or os.environ.get("KIMI_API_KEY")
    if not api_key:
        return None

    try:
        resp = await client.post(
            "https://api.moonshot.cn/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": "moonshot-v1-8k",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.3,
            },
            timeout=30.0,
        )
        resp.raise_for_status()
        data = resp.json()
        content = data["choices"][0]["message"]["content"]
        parsed = json.loads(content)
        if _validate_sentiment_result(parsed):
            return parsed
    except Exception:
        return None

    return None


def _validate_sentiment_result(data: dict) -> bool:
    """验证 LLM 返回的舆情结果是否包含必要字段且类型合法。

    Args:
        data: LLM 返回的字典。

    Returns:
        True 表示验证通过，False 表示数据不完整。
    """
    required_keys = [
        "negativeRate",
        "riskLevel",
        "sentimentDistribution",
        "topIssues",
        "negativeSources",
        "positiveSources",
    ]
    for key in required_keys:
        if key not in data:
            return False

    # 验证 sentimentDistribution 子字段
    dist = data.get("sentimentDistribution", {})
    for sub_key in ("positive", "neutral", "negative"):
        if sub_key not in dist:
            return False
        if not isinstance(dist[sub_key], (int, float)):
            return False

    # 验证 negativeRate 为数字
    if not isinstance(data.get("negativeRate"), (int, float)):
        return False

    return True



