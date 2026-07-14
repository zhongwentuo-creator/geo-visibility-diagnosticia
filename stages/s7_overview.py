"""
Stage 7: 综合总览（OVERVIEW）

基于前 6 个阶段的全部诊断数据，生成执行摘要：
- 一句话定性总结（oneLiner）
- 核心亮点（3-5 条，从高分项/正向指标中提炼）
- 核心风险（3-5 条，基于风险等级与影响范围排序）
- 当前最高优先级建议（priority）

本模块为纯计算/规则推理层，无外部 API 调用。
"""

from __future__ import annotations

import json
import logging
from typing import Any

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────
# 常量与阈值
# ─────────────────────────────────────────────────────────────

_HIGHLIGHT_SCORE_THRESHOLD: int = 70          # 单项得分 ≥ 此值视为亮点
_RISK_SCORE_THRESHOLD: int = 50               # 单项得分 ≤ 此值视为风险
_HIGH_NEGATIVE_RATE: float = 30.0             # 负面率 ≥ 此值为高风险
_MED_NEGATIVE_RATE: float = 20.0              # 负面率 ≥ 此值为中风险
_RISK_SEVERITY_WEIGHT: dict[str, int] = {     # 风险等级映射权重，用于排序
    "高": 3,
    "中": 2,
    "低": 1,
}

# ─────────────────────────────────────────────────────────────
# 主入口
# ─────────────────────────────────────────────────────────────


def generate(
    user_profile: dict[str, Any],
    infra_eval: dict[str, Any],
    geo_effect: dict[str, Any],
    sentiment: dict[str, Any],
) -> dict[str, Any]:
    """
    基于前 6 阶段数据生成诊断报告的执行摘要（综合总览）。

    参数
    ----------
    user_profile : dict
        Stage 1 用户画像输出，含 segments、totalQueries 等。
    infra_eval : dict
        Stage 2 基建评估输出，含 websiteScore、socialMediaScore、
        authorityMediaScore、total、details 等。
    geo_effect : dict
        Stage 5 GEO 效果汇总输出，含 crossPlatformSummary、
        competitorCoOccurrence、missingPatterns 等。
    sentiment : dict
        Stage 6 舆情扫描输出，含 negativeRate、riskLevel、
        sentimentDistribution、topIssues 等。

    返回
    -------
    dict
        {
            "oneLiner": str,          # 一句话定性总结
            "highlights": list,       # 核心亮点列表
            "risks": list,            # 核心风险列表
            "priority": str,          # 最高优先级方向
            "stageStatus": str,       # 阶段状态
            "elapsedMs": int,         # 耗时（毫秒）
        }
    """
    import time

    t0 = time.perf_counter()

    try:
        highlights = _extract_highlights(infra_eval, geo_effect, sentiment)
        risks = _extract_risks(infra_eval, geo_effect, sentiment)
        priority = _determine_priority(infra_eval, geo_effect, sentiment, risks)
        one_liner = _generate_one_liner(infra_eval, geo_effect, sentiment, priority)

        result: dict[str, Any] = {
            "oneLiner": one_liner,
            "highlights": highlights,
            "risks": risks,
            "priority": priority,
            "stageStatus": "completed",
            "elapsedMs": round((time.perf_counter() - t0) * 1000),
        }
        return result

    except Exception as exc:
        logger.exception("Stage 7 综合总览生成失败: %s", exc)
        # 降级：返回兜底数据，确保流水线不中断
        return _fallback_overview()


# ─────────────────────────────────────────────────────────────
# 亮点提取
# ─────────────────────────────────────────────────────────────


