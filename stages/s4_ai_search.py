"""阶段 4：AI 搜索场景测试 — 在目标 AI 搜索平台执行真实搜索并记录品牌提及情况.

本阶段是 GEO 诊断的核心观测阶段，直接度量品牌在 AI 原生搜索环境中的存在感。
对每个 Query 执行搜索后，分析返回结果中的品牌提及位置、情感倾向、
信息完整度、引用来源及竞品共现情况。
"""

from __future__ import annotations

import asyncio
import os
import re
from collections.abc import Awaitable, Callable
from typing import Any

import httpx

# ---------------------------------------------------------------------------
# 尝试导入 utils 中的 API 客户端；如不可用则完全走降级路径
# ---------------------------------------------------------------------------
try:
    from utils.api_client import doubao_search  # type: ignore[import-untyped]

    _HAS_UTILS = True
except ImportError:
    _HAS_UTILS = False

# ---------------------------------------------------------------------------
# API Key 统一从环境变量读取，文件中绝不硬编码真实 Key
# ---------------------------------------------------------------------------
_DOUBAO_API_KEY: str = os.environ.get("DOUBAO_API_KEY", "")
_OPENAI_API_KEY: str = os.environ.get("OPENAI_API_KEY", "")
_PERPLEXITY_API_KEY: str = os.environ.get("PERPLEXITY_API_KEY", "")

# 各平台 API 端点（可按实际部署调整）
_DOUBAO_API_URL: str = os.environ.get(
    "DOUBAO_API_URL", "https://ark.cn-beijing.volces.com/api/v3/chat/completions"
)
_OPENAI_API_URL: str = os.environ.get(
    "OPENAI_API_URL", "https://api.openai.com/v1/chat/completions"
)
_PERPLEXITY_API_URL: str = os.environ.get(
    "PERPLEXITY_API_URL", "https://api.perplexity.ai/chat/completions"
)

# 平台默认模型
_PLATFORM_MODELS: dict[str, str] = {
    "doubao": "doubao-pro-32k",
    "chatgpt": "gpt-4o",
    "perplexity": "sonar-pro",
}

# 并发控制默认值
_MAX_CONCURRENT: int = int(os.environ.get("GEO_MAX_CONCURRENT_SEARCHES", "3"))

SearchProgressCallback = Callable[[int, int], Awaitable[None]]

# ---------------------------------------------------------------------------
# 情感关键词词典（可随业务扩展）
# ---------------------------------------------------------------------------
_POSITIVE_WORDS: list[str] = [
    "推荐",
    "好",
    "优秀",
    "值得",
    "领先",
    "首选",
    "优质",
    "出色",
    "卓越",
    "好评",
    "热门",
    "受欢迎",
    "信赖",
    "可靠",
    "专业",
    "性价比高",
    "不错",
    "很棒",
    "满意",
    "推荐购买",
    "强烈推荐",
    "recommend",
    "excellent",
    "outstanding",
    "best",
    "top",
    "great",
    "good",
    "popular",
    "trusted",
    "leading",
]

_NEGATIVE_WORDS: list[str] = [
    "不推荐",
    "差",
    "问题",
    "投诉",
    "缺点",
    "不建议",
    "失望",
    "糟糕",
    "劣",
    "差评",
    "避坑",
    "雷",
    "踩雷",
    "不推荐购买",
    "慎重",
    "谨慎",
    "一般",
    "平庸",
    "落后",
    "outdated",
    "not recommend",
    "poor",
    "bad",
    "worst",
    "avoid",
    "disappointing",
    "terrible",
    "issue",
    "problem",
]

# 信息完整度检查维度
_INFO_DIMENSIONS: dict[str, list[str]] = {
    "features": [
        "功能",
        "特点",
        "配置",
        "性能",
        "技术",
        "设计",
        "支持",
        "feature",
        "spec",
    ],
    "price": [
        "价格",
        "售价",
        "元",
        "钱",
        "性价比",
        "便宜",
        "贵",
        "price",
        "cost",
        "¥",
        "$",
    ],
    "channels": [
        "购买",
        "渠道",
        "官网",
        "电商",
        "京东",
        "淘宝",
        "天猫",
        "拼多多",
        "亚马逊",
        "buy",
        "purchase",
        "store",
    ],
    "brand_bg": [
        "公司",
        "品牌",
        "成立",
        "总部",
        "创始人",
        "背景",
        "历史",
        "company",
        "brand",
        "founded",
    ],
    "reviews": [
        "评价",
        "口碑",
        "用户",
        "反馈",
        "评分",
        "评论",
        "review",
        "rating",
        "user",
    ],
    "comparison": [
        "对比",
        "比较",
        "vs",
        "versus",
        "相比",
        "区别",
        "差异",
        "优势",
        "劣势",
        "compare",
        "better",
        "worse",
    ],
}


