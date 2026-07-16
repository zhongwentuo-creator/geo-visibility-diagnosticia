# MEMORY.md — GEO 可见度诊断师项目记忆

> 记录本项目联调、维护、扩展过程中的关键经验与踩坑记录。
> 供人类开发者和 AI Agent 在后续工作中快速定位问题、避免重复踩坑。

---

## 当前有效事实（2026-07-17）

- **仓库结构**：根目录是 V1.0 九阶段引擎；`v1.5/` 是 FastAPI、SSE、静态对话工作台、测试和部署工件。V1.5 不修改诊断算法。
- **GitHub 交付**：PR #1 已合并到 `main`（merge commit `21918de`）；四项 GitHub 检查通过。该证据只表示源码与 CI 发布完成，不表示公网可用。
- **Render 节点 2**：2026-07-16 已通过 Blueprint 创建免费 Docker Web Service；服务为 `geo-visibility-diagnosis-v15`，区域为 `singapore`。公网健康检查已返回 `{"status":"ok","version":"1.5.0"}`。
- **Render 节点 3**：生产环境已选择 Kimi + 豆包，并在 Render 配置 `KIMI_API_KEY`、`DOUBAO_API_KEY`、`CORS_ALLOW_ORIGINS`、`KIMI_API_URL` 与 `KIMI_MODEL`。密钥值和 CORS 具体值不记录在仓库；`KIMI_API_URL` 使用 Moonshot OpenAI 兼容 base URL，模型为 `moonshot-v1-8k`。
- **生产路由修复**：PR #3 已合并到 `main`（merge commit `2a21e8d`，包含 `e286a6e`）。Stage 1 与通用 LLM 客户端在仅配置 Kimi Key 时会路由至 Moonshot，避免误落到 OpenAI 默认地址。
- **节点 4 首次生产诊断**：真实品牌任务在后台完成 9 阶段并成功生成 JSON/HTML 报告，但客户端 SSE 在 Stage 4 长时间无事件时提前结束，因此节点 4 仅部分通过。Stage 4 约耗时 113 秒，是当前连接稳定性的主要风险。
- **SSE 修复决策**：不调整 V1.0 诊断算法、模型、查询数量或评分；通过周期 heartbeat、Stage 4 单条查询进度、唯一完成阶段计数和前端状态恢复解决“后台成功、前端误报失败”。观测回调失败不得影响诊断主流程。
- **V1.5 当前状态**：公网服务、生产配置及首次真实诊断均已产生证据；JSON/HTML 已通过，完整 SSE 仍需在修复部署后复测。桌面与手机走查、24 小时复测仍待完成。
- **状态来源**：节点 4 当前行动先看 `v1.5/docs/NODE4_EXECUTION.md`；任务状态只看 `v1.5/docs/plan.md`；验收证据只看 `v1.5/docs/ACCEPTANCE.md`；节点运行数据看 `v1.5/docs/PROJECT_NODE_RECORDS.md`；课程/VibeCoding 范围映射只看 `docs/VIBECODING_ACCEPTANCE_MATRIX.md`。
- **安全边界**：API Key、Token 和任何密钥值不写入仓库、`MEMORY.md`、节点记录或验收截图。可公开的部署 URL、健康检查结果和非敏感配置选择可写入节点记录；生产密钥值仅配置在部署平台。

以下记录是历史联调经验；若与“当前有效事实”冲突，以当前有效事实和对应版本文档为准。

---

## 2026-07-14 联调修复记录（9 Bug 修复）

### 背景

本次联调以品牌"听力熊"为目标，运行完整 9 阶段流水线，目标是生成可读的 JSON 报告和 HTML 可视化报告。联调过程中发现并修复了 9 个核心 Bug，涉及 API 客户端、配置管理、JSON 处理、Python 兼容性等多个层面。

**最终得分**：AIVO 总分 79 / 100（中等），HTML 报告和 JSON 数据均成功生成。

---

### Bug 1：Jinja2 模板报错 `'dict object' has no attribute 'meta'`

**现象**：`main.py` 运行到 `_generate_html_report` 时，`report.meta` 访问失败。

**根因**：`utils/json_repair.py` 中的 `repair_json()` 函数将已合法的字典重新序列化后，`_repair_chinese_quotes()` 把 JSON 字符串值内部的**中文双引号**（`"` 和 `"`）替换为 ASCII `"`，直接破坏了 JSON 结构。例如 `"answerSnippet": "关于"听力熊"的搜索"` 变成非法 JSON。`json.loads()` 失败后返回错误结构：`{'error': ..., 'partial_data': ...}`，替代了正常的 `report` 字典。

