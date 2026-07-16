#!/usr/bin/env python3
"""
GEO 可见度诊断师 — 主入口（8 阶段流水线编排）

用法：
    python main.py --brand 听力熊 --category "儿童AI对话智能体" \
                   --website https://www.tinglexiong.com --platform doubao

流水线依赖关系：
    Stage1 → (Stage2 ∥ Stage3) → Stage4 → (Stage5 ∥ Stage6) → Stage7 → Stage8 → Stage9
"""

from __future__ import annotations

import argparse
import asyncio
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Optional

# 先加载配置（确保 .env 被读取到 os.environ）
from config import Settings

from stages import (
    s1_user_profile as s1,
    s2_infra_eval as s2,
    s3_competitor as s3,
    s4_ai_search as s4,
    s5_geo_effect as s5,
    s6_sentiment as s6,
    s7_overview as s7,
    s8_aivo_score as s8,
    s9_suggestion as s9,
)
from utils.json_repair import repair_json

settings = Settings()


# ═══════════════════════════════════════════════════════════════
# 辅助函数
# ═══════════════════════════════════════════════════════════════


def _extract_queries(user_profile: dict[str, Any]) -> list[dict[str, Any]]:
    """从 Stage 1 用户画像中扁平提取所有 Query。

    Args:
        user_profile: s1.build 返回的字典，包含 ``segments`` 列表。

    Returns:
        所有 Segment 的 queries 合并后的列表。
    """
    queries: list[dict[str, Any]] = []
    for seg in user_profile.get("segments", []):
        for q in seg.get("queries", []):
            queries.append(q)
    return queries


def _stage_meta(
    elapsed_ms: int = 0,
    status: str = "success",
    record_count: int = 0,
) -> dict[str, Any]:
    """生成统一的阶段元数据字典。

    Args:
        elapsed_ms: 阶段耗时（毫秒）。
        status: 阶段状态，如 ``"success"`` / ``"degraded"`` / ``"error"``。
        record_count: 阶段处理的数据条数。

    Returns:
        包含 ``elapsedMs``、``stageStatus``、``recordCount`` 的字典。
    """
    return {
        "elapsedMs": elapsed_ms,
        "stageStatus": status,
        "recordCount": record_count,
    }


