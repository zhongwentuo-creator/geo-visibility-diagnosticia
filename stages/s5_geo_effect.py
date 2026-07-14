"""
阶段 5：GEO 效果汇总（GEO_EFFECT）

聚合 Stage 4 的多平台 AI 搜索测试数据，生成跨平台的 GEO 效果总览。
核心产出：
1. 跨平台汇总统计（提及率、首段提及率、情感分布、意图分布）
2. 竞品共现矩阵（品牌与竞品在同一回答中共同出现的频率与位置分析）
3. 信息缺失模式（未提及 Query 的共性特征归类与优化建议）

输入：
    ai_search_results: Stage 4 产出的单平台或多平台搜索结果（见 s4_ai_search.test 返回结构）
    competitors:     Stage 3 产出的竞品列表

输出：
    {
        "crossPlatformSummary": {...},
        "competitorCoOccurrence": [...],
        "missingPatterns": [...]
    }
"""

from __future__ import annotations

from collections import Counter, defaultdict
from typing import Any

# ---------------------------------------------------------------------------
# 常量
# ---------------------------------------------------------------------------

# 意图类型集合，用于归类未知意图
KNOWN_INTENTS: set[str] = {"信息型", "对比型", "交易型", "导航型"}

# 情感类型集合
KNOWN_SENTIMENTS: set[str] = {"positive", "neutral", "negative", "not_mentioned"}

# 提及位置类型
KNOWN_POSITIONS: set[str] = {"first_paragraph", "body", "not_mentioned"}

# 缺失模式的最小样本数（低于此值不生成模式）
MIN_PATTERN_SAMPLE: int = 2

# ---------------------------------------------------------------------------
# 主入口
# ---------------------------------------------------------------------------


def summarize(ai_search_results: dict[str, Any], competitors: list[dict[str, Any]]) -> dict[str, Any]:
    """
    汇总 GEO 搜索效果数据，生成跨平台洞察、竞品共现矩阵和信息缺失模式。

    Args:
        ai_search_results: Stage 4 返回的搜索结果字典，结构如下：
            {
                "platform": str,
                "totalQueries": int,
                "mentioned": int,
                "mentionRate": float,
                "firstParagraphMentions": int,
                "firstParagraphRate": float,
                "results": [
                    {
                        "query": str,
                        "intent": str,              # 信息型/对比型/交易型/导航型
                        "mentioned": bool,
                        "position": str,            # first_paragraph / body / not_mentioned
                        "sentiment": str,           # positive / neutral / negative / not_mentioned
                        "competitorsMentioned": list[str],
                        "answerSnippet": str
                    }
                ]
            }
        competitors: Stage 3 返回的竞品列表，每项至少包含：
            {"brandName": str, ...}

    Returns:
        dict: 包含 crossPlatformSummary、competitorCoOccurrence、missingPatterns 的汇总字典
    """
    # --- 防御性校验：确保 results 字段存在且为列表 ---
    results: list[dict[str, Any]] = ai_search_results.get("results") or []
    if not isinstance(results, list):
        results = []

    total_queries: int = ai_search_results.get("totalQueries") or len(results)
    platform: str = ai_search_results.get("platform", "unknown")

    # ===================================================================
    # 1. 跨平台汇总
    # ===================================================================
    cross_platform_summary = _build_cross_platform_summary(
        platform=platform,
        total_queries=total_queries,
        results=results,
    )

    # ===================================================================
    # 2. 竞品共现矩阵
    # ===================================================================
    competitor_names: list[str] = [c.get("name", "") for c in competitors if c.get("name")]
    competitor_co_occurrence = _build_competitor_co_occurrence(
        results=results,
        competitor_names=competitor_names,
    )

    # ===================================================================
    # 3. 信息缺失模式
    # ===================================================================
    missing_patterns = _build_missing_patterns(results=results)

    return {
        "crossPlatformSummary": cross_platform_summary,
        "competitorCoOccurrence": competitor_co_occurrence,
        "missingPatterns": missing_patterns,
    }


# ---------------------------------------------------------------------------
# 子函数：跨平台汇总
# ---------------------------------------------------------------------------