**修复**：`repair_json()` 增加**快速路径**：先尝试 `json.dumps(data) → json.loads()` 序列化-反序列化循环，若成功直接返回原数据，跳过字符串级修复。只在数据本身不可序列化时才进入修复流程。

**文件**：`utils/json_repair.py`

**教训**：中文引号修复工具不可盲目对已经是合法 JSON 的字符串进行替换。先判断再修复。

---

### Bug 2：Python 3.9 不支持 `str | None` 联合类型语法

**现象**：`TypeError: unsupported operand type(s) for |: 'type' and 'NoneType'`

**根因**：`stages/s2_infra_eval.py` 使用了 `str | None` 联合类型（Python 3.10+ 特性），但系统环境是 Python 3.9.6。

**修复**：在文件开头添加 `from __future__ import annotations`。

**文件**：`stages/s2_infra_eval.py`

**教训**：项目代码中凡使用 `X | Y` 语法的文件，都必须包含 `from __future__ import annotations`。如果项目升级 Python 3.10+，这条限制可以取消。

---

### Bug 3：`.env` 配置被系统旧 Key 覆盖

**现象**：`config.py` 已加载 `.env`，但 `os.environ.get('KIMI_API_KEY')` 返回的是系统中残留的旧无效 Key（`sk-kimi-ah0yc...`），而非 `.env` 中正确的新 Key（`sk-ugFda...`）。Kimi API 返回 401。

**根因**：`config.py` 中 `load_dotenv(override=False)` 不覆盖已有环境变量。系统 shell 启动时预加载了旧的 `KIMI_API_KEY`。

**修复**：`load_dotenv(dotenv_path=".env", encoding="utf-8", override=True)`，让 `.env` 文件优先于系统环境变量。

**文件**：`config.py`

**教训**：`override=False` 适用于"环境变量优先"场景，但当开发者在 `.env` 中更新 Key 时，系统残留的旧 Key 会静默生效。`.env` 在开发环境中应优先。生产环境可用环境变量覆盖，但开发调试时 `override=True` 更合理。

---

### Bug 4：API Key 命名不匹配（`KIMI_API_KEY` vs `OPENAI_API_KEY`）

**现象**：`llm_chat()` 返回空字符串（`EMPTY`）。直接 `httpx` 测试 Kimi API 正常，但通过 `api_client` 调用就失败。

**根因**：`.env` 中只配置了 `KIMI_API_KEY`，但 `utils/api_client.py` 的 `_get_openai_key()` 只读取 `OPENAI_API_KEY`。当调用 `llm_chat(model='gpt-4o')` 时，`_select_endpoint()` 判定为 OpenAI 端点，但 Key 为空，回退到豆包端点。豆包不支持 `gpt-4o` 模型名，返回 404，最终 `_post_with_retry` 吞掉异常返回 None。

**修复**：`_get_openai_key()` 改为 `os.environ.get("OPENAI_API_KEY") or os.environ.get("KIMI_API_KEY", "")`，同时兼容两者。`_get_openai_url()` 同理。

**文件**：`utils/api_client.py`

**教训**：API 客户端封装必须兼容项目实际使用的 Key 命名。本项目使用 Kimi 替代 OpenAI，但代码中仍写死 `OPENAI_API_KEY`，这是典型的命名与实现不匹配。

---

### Bug 5：URL 重复拼接 `/chat/completions/chat/completions`

**现象**：`llm_chat()` 返回空。直接 `httpx` 测试 Kimi API 正常，但通过 `api_client` 调用就失败。

**根因**：`.env` 中 `KIMI_API_URL=https://api.moonshot.cn/v1/chat/completions`，但 `api_client.py` 的 `llm_chat()` 又拼了一次 `/chat/completions`，最终 URL 变成 `https://api.moonshot.cn/v1/chat/completions/chat/completions`。Kimi 返回 404，异常被吞掉，最终返回空字符串。

**修复**：新增 `_chat_url(base_url)` 函数，智能检测 `base_url` 是否已包含 `/chat/completions` 后缀，避免重复拼接。

**文件**：`utils/api_client.py`

**教训**：配置中的 URL 可能是"base"（如 `https://api.moonshot.cn/v1`）或"完整 endpoint"（如 `https://api.moonshot.cn/v1/chat/completions`）。客户端代码必须兼容两种形式，不能盲目拼接路径。建议在 `.env` 中统一使用 base URL，或在代码中做去重处理。

