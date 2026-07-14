"""Stage 3: 竞品分析 — 自动识别同行业核心竞品并建立对标基准。"""

import json
import os
import time
from typing import Any

import httpx

from utils.api_client import llm_chat


# ───────────────────────── 品类默认竞品库（降级策略） ─────────────────────────

_DEFAULT_COMPETITOR_DB: dict[str, list[dict[str, Any]]] = {
    "儿童AI对话智能体": [
        {"name": "阿尔法蛋", "aivoScore": 80, "matchReason": "同品类儿童AI教育硬件，市场占有率高"},
        {"name": "小度", "aivoScore": 85, "matchReason": "百度生态儿童智能硬件，AI搜索可见度极高"},
        {"name": "小米", "aivoScore": 78, "matchReason": "生态链儿童智能产品，价格带覆盖广"},
        {"name": "优必选", "aivoScore": 72, "matchReason": "AI机器人教育赛道，技术积累深厚"},
        {"name": "汤姆猫", "aivoScore": 82, "matchReason": "AI儿童对话产品，同价位带，AI搜索共现率高"},
    ],
    "新能源汽车": [
        {"name": "比亚迪", "aivoScore": 88, "matchReason": "新能源汽车龙头，品牌认知度极高"},
        {"name": "特斯拉", "aivoScore": 90, "matchReason": "全球电动车标杆，AI搜索高频提及"},
        {"name": "蔚来", "aivoScore": 82, "matchReason": "高端智能电动车，用户社群活跃"},
        {"name": "小鹏", "aivoScore": 80, "matchReason": "智能驾驶技术领先，科技属性强"},
        {"name": "理想", "aivoScore": 83, "matchReason": "家庭用车定位精准，产品力突出"},
    ],
    "智能手机": [
        {"name": "华为", "aivoScore": 92, "matchReason": "国产品牌技术标杆，AI搜索提及率高"},
        {"name": "苹果", "aivoScore": 95, "matchReason": "全球高端手机标杆，品牌认知度最高"},
        {"name": "小米", "aivoScore": 85, "matchReason": "性价比与生态优势，AI可见度良好"},
        {"name": "OPPO", "aivoScore": 78, "matchReason": "线下渠道强势，影像技术突出"},
        {"name": "vivo", "aivoScore": 77, "matchReason": "设计与音质优势，用户忠诚度高"},
    ],
    "SaaS": [
        {"name": "Salesforce", "aivoScore": 92, "matchReason": "全球SaaS龙头，品牌认知度最高"},
        {"name": "HubSpot", "aivoScore": 86, "matchReason": "营销自动化标杆，内容营销强势"},
        {"name": "Zendesk", "aivoScore": 80, "matchReason": "客服SaaS领导者，品牌可见度高"},
        {"name": "Atlassian", "aivoScore": 84, "matchReason": "协作工具生态，开发者社区活跃"},
        {"name": "Notion", "aivoScore": 88, "matchReason": "产品驱动增长，AI功能集成领先"},
    ],
    "新消费": [
        {"name": "完美日记", "aivoScore": 78, "matchReason": "新消费品牌标杆，社媒运营强势"},
        {"name": "喜茶", "aivoScore": 85, "matchReason": "新茶饮头部，品牌年轻化程度高"},
        {"name": "元气森林", "aivoScore": 82, "matchReason": "健康饮料开创者，AI搜索可见度高"},
        {"name": "花西子", "aivoScore": 76, "matchReason": "国潮美妆代表，内容营销突出"},
        {"name": "三顿半", "aivoScore": 75, "matchReason": "精品咖啡创新者，用户社群活跃"},
    ],
    "__default__": [
        {"name": "行业标杆A", "aivoScore": 75, "matchReason": "品类默认竞品（自动识别失败，使用行业基准）"},
        {"name": "行业标杆B", "aivoScore": 72, "matchReason": "品类默认竞品（自动识别失败，使用行业基准）"},
        {"name": "行业标杆C", "aivoScore": 70, "matchReason": "品类默认竞品（自动识别失败，使用行业基准）"},
        {"name": "行业标杆D", "aivoScore": 68, "matchReason": "品类默认竞品（自动识别失败，使用行业基准）"},
        {"name": "行业标杆E", "aivoScore": 65, "matchReason": "品类默认竞品（自动识别失败，使用行业基准）"},
    ],
}


