# GEO 可见度诊断师 V1.0

> 帮助品牌量化自己在 AI 原生时代的"数字存在感"，并提供可执行的优化路径。
> 
> **版本**：V1.0（已冻结） | **状态**：Python MVP 已联调 | **V2.0 方向**：MCP + LangGraph

[English Version](README.md) | [VibeCoding 课程差距评审](docs/COURSE_GAP_ANALYSIS.md)

---

## 什么是 GEO？

**GEO** = **G**enerative **E**ngine **O**ptimization（生成式引擎优化），是 SEO 在 AI 原生时代的进化形态。

SEO 优化搜索引擎排名，而 GEO 优化**品牌在 AI 平台中的被引用率和推荐权重**。

| 维度 | SEO（搜索引擎优化） | GEO（生成式引擎优化） |
|------|---------------------|----------------------|
| **优化目标** | 网页在搜索结果中的排名 | 品牌信息在 AI 回答中的被引用率与推荐权重 |
| **评估场景** | 关键词排名、流量、点击率 | AI 是否主动提及品牌、如何描述品牌、竞品对比中的位置 |
| **内容形态** | 网页内容、Meta 标签 | 结构化数据、权威媒体背书、用户口碑、百科卡片 |
| **竞争维度** | 与网页竞争排名 | 与品牌在 AI 训练数据中的"认知密度"竞争 |

> **Why 现在**：随着 ChatGPT、豆包、Perplexity 等 AI 搜索平台日活突破亿级，用户获取品牌信息的首选路径正从"搜索→点击网页"转变为"直接提问→获取 AI 总结答案"。品牌若未能在 AI 回答中被准确引用，等同于在下一个时代的"搜索结果首页"中消失。

---

## 功能特性

- **9 阶段诊断流水线**：用户画像 → 基建评估 → 竞品分析 → AI 搜索测试 → GEO 效果汇总 → 舆情扫描 → 综合总览 → AIVO 评分 → 建议系统
- **AIVO 评分体系**：4 维度（AI 搜索可见度 / 基建完善度 / 竞品对比优势 / 舆情健康度）× 25% 权重，0-100 分量化评估
- **竞品自动对标**：自动识别 3-5 家同行业竞品，同步执行相同条件测试
- **双轨交付**：JSON 结构化数据（可接入 BI）+ HTML 可视化报告（可直接汇报）
- **可执行建议**：优先级行动清单 + Quick Wins + 三阶段路线图（P1 即时 / P2 短期 / P3 长期）

---

## 快速开始

### 1. 克隆项目

```bash
git clone https://github.com/YOUR_USERNAME/geo-visibility-diagnostician.git
cd geo-visibility-diagnostician
```

### 2. 创建虚拟环境

```bash
python -m venv venv
source venv/bin/activate  # macOS/Linux
# venv\Scripts\activate   # Windows
```

### 3. 安装依赖

```bash
pip install -r requirements.txt
```

### 4. 配置 API Key

```bash
cp .env.example .env
# 编辑 .env，填入你的 API Key
```

**必需配置：**
- `KIMI_API_KEY`：用于 LLM 推理（阶段 1/3/7/9）
- `DOUBAO_API_KEY`：用于 AI 搜索测试（阶段 4）

**可选配置：**
- `SERPAPI_KEY` / `BING_SEARCH_KEY`：用于舆情抓取（阶段 6）
- `OPENAI_API_KEY`：备选 LLM

### 5. 运行诊断

```bash
python main.py --brand "听力熊" --category "儿童AI对话智能体" --platform doubao
```

| 参数 | 必填 | 说明 |
|------|------|------|
| `--brand` | 是 | 品牌名称 |
| `--category` | 是 | 产品类型 |
| `--website` | 否 | 官网地址（可提升基建评估精度） |
| `--platform` | 否 | 诊断平台（默认 doubao，可选 chatgpt / perplexity） |

### 6. 查看报告

```bash
open output/*/听力熊_doubao_*-GEO诊断报告.html  # macOS
start output/*/听力熊_doubao_*-GEO诊断报告.html  # Windows
```

---

## 项目结构