---

### Bug 6：模型名 `gpt-4o` 不被 Kimi 支持

**现象**：各 stage 统一使用 `model="gpt-4o"`，但 Kimi API 返回 `Not found the model gpt-4o or Permission denied`（404）。

**根因**：Kimi（Moonshot）的模型命名体系与 OpenAI 不同。Kimi 支持的模型名如 `moonshot-v1-8k`、`moonshot-v1-32k`，不支持 `gpt-4o`、`gpt-4o-mini`、`gpt-4` 等 OpenAI 专属模型名。

**修复**：新增 `_resolve_model(model, base_url)` 函数，当 `base_url` 包含 `moonshot` 或 `kimi` 时，自动将 OpenAI 模型名映射到 Kimi 等效模型：
- `gpt-4o` → `moonshot-v1-8k`
- `gpt-4o-mini` → `moonshot-v1-8k`
- `gpt-4` → `moonshot-v1-32k`

**文件**：`utils/api_client.py`

**教训**：多 LLM 后端切换时，模型名映射表必须维护。随着新模型发布，映射表需要更新。

---

### Bug 7：S6 舆情 fallback 错误路由到豆包 API

**现象**：S6 舆情扫描返回 `negativeRate=-1`，`riskLevel="数据缺失"`，LLM fallback 未触发。

**根因**：`stages/s6_sentiment.py` 的 `_llm_sentiment_fallback()` 检查 `os.environ.get("OPENAI_API_KEY")` 为空时回退到 `model="doubao-pro-32k"`。但此时系统环境变量中残留的 OpenAI Key 已过期（即使 `.env` 中有新 Key），fallback 使用了无效的豆包 Key（401 错误），最终返回 None。

**修复**：检查逻辑改为 `has_openai_key = bool(os.environ.get("OPENAI_API_KEY") or os.environ.get("KIMI_API_KEY"))`，优先使用 Kimi。同时 `response_format` 从 `"json"` 改为 `"text"`（Kimi 的 `json_object` 模式兼容性不如 text）。

**文件**：`stages/s6_sentiment.py`

**教训**：LLM fallback 的路由逻辑必须与项目实际配置一致。本项目主要使用 Kimi，但代码中仍写死检查 `OPENAI_API_KEY`，导致 fallback 路由错误。

---

### Bug 8：豆包 API 使用错误端点（Chat Completions vs Responses）

**现象**：豆包 `doubao_search()` 返回空，直接 `httpx` 测试 `chat/completions` 端点返回 401 AuthenticationError。

**根因**：豆包（火山方舟）的 Seed 系列模型（如 `doubao-seed-evolving`）使用 **Responses API**（`/api/v3/responses`），而非标准 Chat Completions API（`/api/v3/chat/completions`）。Responses API 的返回格式也不同：`output[]` 数组中 `type="message"` 的 `content` 包含 `type="output_text"` 的文本块，而非 `choices[0].message.content`。

**修复**：
1. 新增 `doubao_chat()` 和 `doubao_search()` 使用 `_post_doubao_responses()` 封装 Responses API
2. 新增 `_parse_doubao_response(data)` 解析豆包返回格式
3. `_get_doubao_url()` 返回的 URL 若包含 `/chat/completions`，自动去除后追加 `/responses`

**文件**：`utils/api_client.py`

**教训**：不同 LLM 提供商的 API 格式差异很大。豆包 Seed 系列不走标准 Chat Completions，必须独立封装。`doubao-pro-32k` 等模型可能走 Chat Completions，但 `doubao-seed-evolving` 只走 Responses API。

---

### Bug 9：豆包 Responses API 不支持 `role: "system"`

**现象**：豆包请求挂起 20-30 秒然后 `ReadTimeout`。

**根因**：豆包 Responses API 的 `input` 数组不支持 `role: "system"`。当 payload 包含 `{"role": "system", ...}` 时，服务器无响应直到超时。

**修复**：将 system prompt 合并到 user message 中：
```python
combined_prompt = f"【系统指令】{system_prompt}\n\n【用户问题】{prompt}"
input_items = [{"role": "user", "content": [{"type": "input_text", "text": combined_prompt}]}]
```

**文件**：`utils/api_client.py`（`doubao_chat()` 和 `doubao_search()`）

**教训**：豆包 Responses API 的 `input` 数组只支持 `role: "user"`（和 `role: "assistant"` 在后续对话中）。System prompt 必须通过前置标记或合并到 user message 中传递。

