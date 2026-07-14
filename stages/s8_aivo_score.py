"""
阶段 8：AIVO 评分计算

基于前序阶段数据，按 4 维度 × 25% 权重计算 AIVO（AI Visibility & Optimization）综合评分。
"""

from typing import Any


def calculate(
    infra_eval: dict[str, Any],
    ai_search_results: dict[str, Any],
    competitors: dict[str, Any],
    sentiment: dict[str, Any],
) -> dict[str, Any]:
    """
    计算 AIVO 4 维度评分。

    输入：
    - infra_eval: {"websiteScore": int, "socialMediaScore": int, "authorityMediaScore": int, "total": int}
    - ai_search_results: {"mentionRate": float, "firstParagraphRate": float, "totalQueries": int, "results": [...]}
    - competitors: {"competitors": [{"name": str, "aivoScore": int}], "benchmarkAverage": float}
    - sentiment: {"negativeRate": float, "riskLevel": str, "sentimentDistribution": {"positive": float, "neutral": float, "negative": float}}

    输出：
    {
        "total": int,  # 0-100
        "grade": str,  # "优秀"/"良好"/"中等"/"较差"/"差"
        "dimensions": [
            {"code": "AI_SEARCH_VISIBILITY", "name": "AI搜索可见度", "score": int, "weight": 0.25, "weightedScore": float},
            {"code": "INFRA_COMPLETENESS", "name": "基建完善度", "score": int, "weight": 0.25, "weightedScore": float},
            {"code": "COMPETITIVE_ADVANTAGE", "name": "竞品对比优势", "score": int, "weight": 0.25, "weightedScore": float},
            {"code": "SENTIMENT_HEALTH", "name": "舆情健康度", "score": int, "weight": 0.25, "weightedScore": float}
        ],
        "nextTierGap": int,
        "nextTierTarget": str
    }

    异常输入时返回安全默认值（total=0, grade="差", 各维度 score=0）。
    """

    # ---------- 1. 安全默认值 ----------
    safe_default = {
        "total": 0,
        "grade": "差",
        "dimensions": [
            {"code": "AI_SEARCH_VISIBILITY", "name": "AI搜索可见度", "score": 0, "weight": 0.25, "weightedScore": 0.0},
            {"code": "INFRA_COMPLETENESS", "name": "基建完善度", "score": 0, "weight": 0.25, "weightedScore": 0.0},
            {"code": "COMPETITIVE_ADVANTAGE", "name": "竞品对比优势", "score": 0, "weight": 0.25, "weightedScore": 0.0},
            {"code": "SENTIMENT_HEALTH", "name": "舆情健康度", "score": 0, "weight": 0.25, "weightedScore": 0.0},
        ],
        "nextTierGap": 60,
        "nextTierTarget": "较差",
    }

    # ---------- 2. 输入校验 ----------
    if not isinstance(infra_eval, dict) or not isinstance(ai_search_results, dict) \
            or not isinstance(competitors, dict) or not isinstance(sentiment, dict):
        return safe_default

    # ---------- 3. 维度一：AI 搜索可见度 ----------
    mention_rate = float(ai_search_results.get("mentionRate", 0))
    first_paragraph_rate = float(ai_search_results.get("firstParagraphRate", 0))
    total_queries = int(ai_search_results.get("totalQueries", 0))
    results = ai_search_results.get("results", [])
    mentioned_count = sum(1 for r in results if r.get("mentioned", False)) if isinstance(results, list) else 0

    if total_queries > 0:
        visibility = round(
            mention_rate * 0.4
            + first_paragraph_rate * 0.3
            + (100 * mentioned_count / total_queries) * 0.3,
            1,
        )
    else:
        # 无有效查询时退化为 mentionRate
        visibility = round(mention_rate, 1)

    visibility = max(0, min(100, visibility))

    # ---------- 4. 维度二：基建完善度 ----------
    infra = int(infra_eval.get("total", 0))
    infra = max(0, min(100, infra))

    # ---------- 5. 维度三：竞品对比优势 ----------
    benchmark_avg = float(competitors.get("benchmarkAverage", 0))
    # 品牌得分以 AI 搜索可见度作为代理（与 PRD 示例一致）
    brand_score = visibility
    if benchmark_avg > 0:
        competitive = round(brand_score / benchmark_avg * 100, 1)
    else:
        competitive = 0.0
    competitive = min(100, competitive)

    # ---------- 6. 维度四：舆情健康度 ----------
    negative_rate = float(sentiment.get("negativeRate", 0))
    risk_level = str(sentiment.get("riskLevel", "")).strip()

    risk_penalty_map = {
        "低风险": 0,
        "中低风险": 5,
        "中风险": 10,
        "高风险": 20,
        "极高风险": 35,
    }
    risk_penalty = risk_penalty_map.get(risk_level, 0)

    sentiment_health = max(0, round(100 - negative_rate * 2.5 - risk_penalty, 1))
    sentiment_health = min(100, sentiment_health)

    # ---------- 7. 加权总分 ----------
    total = round((visibility + infra + competitive + sentiment_health) / 4)
    total = max(0, min(100, total))

    # ---------- 8. 等级判定 ----------
    if total >= 90:
        grade = "优秀"
    elif total >= 80:
        grade = "良好"
    elif total >= 70:
        grade = "中等"
    elif total >= 60:
        grade = "较差"
    else:
        grade = "差"

    # ---------- 9. 下一等级差距 ----------
    tier_thresholds = [
        (90, "优秀"),
        (80, "良好"),
        (70, "中等"),
        (60, "较差"),
    ]
    next_tier_gap = 0
    next_tier_target = "已达成最高等级"
    for threshold, tier_name in tier_thresholds:
        if total < threshold:
            next_tier_gap = threshold - total
            next_tier_target = tier_name
            break

    # ---------- 10. 组装输出 ----------
    dimensions = [
        {
            "code": "AI_SEARCH_VISIBILITY",
            "name": "AI搜索可见度",
            "score": int(round(visibility)),
            "weight": 0.25,
            "weightedScore": round(visibility * 0.25, 2),
        },
        {
            "code": "INFRA_COMPLETENESS",
            "name": "基建完善度",
            "score": int(round(infra)),
            "weight": 0.25,
            "weightedScore": round(infra * 0.25, 2),
        },
        {
            "code": "COMPETITIVE_ADVANTAGE",
            "name": "竞品对比优势",
            "score": int(round(competitive)),
            "weight": 0.25,
            "weightedScore": round(competitive * 0.25, 2),
        },
        {
            "code": "SENTIMENT_HEALTH",
            "name": "舆情健康度",
            "score": int(round(sentiment_health)),
            "weight": 0.25,
            "weightedScore": round(sentiment_health * 0.25, 2),
        },
    ]

    return {
        "total": total,
        "grade": grade,
        "dimensions": dimensions,
        "nextTierGap": next_tier_gap,
        "nextTierTarget": next_tier_target,
    }
