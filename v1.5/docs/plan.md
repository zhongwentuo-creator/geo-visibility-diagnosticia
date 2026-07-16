# V1.5 交付计划与验收状态

> 更新：2026-07-16。此文件是 V1.5 的唯一任务状态来源；旧 `handoff_v1.5.md` 仅作历史交接，不再表示当前完成度。

## 发布目标

朋友可通过公网 URL 打开对话工作台，发起真实品牌 GEO 诊断，实时接收 9 阶段 SSE 事件，并下载 JSON/HTML 报告。

## 已完成

- [x] 前端对话工作台：自然语言意图识别、手动补充、阶段过程、报告操作、响应式布局。
- [x] 同源服务：FastAPI 提供工作台、静态资源、REST API 与 SSE，生产前端不会指向本机地址。
- [x] V1.0 引擎边界：使用 `../GEO可见度诊断师_v1.0引擎/v1.0/src`；该源码已支持 `progress_callback`。
- [x] 端到端本地烟测：真实引擎返回 `start → stage_start ×9 → stage_complete ×9 → complete`，JSON 与 HTML 报告端点可用。
- [x] 异常回归：测试夹具验证 `error` SSE 事件与状态查询。
- [x] 自动化质量门禁：pytest、Python 编译、JS 语法、Docker 构建已写入 GitHub Actions 工作流。
- [x] 部署工件：`Dockerfile`、`render.yaml`、`.env.example`、部署说明已补齐。
- [x] GitHub 源码发布：V1.0 根目录引擎、`v1.5/` 与 `.github/workflows/geo-v15-ci.yml` 已通过 PR #1 合并到 `main`（merge commit `21918de`，4 项检查通过）。

## 待用户完成的发布门禁

- [ ] 在 Render 创建 Docker Web Service，导入 `GEO 可见度诊断_v1.5/render.yaml`。
- [ ] 在 Render 配置 `KIMI_API_KEY`、`DOUBAO_API_KEY`（以及实际使用的平台密钥）和生产域名 `CORS_ALLOW_ORIGINS`。
- [ ] 获得公网 URL 后，用真实品牌完成一次带有效密钥的 SSE、JSON、HTML 报告验收。
- [ ] 用外网桌面端、手机各走一遍；24 小时后复测一次。

## 验收结论

当前状态为 **本地可运行、待部署验收**。公网发布与 24 小时稳定性依赖部署账号、生产密钥和真实访问环境，尚未执行。