---

### Bug 10：豆包 `doubao-seed-evolving` 深度思考模型响应极慢

**现象**：复杂搜索 prompt（如"听力熊 儿童AI智能体 怎么样"）需要 96 秒，触发 3 次重试后超时失败。简单问候（"你好"）只需 7 秒。

**根因**：`doubao-seed-evolving` 是**深度思考模型**，对复杂搜索问题会生成大量推理 token（如 400+ reasoning tokens），导致响应时间飙升到 90 秒以上。

**修复**：
1. 在 system prompt 中明确要求"直接给出答案，不需要展示思考过程，控制在300字以内"
2. 超时从 30 秒提升到 60 秒
3. 重试次数从 3 次降到 2 次

**文件**：`utils/api_client.py`

**教训**：深度思考模型不适合实时搜索场景。如果后续对响应时间敏感，应考虑：
- 使用非思考型模型（如 `doubao-pro-32k` 或 `doubao-pro-256k`）
- 启用豆包的流式输出（SSE）并设置 early cutoff
- 缓存搜索结果减少重复调用

---

## 配置规范（经联调验证）

### `.env` 文件模板

```bash
# Kimi / Moonshot AI（LLM 推理：阶段 1/3/7/9）
KIMI_API_KEY=sk-xxx
KIMI_API_URL=https://api.moonshot.cn/v1/chat/completions

# 豆包（AI 搜索测试：阶段 4）
# 注意：使用 Responses API，非 Chat Completions
DOUBAO_API_KEY=ark-xxx
DOUBAO_BASE_URL=https://ark.cn-beijing.volces.com/api/v3

# 运行参数
DEFAULT_PLATFORM=doubao
MAX_CONCURRENT_SEARCHES=3
REQUEST_TIMEOUT=60
MAX_RETRIES=2
```

### 关键注意事项

1. **KIMI_API_URL 必须包含 `/chat/completions`**：`api_client.py` 已处理重复拼接，但 `.env` 中配置完整 URL 更直观
2. **豆包模型选择**：`doubao-seed-evolving`（深度思考，慢但准确）vs `doubao-pro-32k`（快，标准 Chat Completions）
3. **Python 版本**：当前代码兼容 Python 3.9，但所有使用 `X | Y` 语法的文件必须包含 `from __future__ import annotations`
4. **LLM 并发**：`asyncio.gather` 并行调用 2-3 个 LLM 时，偶发因 rate limit 或网络抖动失败。建议对关键 fallback 增加指数退避重试

---

## 扩展建议

1. **搜索 API 接入**：当前 S4（AI 搜索）和 S6（舆情）完全依赖 LLM 模拟。接入 SerpAPI 或 Bing Search 可大幅提升真实性和数据量。
2. **豆包模型升级**：考虑切换到非思考型豆包模型（如 `doubao-pro-32k`）用于搜索场景，响应时间可从 20 秒降到 3-5 秒。
3. **缓存层**：为豆包搜索结果添加 Redis/SQLite 缓存，同一品牌 24 小时内重复查询直接返回缓存。
4. **权威媒体评估串行化**：当前 S2 的权威媒体评估（`_evaluate_authority_media`）与社交媒体评估并行，偶发超时。建议串行执行或增加更长的超时。

---

*上次更新：2026-07-14*

---

## 2026-07-14 VibeCoding 课程差距评审

### 背景

用户要求将当前项目与 VibeCoding 培训课程（AIGC 产品经理版）进行逐条对比，识别已达成能力与待补齐能力，形成学习地图。评审报告已保存为独立文件。

**评审报告路径**：`VibeCoding-课程差距评审.md`

### 核心结论

| 课程模块 | 达成率 | 状态 |
|---------|--------|------|
| DAY-01：基础原型能力 | 72% | 🟡 部分达成 |
| DAY-02：AI 工具调用与语音全栈 | 32% | 🔴 差距较大 |
| DAY-03：工程化开发与多智能体协同 | 60% | 🟡 部分达成 |
| DAY-04：自主 Agent 与 LangGraph | 8% | 🔴 未开始 |
| **综合** | **43%** | **🟡 中等水平** |

### 最大短板（按优先级排序）

1. **MCP 工具调用**（DAY-02 核心）：当前直接 HTTP 调用 API，未使用 MCP 协议。这是 Agent 时代最核心的产品能力。
2. **LangGraph 编排**（DAY-04 核心）：当前是固定流水线，无 Node/Edge/State 显式定义，Agent 无法自主决策。
3. **LLM LOOP 循环决策**（DAY-02 核心）：无"思考→调用→观察→再思考"循环，流程一旦启动不可调整。
4. **自动化测试**（DAY-03 测试验收）：无 pytest 测试，不符合工程化交付标准。
5. **部署上线**（DAY-01 部署）：仅本地运行，无公网访问能力。