```
geo-visibility-diagnostician/
├── main.py                  # 诊断入口（9 阶段流水线编排）
├── config.py                # 配置管理（pydantic-settings + .env）
├── requirements.txt         # Python 依赖
├── .env.example             # 环境变量模板（无敏感信息）
├── .gitignore               # Git 忽略规则
├── stages/                  # 9 阶段诊断流水线
│   ├── s1_user_profile.py   # 阶段 1：用户画像构建
│   ├── s2_infra_eval.py     # 阶段 2：基建评估
│   ├── s3_competitor.py     # 阶段 3：竞品分析
│   ├── s4_ai_search.py      # 阶段 4：AI 搜索测试
│   ├── s5_geo_effect.py     # 阶段 5：GEO 效果汇总
│   ├── s6_sentiment.py      # 阶段 6：舆情扫描
│   ├── s7_overview.py       # 阶段 7：综合总览
│   ├── s8_aivo_score.py     # 阶段 8：AIVO 评分
│   └── s9_suggestion.py     # 阶段 9：建议系统
├── utils/                   # 工具模块
│   ├── api_client.py        # API 网关（Kimi + 豆包 + OpenAI 兼容）
│   └── json_repair.py       # JSON 修复工具（中文引号/转义/末尾逗号）
├── report/                  # 报告模板
│   └── template.html        # Jinja2 HTML 可视化报告（CSS/SVG 内嵌）
├── output/                  # 自动创建输出目录
│   ├── {品牌}_{平台}_diag-report.json
│   └── {品牌}_{平台}_GEO诊断报告.html
├── docs/                    # 文档
│   ├── PRD.md               # 产品需求文档（中文版）
│   ├── IMPLEMENTATION.md    # Vibe Coding 实现方案（中文版）
│   └── COURSE_GAP_ANALYSIS.md # VibeCoding 课程差距评审（中文版）
├── AGENTS.md                # AI Agent 工作指南
├── MEMORY.md                # 项目记忆（Bug 修复、调优记录）
└── README.md                # 英文版 README
```

---

## AIVO 评分体系

**AIVO** = **AI** **V**isibility & **O**ptimization（AI 可见度与优化）

| 维度 | 权重 | 代码标识 | 数据来源 | 说明 |
|------|------|----------|----------|------|
| AI 搜索可见度 | 25% | `AI_SEARCH_VISIBILITY` | 阶段 4 | 品牌在典型用户问题中被 AI 平台提及的比率 |
| 基建完善度 | 25% | `INFRA_COMPLETENESS` | 阶段 2 | 官网质量、自媒体矩阵、权威媒体覆盖的完整程度 |
| 竞品对比优势 | 25% | `COMPETITIVE_ADVANTAGE` | 阶段 3 + 5 | 与 3-5 家自动识别竞品在相同问题下的相对表现 |
| 舆情健康度 | 25% | `SENTIMENT_HEALTH` | 阶段 6 | 负面率、风险等级、情感分布 |

| 等级 | 分数区间 | 颜色 | 说明 |
|------|----------|------|------|
| 优秀 | 90-100 | 🟢 | GEO 领导者 |
| 良好 | 80-89 | 🟢 | GEO 先进者 |
| 中等 | 70-79 | 🟡 | GEO 跟随者 |
| 较差 | 60-69 | 🟠 | GEO 滞后者 |
| 差 | 0-59 | 🔴 | GEO 缺失者 |

---

## 9 阶段流水线

```
阶段 1: 用户画像构建  ──→ 阶段 2: 基建评估 ─┐
                           阶段 3: 竞品分析 ──┤ 并行
                                           ↓
                           阶段 4: AI 搜索测试
                                           ↓
阶段 5: GEO 效果汇总 ──┐                   │
阶段 6: 舆情扫描     ──┤ 并行            │
                       ↓                   │
              阶段 7: 综合总览          │
                       ↓                   │
              阶段 8: AIVO 评分         │
                       ↓                   │
              阶段 9: 建议系统 ←──────────┘
```

**总耗时**：单平台约 60-120 秒（豆包深度思考模型 `doubao-seed-evolving` 每次搜索约 15-25 秒）