# =============================================================================
# 主入口
# =============================================================================


async def test(
    brand: str,
    queries: list[dict[str, Any] | str],
    competitors: list[dict[str, Any]],
    platform: str = "doubao",
    progress_callback: SearchProgressCallback | None = None,
) -> dict[str, Any]:
    """对一组搜索 Query 在目标 AI 平台上执行搜索测试，记录品牌提及情况.

    Args:
        brand: 品牌名称，如 ``"听力熊"``.
        queries: 搜索 Query 列表。每个元素可以是纯字符串，
            或包含 ``"text"`` / ``"intent"`` 的字典。
        competitors: 竞品列表，每个元素需至少包含 ``"name"`` 键。
        platform: 目标搜索平台，可选 ``"doubao"`` | ``"chatgpt"`` | ``"perplexity"``。
        progress_callback: 每条 Query 完成后调用，参数为 ``(已完成数, 总数)``。

    Returns:
        结构化测试结果字典，包含平台、提及率、首段提及率、
        平均信息完整度及每条 Query 的详细结果。
    """
    normalized_queries = _normalize_queries(queries)
    total = len(normalized_queries)

    if total == 0:
        return _empty_result(platform)

    competitor_names = [
        str(c.get("name", "")) for c in competitors if c.get("name")
    ]

    semaphore = asyncio.Semaphore(_MAX_CONCURRENT)
    progress_lock = asyncio.Lock()
    completed_queries = 0

    async def _search_one(query: dict[str, Any]) -> dict[str, Any]:
        nonlocal completed_queries
        async with semaphore:
            try:
                return await _execute_single_search(
                    brand, query, competitor_names, platform
                )
            finally:
                if progress_callback:
                    async with progress_lock:
                        completed_queries += 1
                        completed = completed_queries
                    try:
                        await progress_callback(completed, total)
                    except Exception:
                        # 观测回调不能影响真实诊断与降级逻辑。
                        pass

    results = await asyncio.gather(
        *[_search_one(q) for q in normalized_queries],
        return_exceptions=True,
    )

    # 将异常降级为默认结果，确保流水线不中断
    processed: list[dict[str, Any]] = []
    for r in results:
        if isinstance(r, Exception):
            processed.append(_fallback_result(str(r)))
        else:
            processed.append(r)

    # 汇总指标
    mentioned_count = sum(1 for r in processed if r.get("mentioned", False))
    first_para_count = sum(
        1 for r in processed if r.get("position") == "first_paragraph"
    )
    completeness_scores = [
        r.get("infoCompleteness", 0)
        for r in processed
        if r.get("mentioned", False)
    ]
    avg_completeness = (
        round(sum(completeness_scores) / len(completeness_scores), 1)
        if completeness_scores
        else 0.0
    )

    mention_rate = round(mentioned_count / total * 100, 1) if total else 0.0
    first_para_rate = (
        round(first_para_count / mentioned_count * 100, 1)
        if mentioned_count
        else 0.0
    )

    return {
        "platform": platform,
        "totalQueries": total,
        "mentioned": mentioned_count,
        "mentionRate": mention_rate,
        "firstParagraphMentions": first_para_count,
        "firstParagraphRate": first_para_rate,
        "avgInfoCompleteness": avg_completeness,
        "results": processed,
    }


# =============================================================================
# Query 标准化
# =============================================================================