def _extract_highlights(
    infra_eval: dict[str, Any],
    geo_effect: dict[str, Any],
    sentiment: dict[str, Any],
) -> list[dict[str, Any]]:
    """
    从各阶段数据中识别高分/正向指标，生成 3-5 条核心亮点。

    规则
    ----
    1. 基建子项 ≥ _HIGHLIGHT_SCORE_THRESHOLD 视为亮点。
    2. GEO 效果中提及率 ≥ 50% 视为亮点。
    3. 舆情正面率 ≥ 40% 视为亮点。
    4. 最多保留 5 条，按得分倒序排列。
    """
    highlights: list[dict[str, Any]] = []

    # ── 基建亮点 ──
    infra_items = [
        ("官网健康度", infra_eval.get("websiteScore", 0), "INFRA_EVAL"),
        ("自媒体矩阵", infra_eval.get("socialMediaScore", 0), "INFRA_EVAL"),
        ("权威媒体覆盖", infra_eval.get("authorityMediaScore", 0), "INFRA_EVAL"),
    ]
    for name, score, stage in infra_items:
        if score >= _HIGHLIGHT_SCORE_THRESHOLD:
            highlights.append({
                "title": f"{name}表现良好",
                "description": f"{name}得分为 {score}/100，已建立较完善的品牌信息基础。",
                "sourceStage": stage,
                "score": score,
                "type": "infra",
            })

    # ── GEO 搜索亮点 ──
    cross_summary = geo_effect.get("crossPlatformSummary", {})
    mention_rate = cross_summary.get("overallMentionRate", 0)
    if mention_rate >= 50:
        highlights.append({
            "title": "AI 搜索基础可见度尚可",
            "description": f"品牌在典型用户问题中的总体提及率为 {mention_rate:.1f}%，具备一定基础可见度。",
            "sourceStage": "GEO_EFFECT",
            "score": round(mention_rate),
            "type": "visibility",
        })

    # ── 舆情亮点 ──
    pos_rate = sentiment.get("sentimentDistribution", {}).get("positive", 0)
    if pos_rate >= 40:
        highlights.append({
            "title": "用户正面声量占比较高",
            "description": f"正面情感占比达 {pos_rate:.1f}%，品牌在用户讨论中整体形象偏正面。",
            "sourceStage": "SENTIMENT",
            "score": round(pos_rate),
            "type": "sentiment",
        })

    # 若亮点不足 3 条，补充"存在优化空间"类中性亮点
    if len(highlights) < 3:
        infra_total = infra_eval.get("total", 0)
        if infra_total > 0:
            highlights.append({
                "title": "品牌基建已具备基础框架",
                "description": f"基建综合得分 {infra_total} 分，核心渠道已覆盖，具备进一步优化的基础。",
                "sourceStage": "INFRA_EVAL",
                "score": infra_total,
                "type": "infra",
            })

    # 排序并截断至 5 条
    highlights.sort(key=lambda x: x.get("score", 0), reverse=True)
    return highlights[:5]


# ─────────────────────────────────────────────────────────────
# 风险提取
# ─────────────────────────────────────────────────────────────


