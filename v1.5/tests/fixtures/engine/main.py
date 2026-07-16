from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any, Awaitable, Callable


async def diagnose(
    brand: str,
    category: str,
    website: str | None = None,
    platform: str = "doubao",
    progress_callback: Callable[[int, dict[str, Any], int, str], Awaitable[None]] | None = None,
    search_progress_callback: Callable[[int, int], Awaitable[None]] | None = None,
) -> dict[str, Any]:
    if brand == "错误品牌":
        raise RuntimeError("测试引擎故障")

    for stage in range(1, 10):
        result = {
            1: {"totalQueries": 3},
            2: {"total": 55},
            3: {"competitors": [{"name": "竞品 A"}]},
            4: {"totalQueries": 6},
            5: {"competitorCoOccurrence": [{"name": "竞品 A"}]},
            6: {"riskLevel": "中等"},
            7: {"highlights": ["亮点"], "risks": ["风险"]},
            8: {"total": 74, "grade": "中等"},
            9: {"suggestions": [{"title": "优化官网"}]},
        }[stage]
        if brand == "慢品牌" and stage == 4:
            await asyncio.sleep(0.03)
        if stage == 4 and search_progress_callback:
            for completed in range(1, 7):
                await search_progress_callback(completed, 6)
        if progress_callback:
            await progress_callback(stage, result, stage * 100, "success")

    report = {
        "meta": {"brandName": brand, "productType": category, "platform": platform},
        "aivoScore": {
            "total": 74,
            "grade": "中等",
            "dimensions": [{"name": "AI 搜索可见度", "score": 58}],
        },
    }
    return {"report": report, "htmlPath": str(Path(__file__).with_name("report.html"))}
