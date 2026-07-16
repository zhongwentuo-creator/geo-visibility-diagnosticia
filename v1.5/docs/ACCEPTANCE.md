# V1.5 发布验收记录

## 本轮已通过

| 关卡 | 结果 | 证据 |
|---|---|---|
| 可复现依赖 | 通过 | `requirements.txt` + 项目内 `.venv` 安装成功。 |
| 静态质量 | 通过 | `py_compile` 与 `node --check` 通过。 |
| API/SSE 自动化回归 | 通过 | `pytest -q`：3 passed，覆盖健康检查、同源首页、9 阶段 SSE、JSON/HTML 报告和错误事件。 |
| 本机 HTTP 烟测 | 通过 | `127.0.0.1:8015` 上用测试引擎验证 POST、完整 SSE、报告端点。 |
| 本地 V1.0 真实引擎联调 | 通过（降级数据） | `127.0.0.1:8016` 完成「听力熊」诊断，返回 9 阶段事件、AIVO 69/100、JSON 与 50,014 字节 HTML 报告。 |
| 部署工件 | 已准备 | Dockerfile、Render Blueprint、环境变量样例、CI 工作流均已生成；当前机器未安装 Docker，镜像构建留待 GitHub Actions/Render 执行。 |
| GitHub 源码与 CI 发布 | 通过 | PR #1 已合并到 `main`（merge commit `21918de`）；V1.0 根目录引擎、`v1.5/` 和 `geo-v15-ci.yml` 位于同一仓库，4 项 GitHub 检查通过。 |
| Render Docker Web Service | 通过 | 2026-07-16 从 `main` 的 `v1.5/render.yaml` 创建 `geo-visibility-diagnosis-v15`（Free / Singapore）；Render 显示 `Deploy live`，公网 `/health` 实测返回 `{"status":"ok","version":"1.5.0"}`。详见 `PROJECT_NODE_RECORDS.md`。 |
| Render 生产配置 | 通过（配置就绪） | Render `Environment` 已配置 Kimi + 豆包所需 Key、`CORS_ALLOW_ORIGINS`，以及非敏感 Kimi base URL / model；PR #3（merge commit `2a21e8d`）已使 Kimi-only 配置路由至 Moonshot。密钥值不进入仓库。该证据不代替真实品牌 API 调用验收。 |

## 已知边界

本轮真实引擎联调未注入平台密钥，因此 S3、S6 等阶段触发了引擎内置降级，S4 明确标注为模拟搜索数据。它证明的是 **V1.5 Web/SSE/报告链路**，不是生产数据质量。

## 发布前阻断项

1. 在公网、真实密钥下完成一次真实品牌诊断，确认完整 SSE、JSON 和 HTML 报告。
2. 桌面端与手机端各验证一次，24 小时后复测。

## 验收命令

```bash
cd 'GEO 可见度诊断_v1.5'
.venv/bin/python -m pytest -q
GEO_ENGINE_ROOT='../GEO可见度诊断师_v1.0引擎/v1.0/src' \
  .venv/bin/python -m uvicorn api:app --app-dir src --host 127.0.0.1 --port 8000
```