---

## 技术栈

| 组件 | 选型 | 说明 |
|------|------|------|
| 语言 | Python 3.9+ | 异步流水线（asyncio），使用 `from __future__ import annotations` 兼容 3.9 |
| HTTP 客户端 | httpx | 异步 HTTP 请求，兼容 Kimi / 豆包 / OpenAI |
| HTML 模板 | jinja2 | 报告渲染，纯 CSS/SVG 内嵌（无外部 JS） |
| 数据解析 | BeautifulSoup4 | 官网结构分析 |
| 配置管理 | pydantic-settings | `.env` 文件加载，支持环境变量覆盖 |
| AI 搜索调用 | 豆包 Responses API + Kimi Chat Completions API | 豆包 Seed 系列（深度思考模型），Kimi moonshot-v1 系列 |

---

## 异常处理与降级

| 异常场景 | 阶段 | 降级策略 | 输出标记 |
|----------|------|----------|----------|
| AI 搜索 API 超时 | 阶段 4 | 使用缓存数据或模拟数据，标记"数据时效性受限" | `dataQuality: "degraded"` |
| 竞品识别失败 | 阶段 3 | 使用品类默认竞品库（Top 3 品牌），标记"竞品为默认推荐" | `competitorSource: "default"` |
| 舆情平台无法访问 | 阶段 6 | 该维度标记为"数据缺失"，评分用品类均值替代 | `sentimentStatus: "unavailable"` |
| 官网无法访问 | 阶段 2 | 官网子项得 0 分，基建评分基于其他维度 | `websiteStatus: "inaccessible"` |
| JSON 生成错误 | 输出阶段 | 调用 JSON 修复工具，最多重试 3 次 | `jsonRepairApplied: true` |

---

## 常见问题

**Q: 为什么诊断结果是"较差"（57分）？**

A: AIVO 评分是 4 维度平均值。如果品牌在某个维度得分很低（如基建 55 分），即使其他维度尚可，总分也会被拉低。查看 HTML 报告，可以看到具体短板和优化建议。

**Q: 可以诊断英文品牌吗？**

A: 可以，但目前优先支持中文品牌。如需诊断国际品牌，建议切换 `--platform` 为 `chatgpt` 或 `perplexity`。

**Q: 报告中的竞品是怎么选出来的？**

A: 系统通过三层策略自动识别：① LLM 语义分析 ② 搜索 API 共现分析 ③ 品类默认库兜底。你可以在 HTML 报告中看到每一家竞品的选择理由。

**Q: 需要付费 API 吗？**

A: 核心功能（LLM 推理 + 搜索测试）需要 API Key。Kimi 和豆包都有免费额度，足以支持日常诊断。

---

## V2.0 演进路线

| 阶段 | 功能 | 课程映射 | 优先级 |
|------|------|----------|--------|
| Phase 1 | MCP 工具集成 | VibeCoding DAY-02 | 🔴 P0 |
| Phase 2 | LangGraph 自主 Agent | VibeCoding DAY-04 | 🔴 P0 |
| Phase 3 | 真实搜索 API（SerpAPI） | VibeCoding DAY-02 | 🟡 P1 |
| Phase 4 | FastAPI Web 服务 | VibeCoding DAY-01 | 🟡 P1 |
| Phase 5 | pytest 自动化测试 | VibeCoding DAY-03 | 🟡 P1 |
| Phase 6 | RAG 向量数据库 | VibeCoding DAY-03 | 🟢 P2 |

**V2.0 核心目标**：从"固定流水线脚本"进化为"自主决策 Agent"，具备 MCP 工具调用、LangGraph 编排、条件边循环决策能力。

---

## 许可证

[MIT License](LICENSE)

## 贡献

详见 [CONTRIBUTING.md](CONTRIBUTING.md)

## 致谢

本项目从 WorkBuddy "GEO 可见度诊断" Agent 的运行记录反推而来，感谢原始 Agent 的设计者。

使用 Vibe Coding 构建 — 11 个 subagent、9 个阶段、10 个 Bug 修复、首次测试 AIVO 得分 74/100。