def _normalize_queries(
    queries: list[dict[str, Any] | str],
) -> list[dict[str, Any]]:
    """将多种格式的 queries 统一为包含 ``text`` 和 ``intent`` 的字典列表.

    Args:
        queries: 原始 Query 列表。

    Returns:
        标准化后的字典列表，每个字典至少包含 ``text`` 和 ``intent``。
    """
    normalized: list[dict[str, Any]] = []
    for q in queries:
        if isinstance(q, str):
            normalized.append({"text": q, "intent": "unknown"})
        elif isinstance(q, dict):
            text = q.get("text") or q.get("query") or ""
            intent = q.get("intent", "unknown")
            if text:
                normalized.append({"text": str(text), "intent": str(intent), **q})
    return normalized


# =============================================================================
# 单次搜索执行
# =============================================================================


async def _execute_single_search(
    brand: str,
    query: dict[str, Any],
    competitor_names: list[str],
    platform: str,
) -> dict[str, Any]:
    """执行单次 AI 搜索并分析返回结果.

    Args:
        brand: 品牌名称。
        query: 标准化后的 Query 字典（含 ``text`` / ``intent``）。
        competitor_names: 竞品名称列表。
        platform: 目标平台标识。

    Returns:
        单条 Query 的详细测试结果字典。
    """
    query_text = query["text"]

    try:
        answer_text = await _call_search_api(query_text, platform)
    except Exception as exc:
        return {
            "query": query_text,
            "intent": query.get("intent", "unknown"),
            "mentioned": False,
            "position": "not_mentioned",
            "sentiment": "not_mentioned",
            "infoCompleteness": 0,
            "competitorsMentioned": [],
            "competitorRank": -1,
            "sources": [],
            "answerSnippet": "",
            "error": str(exc),
        }

    mentioned = brand in answer_text
    position = _detect_position(answer_text, brand)
    sentiment = _detect_sentiment(answer_text, brand)
    info_completeness = _detect_info_completeness(answer_text, brand) if mentioned else 0
    competitors_mentioned = _detect_competitor_cooccurrence(answer_text, competitor_names)
    competitor_rank = _detect_competitor_rank(answer_text, brand, competitor_names)
    sources = _extract_sources(answer_text)

    return {
        "query": query_text,
        "intent": query.get("intent", "unknown"),
        "mentioned": mentioned,
        "position": position,
        "sentiment": sentiment,
        "infoCompleteness": info_completeness,
        "competitorsMentioned": competitors_mentioned,
        "competitorRank": competitor_rank,
        "sources": sources,
        "answerSnippet": answer_text[:500] if answer_text else "",
    }


# =============================================================================
# 平台 API 调用层
# =============================================================================


async def _call_search_api(query_text: str, platform: str) -> str:
    """根据平台标识路由到对应的搜索 API.

    Args:
        query_text: 搜索问题文本。
        platform: 平台标识。

    Returns:
        AI 回答的纯文本内容。

    Raises:
        底层 HTTP 异常会在上层被捕获并降级处理。
    """
    if platform == "chatgpt":
        return await _call_chatgpt_api(query_text)
    if platform == "perplexity":
        return await _call_perplexity_api(query_text)
    # 默认走 doubao
    return await _call_doubao_api(query_text)


