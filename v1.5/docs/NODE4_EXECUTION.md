# V1.5 节点 4 执行与协作入口

> 本文件是节点 4 的单一执行入口，保存当前行动状态、验收顺序和交接信息；它不替代 `plan.md` 的任务状态、`ACCEPTANCE.md` 的验收结论或 `PROJECT_NODE_RECORDS.md` 的运行证据。

## 1. 节点目标

在 Render 公网服务上，用真实品牌和生产密钥完成一次完整诊断，并同时证明：

1. SSE 从 `start` 持续到 `complete`，长耗时阶段有 `heartbeat` 或 `search_progress`，不会被误判为诊断失败。
2. 任务最终状态为 `success`，9 个阶段均完成。
3. JSON 报告返回 `200 application/json`，内容可解析且包含诊断 ID、完整查询数据和 AIVO 结果。
4. HTML 报告返回 `200 text/html`，内容非空且可在浏览器打开。

只有四项同时通过，节点 4 才能标记为完成。

## 2. 完成状态（历史复核）

更新时间：2026-07-18

| 项目 | 已验证事实 |
|---|---|
| 公网地址 | https://geo-visibility-diagnosis-v15.onrender.com |
| 修复发布 | PR #5 已合并到 `main`，merge commit `bf8684238d939acc5180c088dd7923eea87701d4`；Render 公网脚本已包含 heartbeat、查询进度与状态恢复逻辑。 |
| 复测任务 | `GEO-20260716-234717-86530a`，最终 `success`，9 阶段完成，Stage 4 为 9/9 查询，AIVO 75。 |
| SSE | Stage 4 期间已收到 heartbeat 与查询进度；后续真实工作台在桌面、手机端均进入完成态。 |
| JSON / HTML | JSON HTTP 200（21,264 bytes）；HTML HTTP 200（47,399 bytes）。 |
| 节点结论 | **通过**。首次空闲断流保留为历史根因，后续跨设备与 T+24 证据见 `NODE5_EXECUTION.md`。 |

PR：https://github.com/zhongwentuo-creator/geo-visibility-diagnosticia/pull/5

## 3. 文档职责与冲突处理

| 文件 | 负责内容 | 不应写入 |
|---|---|---|
| `AGENTS.md` | 协作规则、版本边界、发布门禁 | 运行流水账、密钥 |
| `MEMORY.md` | 已确认且可复用的事实、根因和决策 | 临时 PR 状态、重复规格 |
| `README.md` / `v1.5/README.md` | 项目导航与当前版本入口 | 详细验收日志 |
| `v1.5/docs/NODE4_EXECUTION.md` | 节点 4 修复、复测与历史交接 | 最终验收结论的唯一副本 |
| `v1.5/docs/NODE5_EXECUTION.md` | 节点 5 跨设备与稳定性证据 | 最终验收结论的唯一副本 |
| `v1.5/docs/plan.md` | V1.5 唯一任务状态 | 详细运行数据 |
| `v1.5/docs/ACCEPTANCE.md` | 验收结论与通过/失败证据 | 密钥、未验证推断 |
| `v1.5/docs/PROJECT_NODE_RECORDS.md` | 非敏感运行数据、任务 ID、耗时和响应结果 | 验收状态替代品 |
| `docs/VIBECODING_ACCEPTANCE_MATRIX.md` | V1.5 承诺与证据映射 | 节点运行细节 |

发生冲突时，先以实际平台状态和 `ACCEPTANCE.md` 的证据为准，再同步修正 `plan.md`、本文件、节点记录和矩阵。不得用“代码已提交”“PR 已合并”代替“公网验收通过”。

## 4. 新对话读取顺序

新对话只需按以下顺序读取，不要重扫整个仓库：

1. 根目录 `AGENTS.md` 的第 0 节。
2. 根目录 `MEMORY.md` 的“当前有效事实”。
3. 本文件的“当前状态”和“下一步”。
4. 只有在更新状态或核验证据时，才读取 `plan.md`、`ACCEPTANCE.md`、`PROJECT_NODE_RECORDS.md` 和矩阵。
5. 只有在修复失败或 CI 失败时，才进入代码和历史记录。

推荐触发语：

> 请读取 `AGENTS.md`、`MEMORY.md` 和 `v1.5/docs/NODE4_EXECUTION.md`，继续执行《GEO 可见度诊断师_1.5》第 4 节点；先报告当前状态与下一步，再执行，不要重复已完成验证。

## 5. 后续

节点 4 已完成，不再为本节点重复发起付费诊断。若出现新的 SSE、报告或部署问题，先写入 `ISSUE_BACKLOG.md`，再按新迭代计划处理。

## 6. 公网复测命令

以下命令不包含任何密钥。生产密钥只存在 Render 环境变量中。

```bash
export GEO_V15_BASE_URL='https://geo-visibility-diagnosis-v15.onrender.com'

curl -fsS "$GEO_V15_BASE_URL/health"

curl -fsS -X POST "$GEO_V15_BASE_URL/api/diagnose" \
  -H 'Content-Type: application/json' \
  --data '{"brand":"听力熊","category":"儿童 AI 对话智能体","website":"https://www.tinglexiong.com","platform":"doubao"}'
```

取得新的 `<task_id>` 后，分别执行：

```bash
curl -N "$GEO_V15_BASE_URL/api/diagnose/<task_id>/stream"
curl -fsS "$GEO_V15_BASE_URL/api/diagnose/<task_id>"
curl -fsS "$GEO_V15_BASE_URL/api/diagnose/<task_id>/report" -o /tmp/geo-v15-node4-report.json
curl -fsS "$GEO_V15_BASE_URL/api/diagnose/<task_id>/report/html" -o /tmp/geo-v15-node4-report.html
```

## 7. 复测判定表

| 验收项 | 通过标准 | 记录位置 |
|---|---|---|
| 健康检查 | HTTP 200，返回 `status=ok`、`version=1.5.0` | 节点记录 |
| SSE | 收到 `start`、9 个阶段完成、`complete`；Stage 4 期间有 heartbeat/query 进度且连接不提前结束 | 验收记录 + 节点记录 |
| 状态接口 | `status=success`、`progress=1.0`、9 个唯一阶段、Stage 4 查询进度完成 | 验收记录 |
| JSON | HTTP 200、可解析、关键字段存在、文件非空 | 验收记录 + 节点记录 |
| HTML | HTTP 200、`text/html`、文件非空、浏览器可打开 | 验收记录 + 节点记录 |
| 数据质量 | 确认使用生产 Kimi/豆包，不是模拟搜索数据 | 验收记录 |

## 8. 安全与费用边界

- 不在仓库、截图、终端记录或对话中保存 API Key、GitHub Token、cookie 或一次性设备码。
- 只有 Render 显示新提交部署完成后才发起付费诊断。
- 同一次任务优先通过状态接口恢复，不因 SSE 断线立即创建新任务。
- 截图前遮盖凭据和响应 cookie；节点记录只保存非敏感结果。

## 9. 交接更新模板

每次暂停前只更新下面五项，避免写成长日志：

```text
更新时间：YYYY-MM-DD HH:MM
当前状态：进行中 / 已通过 / 阻断
最新证据：PR、部署提交、任务 ID 或响应结果
当前阻断：没有则写“无”
唯一下一步：一个可立即执行的动作
```
