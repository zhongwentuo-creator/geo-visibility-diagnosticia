"""V1.5 对 V1.0 引擎的运行适配层。

不复制或改写 V1.0 的阶段算法。通过 ``GEO_ENGINE_ROOT`` 定位固定版本引擎，
并为旧版编排器补齐 SSE 所需的阶段开始/完成回调。
"""

from __future__ import annotations

import asyncio
import importlib
import inspect
import os
import sys
import time
from collections.abc import Awaitable, Callable
from pathlib import Path
from typing import Any

StageStartCallback = Callable[[int], Awaitable[None]]
StageCompleteCallback = Callable[[int, dict[str, Any], int, str], Awaitable[None]]
SearchProgressCallback = Callable[[int, int], Awaitable[None]]

_engine_lock = asyncio.Lock()


class EngineUnavailableError(RuntimeError):
    """V1.0 引擎不可用时给出可行动的错误。"""


def _engine_root() -> Path:
    configured = os.getenv("GEO_ENGINE_ROOT")
    if not configured:
        raise EngineUnavailableError("未配置 GEO_ENGINE_ROOT，无法加载 V1.0 诊断引擎。")
    root = Path(configured).expanduser().resolve()
    if not (root / "main.py").is_file():
        raise EngineUnavailableError(f"V1.0 引擎不完整：{root} 中缺少 main.py。")
    return root


def _load_main() -> Any:
    root = _engine_root()
    root_str = str(root)
    if root_str not in sys.path:
        sys.path.insert(0, root_str)
    return importlib.import_module("main")


async def diagnose_with_progress(
    *,
    brand: str,
    category: str,
    website: str | None,
    platform: str,
    on_stage_start: StageStartCallback,
    on_stage_complete: StageCompleteCallback,
    on_search_progress: SearchProgressCallback | None = None,
) -> dict[str, Any]:
    """运行 V1.0 诊断，并兼容有、无 ``progress_callback`` 的两个引擎版本。"""
    async with _engine_lock:
        engine_main = _load_main()
        diagnose = engine_main.diagnose
        if "progress_callback" in inspect.signature(diagnose).parameters:
            started_stages: set[int] = set()

            async def bridged_progress(
                stage: int,
                result: dict[str, Any],
                elapsed_ms: int,
                status: str,
            ) -> None:
                if stage not in started_stages:
                    started_stages.add(stage)
                    await on_stage_start(stage)
                await on_stage_complete(stage, result, elapsed_ms, status)

            diagnose_kwargs: dict[str, Any] = {
                "brand": brand,
                "category": category,
                "website": website,
                "platform": platform,
                "progress_callback": bridged_progress,
            }
            if on_search_progress and "search_progress_callback" in inspect.signature(diagnose).parameters:
                diagnose_kwargs["search_progress_callback"] = on_search_progress
            return await diagnose(**diagnose_kwargs)

        originals = _instrument_legacy_engine(engine_main, on_stage_start, on_stage_complete)
        try:
            result = await diagnose(brand=brand, category=category, website=website, platform=platform)
            # 让同步阶段包装器排入的回调在返回前执行。
            await asyncio.sleep(0)
            return result
        finally:
            _restore(originals)


def _instrument_legacy_engine(
    engine_main: Any,
    on_stage_start: StageStartCallback,
    on_stage_complete: StageCompleteCallback,
) -> list[tuple[Any, str, Any]]:
    """为 V1.0 的九个阶段函数临时套上观测包装，不修改原始源码。"""
    loop = asyncio.get_running_loop()
    originals: list[tuple[Any, str, Any]] = []

    def wrap_async(module: Any, attr: str, stage: int) -> None:
        original = getattr(module, attr)

        async def wrapped(*args: Any, **kwargs: Any) -> Any:
            await on_stage_start(stage)
            started = time.perf_counter()
            result = await original(*args, **kwargs)
            elapsed = round((time.perf_counter() - started) * 1000)
            await on_stage_complete(stage, result if isinstance(result, dict) else {}, elapsed, "success")
            return result

        originals.append((module, attr, original))
        setattr(module, attr, wrapped)

    def wrap_sync(module: Any, attr: str, stage: int) -> None:
        original = getattr(module, attr)

        def schedule(callback: Awaitable[None]) -> None:
            # s5 在 worker thread 中运行；s7-s9 在 event loop 中同步运行。
            if threading_current_loop() is loop:
                loop.create_task(callback)
            else:
                asyncio.run_coroutine_threadsafe(callback, loop).result()

        def wrapped(*args: Any, **kwargs: Any) -> Any:
            schedule(on_stage_start(stage))
            started = time.perf_counter()
            result = original(*args, **kwargs)
            elapsed = round((time.perf_counter() - started) * 1000)
            schedule(on_stage_complete(stage, result if isinstance(result, dict) else {}, elapsed, "success"))
            return result

        originals.append((module, attr, original))
        setattr(module, attr, wrapped)

    wrap_async(engine_main.s1, "build", 1)
    wrap_async(engine_main.s2, "evaluate", 2)
    wrap_async(engine_main.s3, "identify", 3)
    wrap_async(engine_main.s4, "test", 4)
    wrap_sync(engine_main.s5, "summarize", 5)
    wrap_async(engine_main.s6, "scan", 6)
    wrap_sync(engine_main.s7, "generate", 7)
    wrap_sync(engine_main.s8, "calculate", 8)
    wrap_sync(engine_main.s9, "generate", 9)
    return originals


def threading_current_loop() -> asyncio.AbstractEventLoop | None:
    """返回当前线程的运行事件循环；无事件循环时返回 None。"""
    try:
        return asyncio.get_running_loop()
    except RuntimeError:
        return None


def _restore(originals: list[tuple[Any, str, Any]]) -> None:
    for module, attr, original in reversed(originals):
        setattr(module, attr, original)