async def diagnose(
    brand: str,
    category: str,
    website: str | None = None,
    platform: str = "doubao",
    progress_callback: Optional[Callable[[int, dict, int, str], Any]] = None,
    search_progress_callback: Optional[Callable[[int, int], Any]] = None,
) -> dict[str, Any]:
    """GEO 可见度诊断主函数：8 阶段流水线编排。

    阶段执行顺序：
        1. 用户画像构建（串行）
        2. 基建评估 + 竞品分析（并行）
        3. AI 搜索测试（串行，依赖 1+2）
        4. GEO 效果汇总 + 舆情扫描（并行，依赖 4）
        5. 综合总览（串行，依赖 2+4+5+6）
        6. AIVO 评分（串行，依赖 2+3+4+6）
        7. 建议系统（串行，依赖 8）

    Args:
        brand: 品牌名称。
        category: 产品类型。
        website: 官网地址（可选）。
        platform: 诊断平台，可选 ``"doubao"`` / ``"chatgpt"`` / ``"perplexity"``。
        progress_callback: 阶段完成回调函数，签名为 ``callback(stage, result, elapsed_ms, status)``。
        search_progress_callback: Stage 4 单条 Query 完成回调，签名为 ``callback(completed, total)``。

    Returns:
        包含 ``report``（完整报告字典）、``jsonPath``、``htmlPath`` 的字典。
    """
    diagnosis_id = f"GEO-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    output_dir = Path("output") / diagnosis_id
    output_dir.mkdir(parents=True, exist_ok=True)

    # ── Stage 1：用户画像构建 ──────────────────────────────
    t0 = time.perf_counter()
    user_profile = await s1.build(brand, category)
    stage1_meta = _stage_meta(
        elapsed_ms=round((time.perf_counter() - t0) * 1000),
        status="success",
        record_count=user_profile.get("totalQueries", 0),
    )
    if progress_callback:
        await progress_callback(1, user_profile, stage1_meta["elapsedMs"], stage1_meta["stageStatus"])
    queries = _extract_queries(user_profile)

    # ── Stage 2 & 3：基建评估 + 竞品分析（并行）───────────
    t0 = time.perf_counter()
    infra_eval_raw, competitors_raw = await asyncio.gather(
        s2.evaluate(brand, website),
        s3.identify(brand, category, queries),
        return_exceptions=True,
    )

    # 处理 Stage 2 结果
    if isinstance(infra_eval_raw, Exception):
        infra_eval = {
            "websiteScore": 0,
            "socialMediaScore": 0,
            "authorityMediaScore": 0,
            "total": 0,
            "details": {},
            "error": str(infra_eval_raw),
        }
        stage2_meta = _stage_meta(
            elapsed_ms=0, status="degraded", record_count=0
        )
    else:
        infra_eval = infra_eval_raw
        stage2_meta = _stage_meta(
            elapsed_ms=round((time.perf_counter() - t0) * 1000),
            status="success",
            record_count=3,  # 官网 / 自媒体 / 权威媒体 三项
        )

    # 处理 Stage 3 结果
    if isinstance(competitors_raw, Exception):
        competitors_data = {
            "competitors": [],
            "benchmarkAverage": 0.0,
            "competitorSource": "default",
            "error": str(competitors_raw),
        }
        stage3_meta = _stage_meta(
            elapsed_ms=0, status="degraded", record_count=0
        )
    else:
        competitors_data = competitors_raw
        stage3_meta = _stage_meta(
            elapsed_ms=competitors_data.get("elapsedMs", round((time.perf_counter() - t0) * 1000)),
            status=competitors_data.get("stageStatus", "success"),
            record_count=competitors_data.get("recordCount", 0),
        )

    if progress_callback:
        await progress_callback(2, infra_eval, stage2_meta["elapsedMs"], stage2_meta["stageStatus"])
        await progress_callback(3, competitors_data, stage3_meta["elapsedMs"], stage3_meta["stageStatus"])

    competitors_list: list[dict[str, Any]] = competitors_data.get("competitors", [])

    # ── Stage 4：AI 搜索测试 ──────────────────────────────
    t0 = time.perf_counter()
    ai_search = await s4.test(
        brand,
        queries,
        competitors_list,
        platform,
        progress_callback=search_progress_callback,
    )
    stage4_meta = _stage_meta(
        elapsed_ms=round((time.perf_counter() - t0) * 1000),
        status="success",
        record_count=ai_search.get("totalQueries", 0),
    )

    # ── Stage 5 & 6：GEO 效果汇总 + 舆情扫描（并行）───────
    if progress_callback:
        await progress_callback(4, ai_search, stage4_meta["elapsedMs"], stage4_meta["stageStatus"])

    t0 = time.perf_counter()
    geo_effect_raw, sentiment_raw = await asyncio.gather(
        asyncio.to_thread(s5.summarize, ai_search, competitors_list),
        s6.scan(brand),
        return_exceptions=True,
    )

    # 处理 Stage 5 结果
    if isinstance(geo_effect_raw, Exception):
        geo_effect = {
            "crossPlatformSummary": {},
            "competitorCoOccurrence": [],
            "missingPatterns": [],
            "error": str(geo_effect_raw),
        }
        stage5_meta = _stage_meta(
            elapsed_ms=0, status="degraded", record_count=0
        )
    else:
        geo_effect = geo_effect_raw
        stage5_meta = _stage_meta(
            elapsed_ms=round((time.perf_counter() - t0) * 1000),
            status="success",
            record_count=len(geo_effect.get("competitorCoOccurrence", [])),
        )

    # 处理 Stage 6 结果
    if isinstance(sentiment_raw, Exception):
        sentiment = {
            "negativeRate": -1.0,
            "riskLevel": "数据缺失",
            "sentimentDistribution": {},
            "topIssues": [],
            "negativeSources": [],
            "positiveSources": [],
            "error": str(sentiment_raw),
        }
        stage6_meta = _stage_meta(
            elapsed_ms=0, status="degraded", record_count=0
        )
    else:
        sentiment = sentiment_raw
        stage6_meta = _stage_meta(
            elapsed_ms=sentiment.get("elapsedMs", round((time.perf_counter() - t0) * 1000)),
            status=sentiment.get("stageStatus", "completed"),
            record_count=sentiment.get("recordCount", 0),
        )

    if progress_callback:
        await progress_callback(5, geo_effect, stage5_meta["elapsedMs"], stage5_meta["stageStatus"])
        await progress_callback(6, sentiment, stage6_meta["elapsedMs"], stage6_meta["stageStatus"])

    # ── Stage 7：综合总览 ────────────────────────────────
    t0 = time.perf_counter()
    overview = s7.generate(user_profile, infra_eval, geo_effect, sentiment)
    stage7_meta = _stage_meta(
        elapsed_ms=overview.get("elapsedMs", round((time.perf_counter() - t0) * 1000)),
        status=overview.get("stageStatus", "success"),
        record_count=len(overview.get("highlights", [])) + len(overview.get("risks", [])),
    )

    if progress_callback:
        await progress_callback(7, overview, stage7_meta["elapsedMs"], stage7_meta["stageStatus"])

    # ── Stage 8：AIVO 评分 ────────────────────────────────
    t0 = time.perf_counter()
    aivo_score = s8.calculate(infra_eval, ai_search, competitors_data, sentiment)
    stage8_meta = _stage_meta(
        elapsed_ms=round((time.perf_counter() - t0) * 1000),
        status="success",
        record_count=4,  # 4 个维度
    )

    if progress_callback:
        await progress_callback(8, aivo_score, stage8_meta["elapsedMs"], stage8_meta["stageStatus"])

    # ── Stage 9：建议系统 ──────────────────────────────────
    t0 = time.perf_counter()
    suggestions = s9.generate(aivo_score, infra_eval, sentiment)
    stage9_meta = _stage_meta(
        elapsed_ms=round((time.perf_counter() - t0) * 1000),
        status="success" if "error" not in suggestions else "degraded",
        record_count=len(suggestions.get("suggestions", [])),
    )

    if progress_callback:
        await progress_callback(9, suggestions, stage9_meta["elapsedMs"], stage9_meta["stageStatus"])

    # ── 合并最终报告 ───────────────────────────────────────
    report: dict[str, Any] = {
        "meta": {
            "diagnosisId": diagnosis_id,
            "brandName": brand,
            "productType": category,
            "officialWebsite": website,
            "platform": platform,
            "diagnosisDate": datetime.now().isoformat(),
            "version": "1.0.0",
            "debug": settings.debug,
        },
        "userProfile": {**user_profile, "_stageMeta": stage1_meta},
        "infrastructure": {**infra_eval, "_stageMeta": stage2_meta},
        "competitorAnalysis": {**competitors_data, "_stageMeta": stage3_meta},
        "competitors": competitors_list,
        "aiSearch": {**ai_search, "_stageMeta": stage4_meta},
        "geoEffect": {**geo_effect, "_stageMeta": stage5_meta},
        "sentiment": {**sentiment, "_stageMeta": stage6_meta},
        "overview": {**overview, "_stageMeta": stage7_meta},
        "aivoScore": {**aivo_score, "_stageMeta": stage8_meta},
        "suggestions": {**suggestions, "_stageMeta": stage9_meta},
    }

    # ── JSON 修复 ──────────────────────────────────────────
    report = repair_json(report)

    # ── 输出 JSON ──────────────────────────────────────────
    safe_brand = brand.replace(" ", "_").replace("/", "-")
    json_path = output_dir / f"{safe_brand}_{platform}_diag-report.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    # ── 生成 HTML 报告 ─────────────────────────────────────
    html_path = output_dir / f"{safe_brand}_{platform}_GEO诊断报告.html"
    await _generate_html_report(report, html_path)

    return {
        "report": report,
        "jsonPath": str(json_path),
        "htmlPath": str(html_path),
    }


