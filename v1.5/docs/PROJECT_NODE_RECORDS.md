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

## 节点 4：真实品牌公网完整诊断

| 字段 | 已验证数据 |
|---|---|
| 首次执行日期 | 2026-07-16 |
| 公网服务 | https://geo-visibility-diagnosis-v15.onrender.com |
| 品牌 / 产品 / 平台 | 听力熊 / 儿童 AI 对话智能体 / doubao |
| 官网 | https://www.tinglexiong.com |
| 首次任务 ID | `GEO-20260716-151348-5d5384` |
| 后台任务结果 | `success`；9 个阶段均完成 |
| 关键业务结果 | AIVO 81（良好）；18 条查询；品牌提及率 94.4% |
| 主要阶段耗时 | Stage 1：18.500 秒；Stage 2：4.478 秒；Stage 3：1.663 秒；Stage 4：113.082 秒；Stage 6：2.111 秒 |
| SSE 结果 | 未通过。客户端在 Stage 4 开始后提前结束；后台任务随后成功完成。 |
| JSON 报告 | HTTP 200；`application/json`；31,803 字节 |
| HTML 报告 | HTTP 200；`text/html`；52,387 字节 |
| 根因判断 | Stage 4 长时间没有中间事件，连接可能在代理/客户端侧被关闭；前端把原生 EventSource 断线当作任务失败。 |
| 修复记录 | PR #5 / commit `7a79b48`；增加 heartbeat、Stage 4 查询进度、唯一完成阶段计数和前端状态恢复；代码与 CI 已通过，尚未部署。 |
| 当前结论 | 节点 4 部分通过、仍在进行中；JSON/HTML 通过，完整 SSE 待修复部署后复测。 |

## 下一步

经用户确认后合并 PR #5，等待 Render 部署完成，再按 `NODE4_EXECUTION.md` 只执行一次新的真实品牌诊断并同步回填验收证据。任何 Key、Token、cookie 或请求认证信息不得写入记录。
