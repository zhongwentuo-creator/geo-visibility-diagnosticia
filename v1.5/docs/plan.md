# V1.5 交付计划与验收状态

> 更新：2026-07-17。此文件是 V1.5 的唯一任务状态来源；旧 `handoff_v1.5.md` 仅作历史交接，不再表示当前完成度。

## 发布目标

朋友可通过公网 URL 打开对话工作台，发起真实品牌 GEO 诊断，实时接收 9 阶段 SSE 事件，并下载 JSON/HTML 报告。

## 已完成

- [x] 前端对话工作台：自然语言意图识别、手动补充、阶段过程、报告操作、响应式布局。
- [x] 同源服务：FastAPI 提供工作台、静态资源、REST API 与 SSE，生产前端不会指向本机地址。
- [x] V1.0 引擎边界：生产镜像从仓库根目录复制 V1.0 引擎；该源码已支持 `progress_callback`。
- [x] 端到端本地烟测：真实引擎返回 `start → stage_start ×9 → stage_complete ×9 → complete`，JSON 与 HTML 报告端点可用。
- [x] 异常回归：测试夹具验证 `error` SSE 事件与状态查询。
- [x] 自动化质量门禁：pytest、Python 编译、JS 语法、Docker 构建已写入 GitHub Actions 工作流。
- [x] 部署工件：`Dockerfile`、`render.yaml`、`.env.example`、部署说明已补齐。
- [x] GitHub 源码发布：V1.0 根目录引擎、`v1.5/` 与 `.github/workflows/geo-v15-ci.yml` 已通过 PR #1 合并到 `main`（merge commit `21918de`，4 项检查通过）。
- [x] Render Docker Web Service：通过 `v1.5/render.yaml` 创建 `geo-visibility-diagnosis-v15`（Free / Singapore）；公网 `/health` 已返回 `{"status":"ok","version":"1.5.0"}`。详见 `PROJECT_NODE_RECORDS.md`。
- [x] Render 生产配置：已选择 Kimi + 豆包并配置 `KIMI_API_KEY`、`DOUBAO_API_KEY`、`CORS_ALLOW_ORIGINS`、`KIMI_API_URL`、`KIMI_MODEL`；PR #3（merge commit `2a21e8d`）确保 Kimi-only 配置路由至 Moonshot。密钥值不进入仓库。详见 `PROJECT_NODE_RECORDS.md`。

## 进行中

- [ ] 节点 4：用真实品牌完成公网 SSE、JSON、HTML 验收。首次任务已确认后台 9 阶段成功，JSON/HTML 通过，但 SSE 在 Stage 4 长耗时期间提前结束；修复已进入 PR #5，等待合并部署后复测。当前行动见 `NODE4_EXECUTION.md`。

## 待完成的发布门禁

- [ ] 用外网桌面端、手机各走一遍；24 小时后复测一次。

## 验收结论

当前状态为 **节点 4 进行中**。真实品牌诊断已证明后台和 JSON/HTML 报告链路可用，但完整 SSE 尚未通过；修复部署后的公网复测、跨设备走查与 24 小时稳定性仍未完成。
