# V1.5 项目各节点关键数据记录

> 保存可复核、非敏感的发布事实。任务状态以 `plan.md` 为准，验收结论以 `ACCEPTANCE.md` 为准。

## 记录规则

- 只记录 URL、服务名、时间、任务 ID、公开响应结果与关联提交；不记录 API Key、Token、Cookie 或密钥值。
- 评分、耗时会随真实模型输出波动；任务是否成功以 `status=success`、9 阶段和报告可读性为准。

## 节点 2：Render Docker Web Service

| 字段 | 已验证数据 |
|---|---|
| 完成日期 | 2026-07-16 |
| 服务 | `geo-visibility-diagnosis-v15`，Render Docker Web Service，Free / Singapore |
| 公网地址 | https://geo-visibility-diagnosis-v15.onrender.com |
| 健康检查 | `/health` 返回 `{"status":"ok","version":"1.5.0"}` |

## 节点 3：生产配置

| 字段 | 已验证数据 |
|---|---|
| 模型与域名 | Kimi（通用 LLM）+ 豆包（AI 搜索）；生产 CORS 来源已配置。 |
| 密钥 | `KIMI_API_KEY`、`DOUBAO_API_KEY` 已在 Render 配置；值不记录。 |
| 路由修复 | PR #3 merge commit `2a21e8d`；Kimi-only 环境正确使用 Moonshot 兼容端点。 |

## 节点 4：SSE 修复后的真实品牌验收

| 字段 | 已验证数据 |
|---|---|
| 修复发布 | PR #5 已合并：`bf8684238d939acc5180c088dd7923eea87701d4`。 |
| 任务 | `GEO-20260716-234717-86530a`；听力熊 / 儿童 AI 对话智能体 / doubao。 |
| 结果 | `success`，9 阶段完成；Stage 4 为 9/9 查询（60.394 秒）；AIVO 75。 |
| SSE 可观测性 | 收到 `heartbeat` 与 `search_progress`；生产前端具备断流状态恢复。 |
| 报告 | JSON 200（21,264 bytes）；HTML 200（47,399 bytes）。 |

## 节点 5：跨设备与 T+24 小时复测

| 验收面 | 任务与结果 |
|---|---|
| 桌面端 | `GEO-20260716-235520-a88301`：`success`，9 阶段，Stage 4 为 18 条查询，AIVO 83；JSON 200（31,089 bytes），HTML 200（52,683 bytes）。 |
| 手机 4G | `GEO-20260717-002702-daf325`：iPhone / Safari / 4G，`success`，Stage 4 为 18/18 查询，AIVO 78；完成页、JSON 与 HTML 报告均已操作。 |
| T+24 复测 | `GEO-20260718-014657-f8732c`：距手机任务启动约 25 小时 20 分钟，`success`，Stage 4 为 18/18 查询（106.914 秒），AIVO 82；JSON 200（31,421 bytes），HTML 200（52,306 bytes）。 |
| 结论 | 无阻断问题，节点 5 通过。 |

## 结项状态

节点 1–6 已完成，V1.5 发布验收通过。后续问题与技术债见 `ISSUE_BACKLOG.md`，不要因它们存在而回退本次已验证的发布状态。
