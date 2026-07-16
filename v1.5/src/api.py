#!/usr/bin/env python3
"""
GEO 可见度诊断师 V1.5 — FastAPI 后端

提供 REST API + SSE 流式推送，包装 V1.0 的诊断流水线。
"""

from __future__ import annotations

import asyncio
import json
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from engine_adapter import EngineUnavailableError, diagnose_with_progress

# ═══════════════════════════════════════════════════════════════
# FastAPI 应用初始化
# ═══════════════════════════════════════════════════════════════

app = FastAPI(
    title="GEO 可见度诊断师",
    description="AI 驱动的品牌 GEO 可见度诊断服务 — V1.5 对话式体验",
    version="1.5.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS：生产环境显式指定来源；同源部署无需额外放开。
_default_origins = "http://127.0.0.1:8000,http://localhost:8000,http://127.0.0.1:8765,http://localhost:8765"
allowed_origins = [origin.strip() for origin in os.getenv("CORS_ALLOW_ORIGINS", _default_origins).split(",") if origin.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

_static_dir = Path(__file__).parent / "static"
app.mount("/assets", StaticFiles(directory=_static_dir / "assets"), name="assets")
app.mount("/css", StaticFiles(directory=_static_dir / "css"), name="css")
app.mount("/js", StaticFiles(directory=_static_dir / "js"), name="js")

# ═══════════════════════════════════════════════════════════════
# 内存任务存储（V1.5 不持久化，每次重启清空）
# ═══════════════════════════════════════════════════════════════

_tasks: dict[str, dict[str, Any]] = {}

# 阶段名称映射
_STAGE_NAMES: dict[int, str] = {
    1: "用户画像构建",
    2: "基建评估",
    3: "竞品分析",
    4: "AI 搜索测试",
    5: "GEO 效果汇总",
    6: "舆情扫描",
    7: "综合总览",
    8: "AIVO 评分",
    9: "建议系统",
}


# ═══════════════════════════════════════════════════════════════
# Pydantic 模型
# ═══════════════════════════════════════════════════════════════


class DiagnoseRequest(BaseModel):
    """启动诊断请求体。"""

    brand: str = Field(..., min_length=1, description="品牌名称")
    category: str = Field(..., min_length=1, description="产品类型")
    website: Optional[str] = Field(None, description="官网地址（可选）")
    platform: str = Field("doubao", description="诊断平台：doubao / chatgpt / perplexity")


class DiagnoseResponse(BaseModel):
    """启动诊断响应体。"""

    task_id: str
    status: str
    estimated_time: int


class TaskStatusResponse(BaseModel):
    """任务状态查询响应体。"""

    task_id: str
    status: str
    progress: float
    stages: list[dict[str, Any]]
    aivo_score: Optional[int] = None
    error: Optional[str] = None


# ═══════════════════════════════════════════════════════════════
# 阶段摘要生成
# ═══════════════════════════════════════════════════════════════


def _build_stage_summary(stage: int, result: dict[str, Any]) -> str:
    """根据阶段结果生成简短摘要。"""
    try:
        if stage == 1:
            total = result.get("totalQueries", 0)
            return f"识别了 {total} 类核心用户及其搜索意图"
        if stage == 2:
            total = result.get("total", 0)
            return f"基建完善度 {total}/100"
        if stage == 3:
            comps = result.get("competitors", [])
            names = ", ".join(c.get("name", "") for c in comps[:3])
            return f"识别竞品：{names}" if names else "竞品识别完成"
        if stage == 4:
            total = result.get("totalQueries", 0)
            return f"完成 {total} 个搜索查询测试"
        if stage == 5:
            count = len(result.get("competitorCoOccurrence", []))
            return f"竞品共现 {count} 次，跨平台表现已汇总"
        if stage == 6:
            risk = result.get("riskLevel", "未知")
            return f"舆情风险等级：{risk}"
        if stage == 7:
            h = len(result.get("highlights", []))
            r = len(result.get("risks", []))
            return f"亮点 {h} 个，风险 {r} 个"
        if stage == 8:
            total = result.get("total", 0)
            grade = result.get("grade", "")
            return f"AIVO 总分 {total}/100（{grade}）"
        if stage == 9:
            count = len(result.get("suggestions", []))
            return f"生成 {count} 条优化建议"
    except Exception:
        pass
    return "阶段完成"


# ═══════════════════════════════════════════════════════════════
# 后台诊断任务
# ═══════════════════════════════════════════════════════════════


async def _run_diagnosis(
    task_id: str,
    brand: str,
    category: str,
    website: Optional[str],
    platform: str,
) -> None:
    """后台运行诊断流水线，通过 Queue 推送 SSE 事件。

    事件序列：
        start → stage_start(1) → stage_complete(1) → ... → stage_complete(9) → complete
        （任一阶段失败时穿插 error 事件，但不中断 SSE 流）
    """
    task = _tasks[task_id]
    queue: asyncio.Queue = task["queue"]
    started_stages: set[int] = set()

    # ── 辅助：发送 SSE 事件到队列 ──
    async def _emit(event: str, data: dict[str, Any]) -> None:
        await queue.put({"event": event, "data": data})

    # ── 辅助：progress_callback，由 main.diagnose() 调用 ──
    async def _on_stage(
        stage: int,
        result: dict[str, Any],
        elapsed_ms: int,
        status: str,
    ) -> None:
        summary = _build_stage_summary(stage, result)
        stage_data = {
            "stage": stage,
            "name": _STAGE_NAMES.get(stage, f"阶段 {stage}"),
            "status": status,
            "elapsed_ms": elapsed_ms,
            "summary": summary,
        }
        task["stages"].append(stage_data)
        task["progress"] = round(stage / 9.0, 2)
        await _emit("stage_complete", stage_data)

        completed = {item["stage"] for item in task["stages"]}
        # V1.0 仅在阶段完成时回调；V1.5 据其固定依赖图及时发出后续阶段开始事件。
        dependencies = {
            2: {1}, 3: {1}, 4: {2, 3}, 5: {4}, 6: {4},
            7: {5, 6}, 8: {7}, 9: {8},
        }
        for next_stage, required in dependencies.items():
            if next_stage not in started_stages and required.issubset(completed):
                started_stages.add(next_stage)
                await _emit("stage_start", {
                    "stage": next_stage,
                    "name": _STAGE_NAMES[next_stage],
                    "status": "running",
                })

    # ── 发送诊断开始事件 ──
    await _emit("start", {
        "task_id": task_id,
        "total_stages": 9,
        "brand": brand,
        "category": category,
    })
    started_stages.add(1)
    await _emit("stage_start", {
        "stage": 1,
        "name": _STAGE_NAMES[1],
        "status": "running",
    })

    # ── 启动 diagnose() 作为后台协程 ──
    try:
        async def _on_engine_stage_start(stage: int) -> None:
            # 旧版引擎适配层的开始回调只用于观测；实际 SSE 开始事件由依赖图统一发送。
            return None

        # 通过适配层调用固定版本的 V1.0 引擎；适配层负责向 SSE 暴露阶段事件。
        result = await diagnose_with_progress(
            brand=brand,
            category=category,
            website=website,
            platform=platform,
            on_stage_start=_on_engine_stage_start,
            on_stage_complete=_on_stage,
        )

        # ── 发送完成事件 ──
        report = result.get("report", {})
        aivo = report.get("aivoScore", {})
        task["status"] = "success"
        task["result"] = result
        task["aivo_score"] = aivo.get("total")
        task["progress"] = 1.0

        await _emit("complete", {
            "task_id": task_id,
            "status": "success",
            "aivo_score": aivo.get("total"),
            "grade": aivo.get("grade"),
            "report_url": f"/api/diagnose/{task_id}/report",
            "html_url": f"/api/diagnose/{task_id}/report/html",
        })

    except Exception as exc:
        # ── 异常处理：推送降级信息，不中断 SSE 流 ──
        task["status"] = "error"
        task["error"] = str(exc)
        task["progress"] = round(len(task["stages"]) / 9.0, 2)

        await _emit("error", {
            "task_id": task_id,
            "error": str(exc),
            "message": "诊断过程中发生错误，请稍后重试。部分结果可能已生成。",
            "completed_stages": len(task["stages"]),
        })

    finally:
        # ── 发送结束标记（SSE 关闭信号）──
        await queue.put(None)


# ═══════════════════════════════════════════════════════════════
# API 端点
# ═══════════════════════════════════════════════════════════════


@app.post("/api/diagnose", response_model=DiagnoseResponse)
async def start_diagnosis(request: DiagnoseRequest) -> dict[str, Any]:
    """启动 GEO 诊断任务。

    返回 task_id，前端用这个 id 连接 SSE stream 接收实时进度。
    """
    task_id = f"GEO-{datetime.now().strftime('%Y%m%d-%H%M%S')}-{uuid.uuid4().hex[:6]}"

    _tasks[task_id] = {
        "task_id": task_id,
        "status": "running",
        "brand": request.brand,
        "category": request.category,
        "website": request.website,
        "platform": request.platform,
        "stages": [],
        "progress": 0.0,
        "result": None,
        "error": None,
        "aivo_score": None,
        "queue": asyncio.Queue(),
        "created_at": datetime.now().isoformat(),
    }

    # 后台启动诊断（不阻塞 HTTP 响应）
    asyncio.create_task(_run_diagnosis(
        task_id,
        request.brand,
        request.category,
        request.website,
        request.platform,
    ))

    return {
        "task_id": task_id,
        "status": "running",
        "estimated_time": 120,
    }


@app.get("/api/diagnose/{task_id}", response_model=TaskStatusResponse)
async def get_diagnosis(task_id: str) -> dict[str, Any]:
    """查询诊断任务状态。"""
    task = _tasks.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail=f"任务 {task_id} 不存在或已过期")

    return {
        "task_id": task_id,
        "status": task["status"],
        "progress": task["progress"],
        "stages": task["stages"],
        "aivo_score": task.get("aivo_score"),
        "error": task.get("error"),
    }


@app.get("/api/diagnose/{task_id}/stream")
async def stream_diagnosis(task_id: str) -> StreamingResponse:
    """SSE 流式推送诊断实时进度。

    事件类型：
        - start: 诊断开始
        - stage_start: 某阶段开始
        - stage_complete: 某阶段完成（含结果摘要）
        - complete: 全部完成（含 AIVO 分数）
        - error: 发生错误（含降级信息）
    """
    task = _tasks.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail=f"任务 {task_id} 不存在或已过期")

    queue: asyncio.Queue = task["queue"]

    async def _event_generator():
        while True:
            event = await queue.get()
            if event is None:
                # 结束标记
                break
            # SSE 格式：event: <name>\ndata: <json>\n\n
            yield (
                f"event: {event['event']}\n"
                f"data: {json.dumps(event['data'], ensure_ascii=False)}\n\n"
            )

    return StreamingResponse(
        _event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@app.get("/api/diagnose/{task_id}/report")
async def get_report(task_id: str) -> dict[str, Any]:
    """获取诊断报告的 JSON 数据。"""
    task = _tasks.get(task_id)
    if not task or task.get("status") != "success":
        raise HTTPException(
            status_code=404,
            detail="报告不存在或诊断尚未完成",
        )

    result = task.get("result", {})
    return result.get("report", {})


@app.get("/api/diagnose/{task_id}/report/html")
async def get_html_report(task_id: str) -> FileResponse:
    """下载 HTML 诊断报告文件。"""
    task = _tasks.get(task_id)
    if not task or task.get("status") != "success":
        raise HTTPException(
            status_code=404,
            detail="报告不存在或诊断尚未完成",
        )

    result = task.get("result", {})
    html_path = result.get("htmlPath")
    if not html_path or not Path(html_path).exists():
        raise HTTPException(status_code=404, detail="HTML 报告文件不存在")

    return FileResponse(
        html_path,
        media_type="text/html",
        filename=Path(html_path).name,
    )


# ═══════════════════════════════════════════════════════════════
# 健康检查
# ═══════════════════════════════════════════════════════════════


@app.get("/health")
async def health_check() -> dict[str, str]:
    """服务健康检查。"""
    return {"status": "ok", "version": "1.5.0"}


@app.get("/", include_in_schema=False)
async def serve_workspace() -> FileResponse:
    """同源提供对话工作台，避免部署后前端仍指向本机地址。"""
    return FileResponse(_static_dir / "index.html")


# ═══════════════════════════════════════════════════════════════
# 启动入口（直接 python api.py 时）
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "api:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