async def _generate_html_report(report: dict[str, Any], output_path: Path) -> None:
    """基于 Jinja2 模板生成自包含 HTML 报告。

    Args:
        report: 完整的诊断报告字典。
        output_path: HTML 文件输出路径。
    """
    # DEBUG
    print(f"[DEBUG] report type: {type(report)}, keys: {list(report.keys()) if isinstance(report, dict) else 'N/A'}")

    from jinja2 import Environment, FileSystemLoader

    template_dir = Path(__file__).parent / "report"
    env = Environment(
        loader=FileSystemLoader(str(template_dir)),
        autoescape=True,
    )
    template = env.get_template("template.html")

    html_content = template.render(report=report)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html_content)


# ═══════════════════════════════════════════════════════════════
# CLI 入口
# ═══════════════════════════════════════════════════════════════


def main() -> None:
    parser = argparse.ArgumentParser(description="GEO 可见度诊断师")
    parser.add_argument("--brand", required=True, help="品牌名称")
    parser.add_argument("--category", required=True, help="产品类型")
    parser.add_argument("--website", default=None, help="官网地址（可选）")
    parser.add_argument(
        "--platform",
        default=settings.default_platform,
        choices=["doubao", "chatgpt", "perplexity"],
        help="诊断平台（默认：doubao）",
    )
    args = parser.parse_args()

    result = asyncio.run(
        diagnose(args.brand, args.category, args.website, args.platform)
    )

    total_score = result["report"]["aivoScore"]["total"]
    grade = result["report"]["aivoScore"]["grade"]

    print(f"\n✅ 诊断完成！")
    print(f"   JSON 数据: {result['jsonPath']}")
    print(f"   HTML 报告: {result['htmlPath']}")
    print(f"   AIVO 总分: {total_score} / 100（{grade}）")


if __name__ == "__main__":
    main()