def _extract_risks(
    infra_eval: dict[str, Any],
    geo_effect: dict[str, Any],
    sentiment: dict[str, Any],
) -> list[dict[str, Any]]:
    """
    基于各阶段低分/异常指标，生成 3-5 条核心风险。

    规则
    ----
    1. 基建子项 ≤ _RISK_SCORE_THRESHOLD 视为风险。
    2. 提及率 < 40% 视为可见度风险。
    3. 负面率/风险等级映射为舆情风险。
    4. 最多保留 5 条，按 severity 权重降序排列。
    """
    risks: list[dict[str, Any]] = []

    # ── 基建风险 ──
    infra_items = [
        ("官网健康度", infra_eval.get("websiteScore", 0)),
        ("自媒体矩阵", infra_eval.get("socialMediaScore", 0)),
        ("权威媒体覆盖", infra_eval.get("authorityMediaScore", 0)),
    ]
    for name, score in infra_items:
        if score <= _RISK_SCORE_THRESHOLD:
            severity = "高" if score <= 30 else "中"
            risks.append({
                "title": f"{name}薄弱",
                "description": f"{name}得分仅 {score}/100，可能直接影响 AI 平台对品牌信息的抓取与理解。",
                "sourceStage": "INFRA_EVAL",
                "severity": severity,
                "impact": "AI 搜索引用率下降，品牌信息被竞品替代",
                "type": "infra",
            })

    # ── GEO 可见度风险 ──
    cross_summary = geo_effect.get("crossPlatformSummary", {})
    mention_rate = cross_summary.get("overallMentionRate", 0)
    if mention_rate < 40:
        severity = "高" if mention_rate < 20 else "中"
        risks.append({
            "title": "AI 搜索可见度偏低",
            "description": f"品牌在典型问题中的提及率仅 {mention_rate:.1f}%，大量潜在用户查询中品牌未被呈现。",
            "sourceStage": "GEO_EFFECT",
            "severity": severity,
            "impact": "流失被动搜索流量，竞品抢占用户心智",
            "type": "visibility",
        })

    # ── 信息缺失风险 ──
    missing_patterns = geo_effect.get("missingPatterns", [])
    if len(missing_patterns) >= 3:
        risks.append({
            "title": "多类搜索场景下品牌信息缺失",
            "description": f"在 {len(missing_patterns)} 类典型查询中品牌未被提及，覆盖场景存在明显空白。",
            "sourceStage": "GEO_EFFECT",
            "severity": "中",
            "impact": "用户在对比/推荐场景中无法触达品牌",
            "type": "visibility",
        })

    # ── 舆情风险 ──
    neg_rate = sentiment.get("negativeRate", 0.0)
    risk_level = sentiment.get("riskLevel", "低风险")

    if neg_rate >= _HIGH_NEGATIVE_RATE or risk_level == "高风险":
        severity = "高"
    elif neg_rate >= _MED_NEGATIVE_RATE or risk_level == "中风险":
        severity = "中"
    else:
        severity = "低"

    if severity in ("高", "中"):
        risks.append({
            "title": f"舆情健康度{risk_level}",
            "description": f"负面率为 {neg_rate:.1f}%，AI 平台在生成回答时可能主动回避引用该品牌。",
            "sourceStage": "SENTIMENT",
            "severity": severity,
            "impact": "降低 AI 推荐权重，影响用户信任转化",
            "type": "sentiment",
        })

    # 若风险不足 3 条，补充"竞争环境"风险
    if len(risks) < 3:
        co_occ = geo_effect.get("competitorCoOccurrence", [])
        if co_occ:
            top_comp = max(co_occ, key=lambda x: x.get("count", 0))
            risks.append({
                "title": f"竞品 '{top_comp.get('name', '某竞品')}' 共现率高",
                "description": "在用户查询中，竞品与品牌频繁同时出现，可能分流用户注意力。",
                "sourceStage": "GEO_EFFECT",
                "severity": "中",
                "impact": "品牌差异化认知被稀释",
                "type": "competitive",
            })

    # 按 severity 权重排序
    risks.sort(
        key=lambda x: _RISK_SEVERITY_WEIGHT.get(x.get("severity", "低"), 0),
        reverse=True,
    )
    return risks[:5]


# ─────────────────────────────────────────────────────────────
# 优先级判定
# ─────────────────────────────────────────────────────────────


def _determine_priority(
    infra_eval: dict[str, Any],
    geo_effect: dict[str, Any],
    sentiment: dict[str, Any],
    risks: list[dict[str, Any]],
) -> str:
    """
    根据当前最紧迫的问题判定最高优先级方向。

    优先级规则（按紧迫性排序）
    --------------------------
    1. 舆情高风险 → "舆情修复"
    2. 基建严重短板（官网≤30 或整体≤40）→ "基建补齐"
    3. 提及率<20% → "搜索优化"
    4. 默认 → "综合提升"
    """
    neg_rate = sentiment.get("negativeRate", 0.0)
    risk_level = sentiment.get("riskLevel", "低风险")

    # 舆情最高优先级
    if neg_rate >= _HIGH_NEGATIVE_RATE or risk_level == "高风险":
        return "舆情修复"

    # 基建严重短板
    infra_total = infra_eval.get("total", 100)
    website_score = infra_eval.get("websiteScore", 100)
    if infra_total <= 40 or website_score <= 30:
        return "基建补齐"

    # 可见度极低
    cross_summary = geo_effect.get("crossPlatformSummary", {})
    mention_rate = cross_summary.get("overallMentionRate", 0)
    if mention_rate < 20:
        return "搜索优化"

    # 默认
    return "综合提升"


# ─────────────────────────────────────────────────────────────
# 一句话总结生成
# ─────────────────────────────────────────────────────────────