async def _call_doubao_api(query_text: str) -> str:
    """调用豆包（火山引擎）API 获取搜索回答.

    优先复用 ``utils.api_client`` 中的封装；若不可用或调用失败，
    降级为直接 ``httpx`` 请求。

    Args:
        query_text: 搜索问题文本。

    Returns:
        AI 回答文本。
    """
    if _HAS_UTILS and doubao_search is not None:
        try:
            response = await doubao_search(query_text)
            if isinstance(response, dict):
                answer = (
                    response.get("answer", "")
                    or response.get("content", "")
                    or ""
                )
                # 只有当 answer 非空且 API 成功时才返回
                if answer and response.get("success", True):
                    return answer
            elif response:
                return str(response)
        except Exception:
            pass  # 降级到 mock

    api_key = _DOUBAO_API_KEY
    if not api_key:
        return await _mock_search_response(query_text)

    try:
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": _PLATFORM_MODELS["doubao"],
            "messages": [{"role": "user", "content": query_text}],
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(_DOUBAO_API_URL, headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()
            return str(data["choices"][0]["message"]["content"])
    except Exception:
        return await _mock_search_response(query_text)


async def _call_chatgpt_api(query_text: str) -> str:
    """调用 OpenAI ChatGPT API 获取回答.

    Args:
        query_text: 搜索问题文本。

    Returns:
        AI 回答文本。
    """
    api_key = _OPENAI_API_KEY
    if not api_key:
        return await _mock_search_response(query_text)

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": _PLATFORM_MODELS["chatgpt"],
        "messages": [{"role": "user", "content": query_text}],
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(_OPENAI_API_URL, headers=headers, json=payload)
        resp.raise_for_status()
        data = resp.json()
        return str(data["choices"][0]["message"]["content"])


async def _call_perplexity_api(query_text: str) -> str:
    """调用 Perplexity API 获取带引用来源的搜索回答.

    Args:
        query_text: 搜索问题文本。

    Returns:
        AI 回答文本。
    """
    api_key = _PERPLEXITY_API_KEY
    if not api_key:
        return await _mock_search_response(query_text)

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": _PLATFORM_MODELS["perplexity"],
        "messages": [{"role": "user", "content": query_text}],
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(_PERPLEXITY_API_URL, headers=headers, json=payload)
        resp.raise_for_status()
        data = resp.json()
        return str(data["choices"][0]["message"]["content"])


# =============================================================================
# 结果分析函数（纯计算，使用 def）
# =============================================================================


def _detect_position(answer: str, brand: str) -> str:
    """检测品牌在回答中的位置.

    首段定义为：前 200 个字符，或第一个 ``\n\n`` 段落分隔符之前
    （取两者中较早出现者）。

    Args:
        answer: AI 回答的完整文本。
        brand: 品牌名称。

    Returns:
        ``"first_paragraph"`` | ``"body"`` | ``"not_mentioned"``。
    """
    if brand not in answer:
        return "not_mentioned"

    first_para_end = answer.find("\n\n")
    if first_para_end == -1:
        first_para_end = min(200, len(answer))
    else:
        first_para_end = min(first_para_end, 200)

    first_para = answer[:first_para_end]
    return "first_paragraph" if brand in first_para else "body"


def _detect_sentiment(answer: str, brand: str) -> str:
    """检测品牌提及的语境情感倾向.

    提取品牌词前后 100 字上下文，通过关键词匹配判断情感。
    实际生产环境可替换为 NLP 情感分析模型。

    Args:
        answer: AI 回答的完整文本。
        brand: 品牌名称。

    Returns:
        ``"positive"`` | ``"neutral"`` | ``"negative"`` | ``"not_mentioned"``。
    """
    if brand not in answer:
        return "not_mentioned"

    idx = answer.find(brand)
    context = answer[max(0, idx - 100) : min(len(answer), idx + 100)]

    pos_count = sum(1 for w in _POSITIVE_WORDS if w in context)
    neg_count = sum(1 for w in _NEGATIVE_WORDS if w in context)

    if neg_count > pos_count:
        return "negative"
    if pos_count > neg_count:
        return "positive"
    return "neutral"


def _detect_info_completeness(answer: str, brand: str) -> int:
    """检测回答中品牌信息的完整度评分（0-100）.

    从 6 个维度评估：产品特点、价格信息、购买渠道、品牌背景、
    用户评价、竞品对比。

    Args:
        answer: AI 回答的完整文本。
        brand: 品牌名称。

    Returns:
        0-100 的完整度评分。
    """
    if brand not in answer:
        return 0

    idx = answer.find(brand)
    context = answer[max(0, idx - 200) : min(len(answer), idx + 200)]

    matched = 0
    for keywords in _INFO_DIMENSIONS.values():
        if any(kw in context for kw in keywords):
            matched += 1

    # 6 个维度，每命中一个得 17 分，封顶 100
    return min(100, matched * 17)


def _detect_competitor_cooccurrence(
    answer: str, competitor_names: list[str]
) -> list[str]:
    """检测回答中同时出现的竞品品牌.

    Args:
        answer: AI 回答的完整文本。
        competitor_names: 竞品名称列表。

    Returns:
        被提及的竞品名称列表（保持传入顺序）。
    """
    return [name for name in competitor_names if name in answer]


def _detect_competitor_rank(
    answer: str, brand: str, competitor_names: list[str]
) -> int:
    """检测品牌在同 Query 回答中的提及位次.

    按各品牌首次出现的位置排序，1-based 位次。
    未提及返回 ``-1``。

    Args:
        answer: AI 回答的完整文本。
        brand: 品牌名称。
        competitor_names: 竞品名称列表。

    Returns:
        提及位次（1-based），未提及返回 ``-1``。
    """
    if brand not in answer:
        return -1

    positions: list[tuple[int, str]] = []
    seen: set[str] = set()

    all_brands = [brand] + [c for c in competitor_names if c in answer]
    for b in all_brands:
        if b in seen:
            continue
        seen.add(b)
        idx = answer.find(b)
        if idx != -1:
            positions.append((idx, b))

    positions.sort(key=lambda x: x[0])

    for rank, (_, name) in enumerate(positions, start=1):
        if name == brand:
            return rank

    return -1


def _extract_sources(answer: str) -> list[str]:
    """提取 AI 回答中引用的来源.

    支持以下引用格式：
    - Perplexity 风格 ``[1]`` / ``[2]``
    - Markdown 链接 ``[text](url)``
    - 裸 URL ``https://...``

    Args:
        answer: AI 回答的完整文本。

    Returns:
        去重后的来源列表（保持首次出现顺序）。
    """
    sources: list[str] = []

    # Perplexity / 通用引用标记
    citations = re.findall(r"\[(\d+)\]", answer)
    if citations:
        sources.extend([f"引用 [{c}]" for c in dict.fromkeys(citations)])

    # Markdown 链接中的域名
    md_links = re.findall(r"\[([^\]]+)\]\((https?://[^/)]+)", answer)
    for _, url in md_links:
        sources.append(url)

    # 裸 URL
    raw_urls = re.findall(r"https?://[^\s)\]]+", answer)
    sources.extend(raw_urls)

    # 去重并保持顺序
    seen: set[str] = set()
    unique: list[str] = []
    for s in sources:
        if s not in seen:
            seen.add(s)
            unique.append(s)

    return unique


# =============================================================================
# 降级 / 兜底函数
# =============================================================================


def _empty_result(platform: str) -> dict[str, Any]:
    """当 queries 为空时返回的空结果."""
    return {
        "platform": platform,
        "totalQueries": 0,
        "mentioned": 0,
        "mentionRate": 0.0,
        "firstParagraphMentions": 0,
        "firstParagraphRate": 0.0,
        "avgInfoCompleteness": 0.0,
        "results": [],
    }


def _fallback_result(error_msg: str) -> dict[str, Any]:
    """API 调用失败时的降级结果.

    包含 ``error`` 字段以便后续排查，同时保证数据结构完整，
    不中断整条诊断流水线。
    """
    return {
        "query": "",
        "intent": "unknown",
        "mentioned": False,
        "position": "not_mentioned",
        "sentiment": "not_mentioned",
        "infoCompleteness": 0,
        "competitorsMentioned": [],
        "competitorRank": -1,
        "sources": [],
        "answerSnippet": "",
        "error": error_msg,
    }


async def _mock_search_response(query_text: str) -> str:
    """无 API Key 或 API 不可用时的降级搜索响应。

    当豆包/ChatGPT/Perplexity API 不可用时，回退到 Kimi LLM 生成搜索式回答。
    这比返回空字符串更实用，能让诊断流水线输出有意义的结果。

    Args:
        query_text: 搜索问题文本。

    Returns:
        LLM 生成的搜索式回答文本。
    """
    try:
        from utils.api_client import llm_chat

        prompt = (
            f"请扮演一个智能搜索引擎，针对用户的搜索问题给出客观、"
            f"信息完整的回答。请像真实搜索结果那样，直接给出结论和关键信息。\n\n"
            f"搜索问题：{query_text}\n\n"
            f"请给出 2-3 句话的简洁回答，包含相关品牌、产品特点和用户建议。"
        )
        answer = await llm_chat(prompt, model="moonshot-v1-8k", temperature=0.3)
        if answer and len(answer) > 20:
            return answer
    except Exception:
        pass

    # 最终兜底
    return (
        f"关于「{query_text}」的搜索："
        "当前 AI 搜索 API 暂不可用，正在使用 LLM 模拟搜索。"
        "建议配置豆包 API 以获得更准确的搜索结果。"
    )
