# Phase 1 计划：FastAPI 后端开发

## 目标
将 V1.0 的 CLI 诊断流水线包装为 Web API，支持对话式诊断体验。

## 任务清单

### 1. 修改 `main.py`（最小侵入）
- [x] 添加 `Callable, Optional` 到 typing 导入
- [x] `diagnose()` 签名增加可选 `progress_callback` 参数
- [x] 在 9 个阶段完成后分别调用 `progress_callback(stage, result, elapsed_ms, status)`
- [x] 阶段 2&3、5&6 并行完成后分别回调

### 2. 创建 `api.py`（核心）
- [x] FastAPI 应用 + CORS 中间件
- [x] 内存任务存储 `tasks: dict`（无数据库）
- [x] 阶段名称映射 `STAGE_NAMES`
- [x] `POST /api/diagnose` — 启动诊断，返回 task_id
- [x] `GET /api/diagnose/{task_id}` — 查询进度和状态
- [x] `GET /api/diagnose/{task_id}/stream` — SSE 流式推送实时进度
- [x] `GET /api/diagnose/{task_id}/report` — 获取 JSON 报告
- [x] `GET /api/diagnose/{task_id}/report/html` — 获取 HTML 报告文件
- [x] 后台诊断任务（`asyncio.create_task`）
- [x] 异常降级：阶段失败不中断 SSE 流，推送 `event: error`
- [x] 每个阶段开始前推送 `event: stage_start`
- [x] 每个阶段完成后推送 `event: stage_complete`
- [x] 诊断完成后推送 `event: complete`

### 3. 更新 `requirements.txt`
- [x] 追加 `fastapi>=0.110.0`
- [x] 追加 `uvicorn[standard]>=0.29.0`

## 验证标准
- `curl POST /api/diagnose` 返回 task_id
- 浏览器 EventSource 能收到实时事件（stage_start → stage_complete → ... → complete）
- 诊断完成，数据正确（JSON 报告 + HTML 报告）
- 阶段异常时推送降级信息，不中断 SSE 流