# ───────────────────────── 头部品牌 AIVO 分数速查表（估算） ─────────────────────────

_KNOWN_BRAND_SCORES: dict[str, int] = {
    "小度": 85,
    "阿尔法蛋": 80,
    "汤姆猫": 82,
    "小米": 78,
    "优必选": 72,
    "比亚迪": 88,
    "特斯拉": 90,
    "蔚来": 82,
    "小鹏": 80,
    "理想": 83,
    "华为": 92,
    "苹果": 95,
    "百度": 88,
    "阿里": 87,
    "腾讯": 89,
    "字节跳动": 90,
    "京东": 85,
    "拼多多": 84,
    "美团": 83,
    "网易": 80,
    "Salesforce": 92,
    "HubSpot": 86,
    "Zendesk": 80,
    "Atlassian": 84,
    "Notion": 88,
    "完美日记": 78,
    "喜茶": 85,
    "元气森林": 82,
    "花西子": 76,
    "三顿半": 75,
}


# ───────────────────────── 公共函数 ─────────────────────────

async def identify(brand: str, category: str, queries: list) -> dict:
    """
    自动识别 3-5 家同行业核心竞品，并建立对标基准。

    采用三层识别策略（按优先级）：
    1. LLM 语义分析 — 基于品牌、品类信息直接推断核心竞品
    2. 搜索 API 共现分析 — 通过搜索"品牌+品类+推荐/对比"抓取共现品牌
    3. 品类默认库 — 当自动识别失败时回退到预设竞品库

    容错设计：任一策略失败时不打断流程，自动降级到下一策略。

    Args:
        brand: 品牌名称，如"听力熊"。
        category: 产品类型，如"儿童AI对话智能体"。
        queries: Stage 1 生成的典型查询列表，可为字符串列表或字典列表。
                 字典列表时提取每个元素的 "text" / "query" / "question" 字段。

    Returns:
        包含竞品列表和行业基准平均分的字典：
        {
            "competitors": [
                {
                    "name": str,           # 竞品品牌名
                    "aivoScore": int,      # 预估 AIVO 分数（0-100）
                    "matchReason": str     # 被识别为竞品的理由
                }
            ],
            "benchmarkAverage": float,     # 竞品平均分
            "competitorSource": str,       # "llm" | "search" | "default"
            "stageStatus": str,            # "success" | "degraded"
            "elapsedMs": int,              # 阶段耗时（毫秒）
            "recordCount": int             # 识别到的竞品数量
        }
    """
    start_time = time.time()
    competitors: list[dict[str, Any]] = []
    source = "default"
    status = "success"

    # ── 策略 1：LLM 语义分析 ──
    try:
        llm_competitors = await _identify_via_llm(brand, category)
        competitors = [c for c in llm_competitors if c.get("name") != brand]
        if len(competitors) >= 3:
            source = "llm"
    except Exception:
        competitors = []

    # ── 策略 2：搜索 API 共现分析（LLM 结果不足时补充） ──
    if len(competitors) < 3:
        try:
            search_competitors = await _identify_via_search(brand, category, queries)
            search_competitors = [c for c in search_competitors if c.get("name") != brand]
            _merge_competitors(competitors, search_competitors)
            if competitors and source != "llm":
                source = "search"
        except Exception:
            pass

    # ── 策略 3：品类默认竞品库（兜底） ──
    if len(competitors) < 3:
        try:
            default_competitors = _get_default_competitors(category)
            default_competitors = [c for c in default_competitors if c.get("name") != brand]
            _merge_competitors(competitors, default_competitors)
            source = "default"
            status = "degraded"
        except Exception:
            status = "degraded"

    # 限制最多 5 个竞品，按分数降序排列
    competitors = sorted(
        competitors,
        key=lambda x: x.get("aivoScore", 0),
        reverse=True,
    )[:5]

    # 确保字段完整性（兜底补全）
    for c in competitors:
        if not c.get("aivoScore"):
            c["aivoScore"] = _estimate_aivo_score(c.get("name", ""), category)
        if not c.get("matchReason"):
            c["matchReason"] = "同品类竞品"

    benchmark_avg = (
        round(sum(c["aivoScore"] for c in competitors) / len(competitors), 1)
        if competitors else 0.0
    )

    elapsed_ms = int((time.time() - start_time) * 1000)

    return {
        "competitors": competitors,
        "benchmarkAverage": benchmark_avg,
        "competitorSource": source,
        "stageStatus": status,
        "elapsedMs": elapsed_ms,
        "recordCount": len(competitors),
    }


