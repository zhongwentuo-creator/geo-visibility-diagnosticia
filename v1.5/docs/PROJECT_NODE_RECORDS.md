# V1.5 项目各节关键数据记录

> 用于保存已验证的发布节点事实，方便后续协作、复测和交接。它不替代 `plan.md` 的任务状态或 `ACCEPTANCE.md` 的验收结论。

## 记录规则

- 只记录已产生证据的非敏感数据：URL、服务名、版本、区域、套餐、时间、检查结果和关联提交。
- API Key、Token、密码和密钥值永不记录；仅可记录“已配置”或“未配置”状态。
- 每项记录须同时回填 `plan.md` 与 `ACCEPTANCE.md`；若三者冲突，以验收记录和实际平台状态为准。

## 节点 2：Render Docker Web Service

| 字段 | 已验证数据 |
|---|---|
| 完成日期 | 2026-07-16 |
| GitHub 仓库 / 分支 | `zhongwentuo-creator/geo-visibility-diagnosticia` / `main` |
| Blueprint 路径 | `v1.5/render.yaml` |
| Blueprint / 服务名 | `geo-visibility-diagnosis-v15` |
| 运行形态 | Render Docker Web Service，Blueprint managed |
| 套餐 / 区域 | Free / Singapore |
| 公网地址 | https://geo-visibility-diagnosis-v15.onrender.com |
| 健康检查 | https://geo-visibility-diagnosis-v15.onrender.com/health |
| 健康检查实测 | `{"status":"ok","version":"1.5.0"}` |
| 部署结果 | Render Events 显示 `Deploy live` |
| 关联源码版本 | `ef17ee3`（PR #2 的合并提交） |
| API Key / CORS | 未配置，属于节点 3 |
| 已知运行特征 | Free 实例闲置后会休眠，首次访问可能延迟约 50 秒。 |

## 节点 3：Render 生产 API 与域名配置

| 字段 | 已验证数据 |
|---|---|
| 完成日期 | 2026-07-16 |
| 生产服务 | `geo-visibility-diagnosis-v15`（Render Environment） |
| 模型提供方 | Kimi（通用 LLM）+ 豆包（AI 搜索） |
| 已配置密钥项 | `KIMI_API_KEY`、`DOUBAO_API_KEY`；仅记录已配置状态，不记录值。 |
| 已配置域名项 | `CORS_ALLOW_ORIGINS` 已配置为生产访问来源；具体值不记录在仓库。 |
| 非敏感 Kimi 配置 | `KIMI_API_URL=https://api.moonshot.cn/v1`；`KIMI_MODEL=moonshot-v1-8k`。 |
| 路由源码版本 | PR #3 merge commit `2a21e8d`（包含 `e286a6e`）；Kimi-only 配置会使用 Moonshot 兼容端点。 |
| 配置后健康检查 | https://geo-visibility-diagnosis-v15.onrender.com/health 返回 `{"status":"ok","version":"1.5.0"}`。 |
| 节点结论 | 生产配置已完成；尚未以真实品牌验证外部 API 是否成功返回诊断数据。 |

## 下一节点

节点 4：用真实品牌在公网执行完整诊断，保存任务标识与 SSE、JSON、HTML 报告证据；任何 Key 或请求认证信息不得写入记录。