### 已做到可直接复用的能力

- 多智能体并行开发（11 subagent）✅
- 异步流水线编排（asyncio.gather）✅
- API 封装与降级（三端兼容）✅
- JSON 数据修复（中文引号/转义/逗号）✅
- 配置管理（pydantic-settings）✅
- 经验沉淀系统（MEMORY.md）✅

### 建议学习路径

```
Phase 1（本周）：pytest 测试 + FastAPI 包装 + MDC 规范
Phase 2（下周）：MCP 协议学习 + 搜索/豆包 API 封装为 MCP Tool + LLM LOOP
Phase 3（第 3 周）：ChromaDB 向量库 + RAG 链路 + 部署上线
Phase 4（第 4 周）：LangGraph 重构 + 条件边 + 循环决策
```

**总投入**：约 40-50 小时（4 周，每天 2 小时）

### 关键决策记录

- Dify 重构已评估为不可行，暂不执行（记录在 AGENTS.md 中）
- 模板已锁定 refer_1 规范（浅色主题），不再回退
- 用户目标是"参考课程做练习、学习"，评审报告是学习地图
- 项目作为课程实战素材的价值评级：⭐⭐⭐⭐⭐（极高）

---

*上次更新：2026-07-14*

---

## V1.0 版本划定（2026-07-14）

### 决策记录

**用户指令**："先把现有的版本划定为 V1.0，接下来要补齐的计划设计为 V2.0。"

**V1.0 冻结范围**：
- 9 阶段 Python MVP（`main.py` + 9 个 stage 模块 + 2 个工具模块）
- AIVO 评分体系（4 维度 × 25%）
- HTML 可视化报告（refer_1 设计规范）
- JSON 结构化报告 + 自动修复
- 双 LLM 后端（Kimi + 豆包）
- 项目文档（PRD / 实现方案 / README / AGENTS / MEMORY）

**V1.0 冻结后禁止修改**：
- 核心流水线逻辑（main.py 阶段编排）
- AIVO 评分算法
- HTML 报告模板（除非设计规范整体升级）

**V2.0 计划范围**：
| 模块 | 方向 | 课程对应 |
|------|------|---------|
| MCP 工具调用 | 将 API 调用从硬编码改为 MCP 协议 | DAY-02 |
| LangGraph 编排 | 固定流水线 → 自主决策 Agent | DAY-04 |
| 搜索 API 接入 | SerpAPI/Bing 真实搜索数据 | DAY-02 |
| FastAPI 服务 | 本地脚本 → Web API | DAY-01 |
| pytest 测试 | 零覆盖 → 全阶段覆盖 | DAY-03 |
| RAG 向量库 | ChromaDB + Embedding | DAY-03 |

**V2.0 启动条件**：用户明确启动，或完成课程对应模块学习后。

---

*V1.0 已冻结，等待 V2.0 启动指令。*

---

## V1.0 GitHub 发布经验（2026-07-14）

### 背景

用户希望将 V1.0 Python MVP 发布到 GitHub，并同时创建 Kimi Work Skill。过程中遇到多次 Token 权限和仓库名不匹配问题，最终通过创建新 Classic Token 成功推送。

### 发布流程

```
项目清理 → 英文文档撰写 → git 初始化 → Token 权限排查 → 仓库名确认 → 推送成功
```

### 关键踩坑记录

#### Bug 1：Token 权限不足（`403 Permission denied`）

**现象**：首次推送返回 `remote: Permission to ... denied (403)`。

**根因**：用户提供的第一个 Token（`github_pat_...` 开头）是 **Fine-grained PAT**，且该 Token 在 GitHub 账户中已不存在（用户截图显示"No personal access token created"）。

**修复**：在 GitHub → Settings → Developer settings → Personal access tokens → **Tokens (classic)** 中创建新的 **Classic Token**，勾选 `repo` 权限。

**教训**：
- GitHub 现在主推 Fine-grained tokens，但 Classic tokens 对 `git push` 更兼容
- Fine-grained tokens 的权限模型不同，需要单独授权每个仓库
- 如果用户说"已有 Token"但实际账户中没有，说明 Token 来自另一个账号或已过期

