# Handoff Note — V1.5 开发交接

**日期**：2026-07-14
**交接人**：当前对话（项目总档案）
**接收人**：新对话（V1.5 开发专用）
**项目路径**：`/Users/zhongwentuo/Desktop/WenTuo_kimi/WorkBuddy_Dify/GEO可见度诊断师`

---

## 一、项目状态快照

### V1.0 已完成（已冻结）

- 9 阶段 Python MVP 诊断流水线，已联调通过
- AIVO 评分体系（4 维度 × 25%），实测 74/100
- HTML 可视化报告（refer_1 浅色主题）
- JSON 结构化报告 + 自动修复（中文引号/转义/逗号）
- 双 LLM 后端兼容（Kimi + 豆包 + OpenAI）
- GitHub 已发布：https://github.com/zhongwentuo-creator/geo-visibility-diagnosticia

### V1.5 已规划（待执行）

**定位**：V1.0 核心逻辑不变，只加 Web 对话壳
**目标**：FastAPI + 前端聊天框 + SSE 流式推送 + Vercel 部署
**课程对标**：DAY-01（前端+部署）+ DAY-02（前后端打通）+ DAY-03（工程化）
**PRD**：`v1.5/docs/PRD.md`（已创建）
**实现方案**：`v1.5/v1.5/docs/IMPLEMENTATION_V1.5.md`（待创建）
**实现方案**：`v1.5/docs/IMPLEMENTATION_V1.5.md`（待创建）

---

## 二、关键文件索引

| 文件 | 路径 | 说明 |
|------|------|------|
| **V1.5 PRD** | `v1.5/docs/PRD.md` | 产品需求（对话式体验、技术架构、API 设计） |
| **V1.0 PRD** | `v1.0/PRD.md` | 产品说明书（中文，通俗易懂） |
| **技术实现** | `v1.0/docs/IMPLEMENTATION.md` | V1.0 技术方案（Vibe Coding） |
| **Agent 指南** | `AGENTS.md` | 架构总览、模块说明、扩展指南 |
| **项目记忆** | `MEMORY.md` | 踩坑记录（Bug 修复、配置规范、发布经验） |
| **文档地图** | `文档地图.md` | 所有文件导航（按角色选阅读路径） |
| **主入口** | `v1.0/src/main.py` | V1.0 诊断引擎（9 阶段流水线） |
| **API 封装** | `v1.0/src/utils/api_client.py` | Kimi + 豆包 + OpenAI 三端兼容 |
| **报告模板** | `v1.0/src/report/template.html` | Jinja2 HTML 模板（CSS/SVG 内嵌） |

---

## 三、V1.5 开发任务分解（Phase 1-3）

### Phase 1：FastAPI 后端（1-2 天）

**目标**：创建 `v1.5/src/api.py`，包装 V1.0 的 `v1.0/src/main.py:diagnose()` 为 Web API

**具体任务**：
1. 安装依赖：`pip install fastapi uvicorn[standard]`（追加到 `requirements.txt`）
2. 创建 `api.py`：
   - `POST /api/diagnose` — 启动诊断，返回 `task_id`
   - `GET /api/diagnose/{task_id}` — 查询进度
   - `GET /api/diagnose/{task_id}/stream` — SSE 流式推送
3. 异步任务执行：
   - `asyncio.create_task` 后台运行 `main.diagnose()`
   - 内存字典存储任务状态（`task_id → {status, progress, result}`）
4. SSE 事件设计：
   - `event: stage_start` / `event: stage_complete` / `event: complete` / `event: error`
5. 异常处理：阶段失败时推送降级信息，不中断 SSE 流

**验证标准**：
- `curl POST /api/diagnose` 返回 `task_id`
- 浏览器 EventSource 能收到实时事件
- 诊断完成，数据正确

---

### Phase 2：前端对话界面（1-2 天）

**目标**：创建 `index.html`，实现对话式诊断体验

**具体任务**：
1. 创建 `index.html`：
   - 聊天框 UI（用户消息在右，系统消息在左）
   - 输入框 + 发送按钮
2. 实现消息发送：
   - 用户输入 → 提取品牌名/品类 → 调用 `POST /api/diagnose`
3. 实现 SSE 接收：
   - `new EventSource('/api/diagnose/{task_id}/stream')`
   - 接收事件 → 渲染进度卡片（阶段名称、耗时、摘要）