# ───────────────────────── 内部辅助函数 ─────────────────────────

async def _identify_via_llm(brand: str, category: str) -> list[dict[str, Any]]:
    """
    通过 LLM 语义分析识别核心竞品。

    向 LLM 提供品牌和品类信息，要求其返回结构化的竞品列表。

    Args:
        brand: 品牌名称。
        category: 产品类型。

    Returns:
        LLM 返回的竞品字典列表，每个字典包含 name、aivoScore、matchReason。
        解析失败或 API 异常时返回空列表，不打断上层流程。
    """
    prompt = f"""你是一个资深的行业研究分析师。请基于以下信息，识别该品牌最直接的核心竞品。

品牌名称：{brand}
产品类型：{category}

要求：
1. 识别 3-5 家同品类、同价位带、目标用户重叠度高的真实品牌
2. 严格排除品牌自身"{brand}"
3. 对每家竞品给出：
   - name: 品牌名称（必须是真实存在的品牌）
   - aivoScore: 预估 AIVO 分数（0-100，基于行业地位、知名度、AI 搜索可见度估算）
   - matchReason: 匹配理由（20-50 字，说明为什么是该品牌的竞品）

输出严格 JSON 数组格式，不要有任何额外文字：
[
  {{"name": "竞品品牌名", "aivoScore": 82, "matchReason": "匹配理由"}},
  ...
]
"""

    try:
        response = await llm_chat(prompt, model="gpt-4o", response_format="json")
        data = json.loads(response)

        if isinstance(data, list):
            return _normalize_competitors(data)
        if isinstance(data, dict):
            # LLM 可能包装在 {{"competitors": [...]}} 中
            for key in ("competitors", "data", "results", "items"):
                if key in data and isinstance(data[key], list):
                    return _normalize_competitors(data[key])
            # 也可能是单条记录
            return _normalize_competitors([data])
        return []
    except Exception:
        return []


