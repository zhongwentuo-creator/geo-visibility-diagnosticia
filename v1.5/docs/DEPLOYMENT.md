# V1.5 部署说明

## 引擎来源

生产运行时使用同一 GitHub 仓库根目录中的 V1.0 引擎（`main.py`、`config.py`、
`stages/`、`report/`、`utils/`）。该引擎已包含 9 个阶段的 `progress_callback`，
是 V1.5 SSE 的真实事件来源；Dockerfile 会在构建镜像时将它复制到 `/app/engine`。

## 本地启动

在 `GEO 可见度诊断_v1.5` 目录执行：

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
GEO_ENGINE_ROOT='../GEO可见度诊断师_v1.0引擎/v1.0/src' \
  .venv/bin/python -m uvicorn api:app --app-dir src --host 127.0.0.1 --port 8000
```

浏览器打开 `http://127.0.0.1:8000`。前端由 FastAPI 同源提供，因此生产环境不会再指向
`127.0.0.1`。

## Docker 与 Render

GitHub 发布后，Docker 构建上下文必须是仓库根目录；V1.5 位于 `v1.5/`：

```bash
docker build -f v1.5/Dockerfile -t geo-diagnosis-v15 .
docker run --rm -p 8000:8000 \
  -e KIMI_API_KEY -e DOUBAO_API_KEY \
  -e CORS_ALLOW_ORIGINS='https://your-domain.example' \
  geo-diagnosis-v15
```

`render.yaml` 假定 Git 仓库根目录保留 V1.0 引擎，V1.5 位于 `v1.5/`：Docker 上下文为 `.`，
并同时监听 Web 层与引擎的改动。服务固定使用 Render `free` 套餐和 `singapore` 区域；
部署时在 Render Dashboard 配置 API Key，不要提交 `.env`。

生产环境默认使用 Kimi 完成通用 LLM 推理、豆包完成 AI 搜索。Blueprint 已固定非敏感配置
`KIMI_API_URL=https://api.moonshot.cn/v1` 与 `KIMI_MODEL=moonshot-v1-8k`；Render 中只需手动填写：

- `CORS_ALLOW_ORIGINS=https://geo-visibility-diagnosis-v15.onrender.com`
- `KIMI_API_KEY`：Kimi 开放平台生产密钥
- `DOUBAO_API_KEY`：火山方舟生产密钥

不要把密钥填写到 `OPENAI_API_KEY`，也不要把任何真实密钥提交到 GitHub。

本机当前的两个兄弟目录结构请使用 `Dockerfile.local`：

```bash
docker build -f 'GEO 可见度诊断_v1.5/Dockerfile.local' -t geo-diagnosis-v15 .
```

## 发布前必做

1. 设置生产域名为 `CORS_ALLOW_ORIGINS`，不要使用通配符。
2. 配置至少一个真实 LLM 平台所需 API Key。
3. 用真实品牌完成一次 SSE、JSON 报告和 HTML 报告验证。
4. 使用公网桌面端与移动端分别完成走查，并在 24 小时后复测。