4. 实现报告展示：
   - 诊断完成后渲染 AIVO 摘要卡片（分数、等级、4 维度）
   - 提供下载按钮（HTML 报告、JSON 数据）
5. 美化：
   - CSS 样式（头像、气泡、进度条、卡片）
   - 响应式布局（手机可用）

**技术选型**：纯 HTML + JS（或 Vue 3）+ SSE 客户端

**验证标准**：
- 打开网页能看到对话界面
- 输入品牌名 → 看到实时进度更新 → 看到最终报告
- 报告可下载

---

### Phase 3：部署上线（0.5-1 天）

**目标**：部署到 Vercel，公网可访问

**具体任务**：
1. 更新 `v1.0/src/requirements.txt`：包含 `fastapi`、`uvicorn`、`httpx` 等
2. 创建 `vercel.json`：配置 FastAPI 启动命令
3. 配置 `.env`（生产环境 API Key）
4. 执行 `vercel --prod` 部署
5. 测试：用流量打开 URL，完整走一遍诊断流程

**验证标准**：
- 朋友能用手机打开 URL 体验
- 诊断流程完整，无报错
- 24 小时内稳定运行

---

## 四、关键设计决策（已确认）

| 决策 | 选择 | 原因 |
|------|------|------|
| 流式协议 | **SSE**（而非 WebSocket） | 单向推送足够简单，HTTP 协议兼容性好 |
| 前端框架 | **纯 HTML + JS**（或 Vue 3） | 越简单越好，V1.5 追求速度 |
| 会话管理 | **内存字典**（无数据库） | V1.5 不持久化，每次刷新重新开始 |
| 部署平台 | **Vercel** | 一键部署，免费额度充足，国内可访问 |
| 后端框架 | **FastAPI** | 异步原生支持，自动 API 文档，Python 生态 |
| 报告存储 | **内存/临时文件** | 诊断完成后即返回，不长期存储 |

---

## 五、已知约束和注意事项

1. **V1.0 核心逻辑不可改**：`v1.0/src/main.py` 和 `v1.0/src/stages/` 里的代码完全复用，不动任何诊断逻辑
2. **API Key 安全**：生产环境 `.env` 中的 Key 不能提交到 GitHub（已 `.gitignore`）
3. **超时处理**：豆包深度思考模型仍慢（15-25s/请求），SSE 需设置较长超时
4. **并发限制**：V1.5 无队列，同时只能跑 1-2 个诊断（V2.0 加 Celery）
5. **资源限制**：Vercel 免费版有函数执行时间限制（10s-60s），需测试是否足够

---

## 六、用户期望

**用户明确说**：
- "我认可路径 A：V1.0 + 对话壳，版本叫 V1.5"
- "V2.0 暂不开启，小版本迭代，快步跑"
- "目的非常清晰：把 vibe coding 的链路跑通，符合 VibeCoding 培训课程包含的能力"
- "当前对话保留，V1.5 开发开新对话进行"

**用户的核心诉求**：
1. 体验层面：从命令行 → 浏览器对话（像 ChatGPT 一样聊天）
2. 课程层面：把 DAY-01（前端+部署）到 DAY-03（工程化）跑通
3. 时间层面：3-5 天完成，快速验证

---

## 七、新对话启动建议

### 新对话第一句话建议

```
你是 GEO 可见度诊断师 V1.5 的开发助手。

项目路径：/Users/zhongwentuo/Desktop/WenTuo_kimi/WorkBuddy_Dify/GEO可见度诊断师
请先读取以下文件了解上下文：
1. v1.5/docs/PRD.md — V1.5 产品需求
2. AGENTS.md — 项目架构和模块说明
3. MEMORY.md — 踩坑记录（维护前必读）
4. handoff_v1.5.md — 本交接文档

然后我们开始 Phase 1：FastAPI 后端开发。
```

### 新对话需知

- 项目已有 Git 仓库，提交后需要推送到 GitHub 更新
- 用户有 GitHub 账号：`zhongwentuo-creator`
- 仓库地址：`https://github.com/zhongwentuo-creator/geo-visibility-diagnosticia`
- 用户已有 GitHub Classic Token（`repo` 权限），需询问是否复用或创建新 Token

---

*本交接文档在 V1.5 启动时创建，供新对话 AI 快速了解项目状态和开发任务。*