def _build_cross_platform_summary(
    platform: str,
    total_queries: int,
    results: list[dict[str, Any]],
) -> dict[str, Any]:
    """
    构建跨平台 GEO 效果汇总统计。

    当前实现支持单平台数据；若未来接入多平台，可将 platform 扩展为列表聚合。
    """
    # 基础计数
    total_mentions: int = sum(1 for r in results if r.get("mentioned") is True)
    first_para_mentions: int = sum(
        1 for r in results if r.get("position") == "first_paragraph"
    )

    # 安全计算比率
    mention_rate: float = round(total_mentions / total_queries * 100, 1) if total_queries else 0.0
    first_para_rate: float = round(first_para_mentions / total_queries * 100, 1) if total_queries else 0.0

    # 情感分布
    sentiment_counter: Counter = Counter()
    for r in results:
        sentiment: str = r.get("sentiment", "not_mentioned")
        if sentiment not in KNOWN_SENTIMENTS:
            sentiment = "not_mentioned"
        sentiment_counter[sentiment] += 1

    sentiment_breakdown: dict[str, int] = {
        "positive": sentiment_counter.get("positive", 0),
        "neutral": sentiment_counter.get("neutral", 0),
        "negative": sentiment_counter.get("negative", 0),
        "notMentioned": sentiment_counter.get("not_mentioned", 0),
    }

    # 意图分布（按提及 / 未提及分组统计）
    intent_stats: dict[str, dict[str, int]] = defaultdict(lambda: {"total": 0, "mentioned": 0})
    for r in results:
        intent: str = r.get("intent", "未知")
        if not intent or not isinstance(intent, str):
            intent = "未知"
        intent_stats[intent]["total"] += 1
        if r.get("mentioned") is True:
            intent_stats[intent]["mentioned"] += 1

    intent_breakdown: list[dict[str, Any]] = []
    for intent, stats in sorted(intent_stats.items()):
        total: int = stats["total"]
        mentioned: int = stats["mentioned"]
        rate: float = round(mentioned / total * 100, 1) if total else 0.0
        intent_breakdown.append(
            {
                "intent": intent,
                "totalQueries": total,
                "mentioned": mentioned,
                "mentionRate": rate,
            }
        )

    # 位置分布
    position_counter: Counter = Counter()
    for r in results:
        pos: str = r.get("position", "not_mentioned")
        if pos not in KNOWN_POSITIONS:
            pos = "not_mentioned"
        position_counter[pos] += 1

    position_breakdown: dict[str, int] = {
        "firstParagraph": position_counter.get("first_paragraph", 0),
        "body": position_counter.get("body", 0),
        "notMentioned": position_counter.get("not_mentioned", 0),
    }

    # 平台层级汇总（预留多平台扩展结构）
    platform_breakdown: list[dict[str, Any]] = [
        {
            "platform": platform,
            "totalQueries": total_queries,
            "mentions": total_mentions,
            "mentionRate": mention_rate,
            "firstParagraphMentions": first_para_mentions,
            "firstParagraphRate": first_para_rate,
        }
    ]

    return {
        "overallMentionRate": mention_rate,
        "overallFirstParagraphRate": first_para_rate,
        "totalQueries": total_queries,
        "totalMentions": total_mentions,
        "platformBreakdown": platform_breakdown,
        "sentimentBreakdown": sentiment_breakdown,
        "intentBreakdown": intent_breakdown,
        "positionBreakdown": position_breakdown,
    }


# ---------------------------------------------------------------------------
# 子函数：竞品共现矩阵
# ---------------------------------------------------------------------------


def _build_competitor_co_occurrence(
    results: list[dict[str, Any]],
    competitor_names: list[str],
) -> list[dict[str, Any]]:
    """
    统计每个竞品与品牌在同一回答中的共现次数、共现率及位置关系。

    分析维度：
    - coOccurrenceCount: 共现次数
    - coOccurrenceRate: 共现率（共现次数 / 品牌被提及的总次数）
    - positionSummary: 品牌在共现 query 中的位置汇总（领先/落后/持平）
    - coOccurrenceQueries: 发生共现的具体 query 列表
    """
    if not competitor_names:
        return []

    # 品牌被提及的总次数（用于计算共现率分母）
    brand_mentioned_results: list[dict[str, Any]] = [
        r for r in results if r.get("mentioned") is True
    ]
    brand_mention_total: int = len(brand_mentioned_results)

    co_occurrence_list: list[dict[str, Any]] = []

    for comp_name in competitor_names:
        comp_co_queries: list[dict[str, Any]] = []
        position_counts: Counter = Counter()

        for r in brand_mentioned_results:
            comp_mentioned_list: list[str] = r.get("competitorsMentioned") or []
            if comp_name in comp_mentioned_list:
                query_info: dict[str, Any] = {
                    "query": r.get("query", ""),
                    "brandPosition": r.get("position", "body"),
                }
                comp_co_queries.append(query_info)
                position_counts[r.get("position", "body")] += 1

        co_count: int = len(comp_co_queries)
        if co_count == 0:
            # 无共现时仍输出占位项，保持矩阵完整性
            co_occurrence_list.append(
                {
                    "competitorName": comp_name,
                    "coOccurrenceCount": 0,
                    "coOccurrenceRate": 0.0,
                    "coOccurrenceQueries": [],
                    "positionSummary": "no_cooccurrence",
                }
            )
            continue

        # 共现率 = 共现次数 / 品牌总提及次数
        co_rate: float = round(co_count / brand_mention_total * 100, 1) if brand_mention_total else 0.0

        # 位置关系摘要
        position_summary: str = _summarize_position(position_counts)

        co_occurrence_list.append(
            {
                "competitorName": comp_name,
                "coOccurrenceCount": co_count,
                "coOccurrenceRate": co_rate,
                "coOccurrenceQueries": comp_co_queries,
                "positionSummary": position_summary,
            }
        )

    # 按共现次数降序排列
    co_occurrence_list.sort(key=lambda x: x["coOccurrenceCount"], reverse=True)
    return co_occurrence_list