async def _identify_via_search(brand: str, category: str, queries: list) -> list[dict[str, Any]]:
    """
    通过搜索 API 获取共现品牌，并用 LLM 提取竞品。

    构造种子搜索查询（如"品牌+品类+推荐/对比"），调用通用搜索接口
    获取结果摘要，再交由 LLM 从中提取高频共现品牌。

    Args:
        brand: 品牌名称。
        category: 产品类型。
        queries: Stage 1 的查询列表，用于构造额外的种子查询。

    Returns:
        从搜索结果中提取的竞品列表。搜索失败、提取失败或 API 不可用时返回空列表。
    """
    # 提取查询文本
    query_texts = _extract_query_texts(queries)

    # 构造种子搜索查询
    seed_queries = [
        f"{brand} {category} 推荐",
        f"{brand} {category} 对比",
        f"{category} 品牌排行榜",
        f"{category} 哪个牌子好",
    ]
    # 如果 queries 中有对比/推荐类查询，优先使用
    for qt in query_texts:
        lowered = qt.lower()
        if any(kw in lowered for kw in ("对比", "vs", "和", "哪个", "推荐", "排行", "最好")):
            seed_queries.insert(0, qt)

    seed_queries = seed_queries[:5]  # 最多 5 个种子查询

    # 收集搜索结果文本
    search_snippets: list[str] = []

    # 尝试使用 SerpAPI（如果配置了）
    serpapi_key = os.environ.get("SERPAPI_KEY")
    if serpapi_key:
        async with httpx.AsyncClient(timeout=30) as client:
            for query in seed_queries:
                try:
                    resp = await client.get(
                        "https://serpapi.com/search",
                        params={
                            "engine": "google",
                            "q": query,
                            "api_key": serpapi_key,
                            "num": 5,
                            "hl": "zh-CN",
                        },
                    )
                    if resp.status_code == 200:
                        results = resp.json()
                        for item in results.get("organic_results", []):
                            search_snippets.append(item.get("title", ""))
                            search_snippets.append(item.get("snippet", ""))
                except Exception:
                    continue

    # 尝试使用 Google Custom Search（如果配置了且结果仍不足）
    if len(search_snippets) < 10:
        google_key = os.environ.get("GOOGLE_SEARCH_API_KEY")
        google_cx = os.environ.get("GOOGLE_SEARCH_CX")
        if google_key and google_cx:
            async with httpx.AsyncClient(timeout=30) as client:
                for query in seed_queries:
                    try:
                        resp = await client.get(
                            "https://www.googleapis.com/customsearch/v1",
                            params={
                                "key": google_key,
                                "cx": google_cx,
                                "q": query,
                                "num": 5,
                            },
                        )
                        if resp.status_code == 200:
                            results = resp.json()
                            for item in results.get("items", []):
                                search_snippets.append(item.get("title", ""))
                                search_snippets.append(item.get("snippet", ""))
                    except Exception:
                        continue

    # 如果没有任何搜索结果，直接返回空（不调用 LLM，避免浪费 token）
    if not search_snippets:
        return []

    # 用 LLM 从搜索结果中提取竞品
    combined_text = "\n".join(search_snippets[:15])
    prompt = f"""从以下搜索结果中，提取与"{brand}"（{category}）同品类的竞争品牌。

搜索结果：
{combined_text}

要求：
1. 只提取真实存在的品牌名称
2. 严格排除"{brand}"自身
3. 最多提取 5 个品牌
4. 对每个品牌给出简短的匹配理由

输出严格 JSON 数组格式：
[
  {{"name": "品牌名", "matchReason": "从搜索结果推断的匹配理由"}},
  ...
]
"""

    try:
        response = await llm_chat(prompt, model="gpt-4o", response_format="json")
        data = json.loads(response)
        if isinstance(data, list):
            return _normalize_competitors(data, with_score=True, category=category)
        if isinstance(data, dict):
            for key in ("competitors", "data", "results", "items"):
                if key in data and isinstance(data[key], list):
                    return _normalize_competitors(data[key], with_score=True, category=category)
        return []
    except Exception:
        return []


def _get_default_competitors(category: str) -> list[dict[str, Any]]:
    """
    根据产品类型从默认竞品库中获取竞品列表。

    匹配逻辑：
    1. 精确匹配品类名
    2. 模糊匹配：品类名包含库中关键词，或库中关键词包含品类名
    3. 无匹配时返回通用默认列表

    Args:
        category: 产品类型。

    Returns:
        匹配的默认竞品列表的深拷贝。如果没有精确匹配，返回通用默认列表。
    """
    # 精确匹配
    if category in _DEFAULT_COMPETITOR_DB:
        return [dict(c) for c in _DEFAULT_COMPETITOR_DB[category]]

    # 模糊匹配：检查 category 是否包含库中的某个关键词
    for key in _DEFAULT_COMPETITOR_DB:
        if key == "__default__":
            continue
        if key in category or category in key:
            return [dict(c) for c in _DEFAULT_COMPETITOR_DB[key]]

    # 通用默认
    return [dict(c) for c in _DEFAULT_COMPETITOR_DB["__default__"]]