def _generate_one_liner(
    infra_eval: dict[str, Any],
    geo_effect: dict[str, Any],
    sentiment: dict[str, Any],
    priority: str,
) -> str:
    """
    生成一句定性总结，反映品牌当前 GEO 整体态势。

    模板规则
    --------
    根据基建总分、提及率、负面率组合选择不同模板。
    """
    infra_total = infra_eval.get("total", 0)
    cross_summary = geo_effect.get("crossPlatformSummary", {})
    mention_rate = cross_summary.get("overallMentionRate", 0)
    neg_rate = sentiment.get("negativeRate", 0.0)

    # 判断维度档次
    infra_ok = infra_total >= 60
    vis_ok = mention_rate >= 40
    sentiment_ok = neg_rate < 20

    # 组合模板
    if infra_ok and vis_ok and sentiment_ok:
        return "品牌 GEO 基础较为扎实，在 AI 搜索生态中具备良好可见度，建议持续优化以保持竞争优势。"

    if not infra_ok and not vis_ok and not sentiment_ok:
        return "品牌在 AI 搜索生态中存在感薄弱，基建缺失与舆情风险叠加，亟需系统性重建 GEO 基础。"

    if not vis_ok and sentiment_ok:
        return "品牌基建尚可，但在 AI 搜索场景中的可见度明显不足，需重点优化搜索触达能力。"

    if vis_ok and not sentiment_ok:
        return "品牌具备一定 AI 搜索可见度，但负面舆情可能制约 AI 推荐权重，建议同步推进舆情修复。"

    if not infra_ok and vis_ok:
        return "品牌在 AI 搜索中具备基础可见度，但底层基建薄弱将制约长期增长，建议优先补齐基础设施。"

    # 默认：结合 priority 动态拼接
    parts: list[str] = []
    if not infra_ok:
        parts.append("基建薄弱")
    if not vis_ok:
        parts.append("可见度偏低")
    if not sentiment_ok:
        parts.append("舆情风险")

    weakness = "、".join(parts) if parts else "存在优化空间"

    if priority == "舆情修复":
        return f"品牌具备基础可见度，但{weakness}制约了 GEO 效果，当前最紧迫任务是修复舆情。"
    if priority == "基建补齐":
        return f"品牌在 AI 搜索中有一定曝光，但{weakness}导致信息根基不稳，建议优先补齐基建。"
    if priority == "搜索优化":
        return f"品牌基建已搭建，但{weakness}导致用户触达率低，需重点提升搜索场景覆盖。"

    return f"品牌 GEO 建设已起步，但{weakness}，需多维度协同提升。"


# ─────────────────────────────────────────────────────────────
# 降级兜底
# ─────────────────────────────────────────────────────────────


def _fallback_overview() -> dict[str, Any]:
    """
    当 Stage 7 处理异常时返回的兜底数据，确保下游阶段仍可继续。
    """
    return {
        "oneLiner": "诊断数据暂不完整，建议完成全部阶段后重新生成总览。",
        "highlights": [],
        "risks": [
            {
                "title": "综合总览生成异常",
                "description": "Stage 7 在汇总前序阶段数据时发生错误，当前总览为默认兜底内容。",
                "sourceStage": "OVERVIEW",
                "severity": "低",
                "impact": "报告摘要可能缺失，建议人工复核前序阶段输出",
                "type": "system",
            }
        ],
        "priority": "综合提升",
        "stageStatus": "degraded",
        "elapsedMs": 0,
    }


# ─────────────────────────────────────────────────────────────
# 脚本级自检（直接运行此文件时执行）
# ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    # 构造模拟输入，验证 generate 可正常运行
    _sample_user_profile = {
        "segments": [
            {"label": "家长群体", "queries": [{"text": "儿童AI学习机推荐"}]}
        ],
        "totalQueries": 6,
    }
    _sample_infra_eval = {
        "websiteScore": 45,
        "socialMediaScore": 70,
        "authorityMediaScore": 30,
        "total": 50,
        "details": {"missingModules": ["结构化数据"]},
    }
    _sample_geo_effect = {
        "crossPlatformSummary": {"overallMentionRate": 35.0},
        "competitorCoOccurrence": [{"name": "小度", "count": 8}],
        "missingPatterns": ["对比查询", "推荐查询", "场景查询"],
    }
    _sample_sentiment = {
        "negativeRate": 28.0,
        "riskLevel": "中风险",
        "sentimentDistribution": {"positive": 25.0, "neutral": 47.0, "negative": 28.0},
        "topIssues": [{"issue": "售后响应慢", "source": "黑猫投诉"}],
        "negativeSources": [{"platform": "黑猫投诉", "issue": "售后响应慢"}],
        "positiveSources": [{"platform": "小红书", "content": "开箱体验"}],
    }

    _result = generate(
        user_profile=_sample_user_profile,
        infra_eval=_sample_infra_eval,
        geo_effect=_sample_geo_effect,
        sentiment=_sample_sentiment,
    )

    print(json.dumps(_result, ensure_ascii=False, indent=2))
