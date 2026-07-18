# GEO 可见度诊断师 V1.5

V1.5 为既有 V1.0 九阶段 GEO 诊断引擎提供对话式 Web 体验：用户以自然语言发起诊断，浏览器通过 SSE 接收阶段进度，并在完成后查看 JSON 与 HTML 报告。

> V1.5 不改诊断算法；它增加 FastAPI 服务、SSE 适配层、静态对话工作台和发布配置。

当前发布状态：Render 公网服务已完成真实品牌、桌面、手机 4G 与 T+24 小时复测，V1.5 发布验收通过。历史 SSE 修复见 [节点 4 记录](docs/NODE4_EXECUTION.md)，跨设备与稳定性证据见 [节点 5 记录](docs/NODE5_EXECUTION.md)。

## 能力

- 自然语言输入，自动识别品牌、产品类型和官网
- 9 阶段诊断过程的 SSE 事件流
- AIVO 摘要卡片、JSON 报告与 HTML 报告下载
- 同源前后端服务，生产环境不依赖本机地址
- FastAPI 回归测试与 GitHub Actions 质量门禁

## 本地运行

当前工作区中，V1.0 引擎位于相邻目录：

```bash
cd 'GEO 可见度诊断_v1.5'
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
GEO_ENGINE_ROOT='../GEO可见度诊断师_v1.0引擎/v1.0/src' \
  .venv/bin/python -m uvicorn api:app --app-dir src --host 127.0.0.1 --port 8000
```

打开 <http://127.0.0.1:8000>。

## 测试

```bash
.venv/bin/python -m pytest -q
```

测试覆盖健康检查、同源工作台、SSE 事件序列、JSON/HTML 报告端点与错误降级。

## 项目结构

```text
v1.5/
├── src/
│   ├── api.py                 # FastAPI + REST + SSE
│   ├── engine_adapter.py      # V1.0 引擎适配，不修改诊断算法
│   └── static/                # 对话工作台
├── tests/                     # API/SSE 回归测试
├── docs/                      # PRD、设计、计划、验收与部署说明
├── Dockerfile
├── render.yaml
└── requirements.txt
```

## 发布说明

V1.5 应发布到既有仓库 `zhongwentuo-creator/geo-visibility-diagnosticia` 的 `v1.5/` 目录，保留仓库根目录的 V1.0 引擎。具体结构、迁移文件和发布门禁见 [GitHub 发布说明](docs/GITHUB_RELEASE.md)。

生产部署、API Key、CORS 和公网验收见 [部署说明](docs/DEPLOYMENT.md)。

## 协作与验收入口

- [节点 4 执行记录](docs/NODE4_EXECUTION.md)：SSE 修复与生产复测历史。
- [节点 5 执行与协作入口](docs/NODE5_EXECUTION.md)：跨设备、T+24 小时证据与后续读取顺序。
- [交付计划](docs/plan.md)：唯一任务状态。
- [问题与改进待办池](docs/ISSUE_BACKLOG.md)：交互、业务、稳定性与技术债问题的分诊入口。
- [技术设计说明](docs/SDD.md)：当前实现、运行边界与后续维护规则。
- [发布验收记录](docs/ACCEPTANCE.md)：验收结论与证据。
- [项目节点记录](docs/PROJECT_NODE_RECORDS.md)：非敏感运行数据。