def _estimate_aivo_score(brand_name: str, category: str) -> int:
    """
    基于品牌名和行业常识估算竞品的 AIVO 分数。

    此分数为预估值，仅供 Stage 3 竞品识别阶段使用。
    实际的竞品 AIVO 分数应由 Stage 4-8 基于真实测试数据重新计算。

    Args:
        brand_name: 品牌名称。
        category: 产品类型（用于未收录品牌时生成随机但稳定的分数）。

    Returns:
        预估的 AIVO 分数（0-100）。已知品牌返回固定估值，未知品牌返回
        基于哈希的稳定随机值（65-80 区间）。
    """
    if brand_name in _KNOWN_BRAND_SCORES:
        return _KNOWN_BRAND_SCORES[brand_name]

    # 基于品牌名+品类哈希生成一个稳定但随机的分数（65-80 区间）
    # 这样同一品牌在同一品类下不同运行中得到一致分数
    hash_val = hash(f"{brand_name}:{category}") % 16
    return 65 + hash_val


def _extract_query_texts(queries: list) -> list[str]:
    """
    从 queries 列表中提取纯文本查询字符串。

    支持多种输入格式：
    - 字符串列表：["查询1", "查询2"]
    - 字典列表：[{"text": "查询1"}, {"query": "查询2"}]

    Args:
        queries: 查询列表，元素可为字符串或字典。

    Returns:
        纯文本查询字符串列表。无法识别的元素被静默跳过。
    """
    texts: list[str] = []
    for q in queries:
        if isinstance(q, str):
            texts.append(q)
        elif isinstance(q, dict):
            for key in ("text", "query", "question", "content", "value"):
                if key in q and isinstance(q[key], str):
                    texts.append(q[key])
                    break
    return texts


def _normalize_competitors(
    raw: list[dict[str, Any]],
    with_score: bool = False,
    category: str = "",
) -> list[dict[str, Any]]:
    """
    将各种格式的竞品数据归一化为标准格式 {"name": ..., "aivoScore": ..., "matchReason": ...}。

    支持 LLM 返回的多种字段命名变体：name / brandName / brand 等。

    Args:
        raw: 原始竞品数据列表。
        with_score: 是否需要调用 _estimate_aivo_score 补全分数。
                     当数据来自搜索 API（无分数）时设为 True。
        category: 产品类型，用于估算分数。

    Returns:
        标准化后的竞品字典列表。无效元素被静默过滤。
    """
    normalized: list[dict[str, Any]] = []
    for item in raw:
        if not isinstance(item, dict):
            continue

        # 支持多种 name 字段命名
        name = item.get("name") or item.get("brandName") or item.get("brand")
        if not name or not isinstance(name, str):
            continue

        name = name.strip()
        if not name:
            continue

        # 分数处理
        if with_score or "aivoScore" not in item:
            score = _estimate_aivo_score(name, category)
        else:
            score = item.get("aivoScore", 0)
            if not isinstance(score, int):
                try:
                    score = int(score)
                except (TypeError, ValueError):
                    score = _estimate_aivo_score(name, category)

        # 匹配理由
        reason = item.get("matchReason") or item.get("reason") or item.get("description") or ""
        if not reason:
            reason = "同品类竞品"

        normalized.append({
            "name": name,
            "aivoScore": score,
            "matchReason": reason,
        })

    return normalized


def _merge_competitors(
    base: list[dict[str, Any]],
    incoming: list[dict[str, Any]],
) -> None:
    """
    将 incoming 中的竞品合并到 base 中，按品牌名去重。

    合并规则：如果 incoming 中的竞品已存在于 base，则保留 base 中的版本
    （因为 base 通常来自更高优先级的识别策略，分数更可靠）。

    Args:
        base: 基础竞品列表（就地修改）。
        incoming: 待合并的竞品列表。
    """
    existing_names = {c["name"] for c in base}
    for c in incoming:
        name = c.get("name")
        if name and name not in existing_names:
            base.append(c)
            existing_names.add(name)