def _summarize_position(position_counts: Counter) -> str:
    """
    根据品牌在共现 query 中的位置分布，生成定性摘要。

    返回：
        "brand_leading"  — 品牌多在首段出现，位置占优
        "brand_lagging"  — 品牌多在正文出现，位置劣势
        "mixed"          — 首段与正文混合出现
    """
    first_para: int = position_counts.get("first_paragraph", 0)
    body: int = position_counts.get("body", 0)
    total: int = first_para + body

    if total == 0:
        return "mixed"

    first_ratio: float = first_para / total
    if first_ratio >= 0.6:
        return "brand_leading"
    elif first_ratio <= 0.3:
        return "brand_lagging"
    return "mixed"


# ---------------------------------------------------------------------------
# 子函数：信息缺失模式
# ---------------------------------------------------------------------------


def _build_missing_patterns(results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    分析品牌未被提及的 Query，识别共性缺失模式并给出优化建议。

    识别维度：
    1. 意图型缺失 — 某类意图下提及率显著偏低
    2. 位置型缺失 — 品牌仅在正文出现、从未在首段出现（隐含缺失）
    3. 竞品主导型缺失 — 竞品被提及但品牌未被提及的 query
    """
    missing_patterns: list[dict[str, Any]] = []

    # --- 模式 A：意图型缺失 ---
    intent_stats: dict[str, dict[str, int]] = defaultdict(lambda: {"total": 0, "mentioned": 0})
    for r in results:
        intent: str = r.get("intent", "未知")
        if not intent or not isinstance(intent, str):
            intent = "未知"
        intent_stats[intent]["total"] += 1
        if r.get("mentioned") is True:
            intent_stats[intent]["mentioned"] += 1

    for intent, stats in intent_stats.items():
        total: int = stats["total"]
        mentioned: int = stats["mentioned"]
        if total < MIN_PATTERN_SAMPLE:
            continue
        rate: float = mentioned / total * 100 if total else 100.0
        if rate < 50.0:
            # 收集属于该缺失模式的未提及 query
            affected_queries: list[str] = [
                r.get("query", "")
                for r in results
                if r.get("intent") == intent and r.get("mentioned") is not True
            ]
            missing_patterns.append(
                {
                    "patternType": "意图型缺失",
                    "description": f"{intent}查询中品牌提及率仅 {rate:.1f}%（{mentioned}/{total}），显著低于整体水平",
                    "affectedQueries": [q for q in affected_queries if q],
                    "recommendation": _recommendation_for_intent(intent),
                }
            )

    # --- 模式 B：竞品主导型缺失 ---
    # 找出竞品被提及但品牌未被提及的 query
    competitor_only_queries: list[str] = []
    for r in results:
        if r.get("mentioned") is not True:
            comp_list: list[str] = r.get("competitorsMentioned") or []
            if comp_list:
                competitor_only_queries.append(r.get("query", ""))

    if len(competitor_only_queries) >= MIN_PATTERN_SAMPLE:
        missing_patterns.append(
            {
                "patternType": "竞品主导型缺失",
                "description": f"存在 {len(competitor_only_queries)} 个查询中竞品被提及但本品牌缺失",
                "affectedQueries": [q for q in competitor_only_queries if q],
                "recommendation": "针对竞品高频出现的搜索场景，补充品牌对比评测和差异化内容",
            }
        )

    # --- 模式 C：首段缺失（品牌在正文中被提及但从未出现在首段）---
    body_only_count: int = sum(
        1 for r in results if r.get("position") == "body"
    )
    first_para_count: int = sum(
        1 for r in results if r.get("position") == "first_paragraph"
    )
    if body_only_count > 0 and first_para_count == 0:
        body_only_queries: list[str] = [
            r.get("query", "")
            for r in results
            if r.get("position") == "body"
        ]
        missing_patterns.append(
            {
                "patternType": "首段可见性缺失",
                "description": f"品牌在 {body_only_count} 个查询中仅出现在正文段落，从未进入首段推荐",
                "affectedQueries": [q for q in body_only_queries if q],
                "recommendation": "优化品牌权威信息源（百科、官网结构化数据、权威媒体报道），提升 AI 首段引用优先级",
            }
        )

    return missing_patterns


def _recommendation_for_intent(intent: str) -> str:
    """根据意图类型返回针对性的 GEO 优化建议。"""
    recommendations: dict[str, str] = {
        "信息型": "在知识库型平台（知乎、百度百科）增加品牌产品科普内容，提升信息型查询覆盖率",
        "对比型": "发布官方产品对比指南，与主流竞品进行差异化定位，增加对比型搜索场景的可见度",
        "交易型": "优化电商详情页和种草内容（小红书、什么值得买），强化购买决策阶段的品牌露出",
        "导航型": "确保品牌官网 SEO 和结构化数据完善，提交站点地图至搜索引擎",
    }
    return recommendations.get(intent, "针对该意图类型补充相关内容，提升品牌搜索覆盖率")