#### Bug 2：仓库名不匹配（`Repository not found`）

**现象**：用户提供的仓库 URL 是 `.../geo-visibility-diagnosticia`（拼写有误），但 git remote 配置的是 `.../geo-visibility-diagnostician`（正确拼写）。

**根因**：用户在 GitHub 上创建仓库时拼写错误，实际仓库名是 `geo-visibility-diagnosticia`（少了一个字母 n）。

**修复**：通过 API 查询用户仓库列表失败（Token 权限不足），最终通过尝试两个名称确认正确的仓库名是 `geo-visibility-diagnosticia`。

**教训**：
- 推送前务必确认实际仓库名，不能依赖用户记忆或初始命名
- 可用 `curl https://api.github.com/users/{username}/repos` 查询用户所有公开仓库
- 如果仓库名不确定，可以逐个尝试

#### Bug 3：API Key 残留在 .env 中

**现象**：项目根目录下存在 `.env` 文件，内含真实的 API Key。

**根因**：开发过程中 `.env` 被创建用于本地调试，但未纳入 `.gitignore` 的排除范围（实际上 `.gitignore` 已包含 `.env`，但文件仍存在于工作目录中）。

**修复**：
1. 删除 `.env` 文件
2. 创建 `.env.example` 模板（含注释说明，无真实 Key）
3. 确认 `.gitignore` 中已包含 `.env`

**教训**：
- 发布前必须执行 `rm -rf .env venv/ output/ __pycache__/` 清理敏感/临时文件
- `.env.example` 是标准做法，让其他用户知道需要配置哪些变量
- 检查 `git status` 确认没有意外提交敏感文件

#### Bug 4：Token 硬编码在命令中

**现象**：在 Bash 命令中直接拼接 Token 到 git remote URL，Token 可能出现在日志中。

**根因**：为了方便推送，直接将 Token 嵌入 `https://TOKEN@github.com/...` 格式的 URL 中。

**修复**：使用 Python 封装 git 命令，在输出前过滤替换 Token 为 `***TOKEN***`；推送完成后立即执行 `git remote set-url origin https://github.com/...` 移除 Token。

**教训**：
- Token 绝不应出现在任何日志、输出或命令历史中
- 推送完成后必须立即清理 remote URL 中的 Token
- 最好的做法是通过 git credential helper 或 SSH key 管理凭证

### 发布检查清单

| 检查项 | 命令/方法 | 通过标准 |
|--------|----------|---------|
| 无 .env 文件 | `ls -la` | 不存在 `.env` |
| 无 venv/ 目录 | `ls -la` | 不存在 `venv/` |
| 无 output/ 目录 | `ls -la` | 不存在 `output/` |
| 无 __pycache__/ | `find . -name __pycache__` | 无结果 |
| .env.example 存在 | `cat .env.example` | 有模板，无真实 Key |
| .gitignore 正确 | `cat .gitignore` | 包含 `.env` `venv/` `output/` |
| git remote 无 Token | `git remote -v` | URL 中无 Token 字符串 |
| README 英文版本 | `head README.md` | 英文为主 |
| LICENSE 存在 | `ls LICENSE` | MIT License |
| CHANGELOG 存在 | `ls CHANGELOG.md` | 含 V1.0 冻结说明 |

### GitHub 推送速查

```bash
# 1. 清理项目
rm -rf .env venv/ output/ __pycache__/ .DS_Store

# 2. 创建 .env.example
cat > .env.example << 'EOF'
KIMI_API_KEY=sk-your-key
DOUBAO_API_KEY=ark-your-key
EOF

# 3. 初始化 git（如未初始化）
git init
git add .
git commit -m "v1.0: initial release"

# 4. 设置 remote
git remote add origin https://github.com/USERNAME/REPO.git

# 5. 推送（在 GitHub 网页创建仓库后）
git branch -M main
git push -u origin main
```

### 如果推送失败排查

| 错误信息 | 原因 | 解决 |
|---------|------|------|
| `Repository not found` | 仓库名错误或仓库不存在 | 确认 GitHub 上的实际仓库名 |
| `Permission denied (403)` | Token 无 `repo` 权限 | 创建新的 Classic Token，勾选 `repo` |
| `Authentication failed` | Token 已过期或被撤销 | 去 https://github.com/settings/tokens 生成新 Token |
| `Could not resolve host` | 网络问题 | 检查网络连接，或稍后重试 |

---

*发布日期：2026-07-14 | 仓库：https://github.com/zhongwentuo-creator/geo-visibility-diagnosticia*
