# AGENTS.md — GEO 可见度诊断师

> 本项目 AI Agent 工作指南。供人类开发者和 AI Agent 在维护、扩展本项目时参考。

---

## 1. 项目架构总览

GEO 可见度诊断师采用**分层管道架构（Layered Pipeline Architecture）**，由四个核心层级组成：

```
┌─────────────────────────────────────────────────────────────┐
│                      输入层（Input Layer）                    │
│  品牌名称 + 产品类型 + 官网地址（可选）                        │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│                  诊断引擎层（Engine Layer）                   │
│              8 阶段流水线（Stage 1 → Stage 9）                │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│                  数据能力层（Data Layer）                     │
│  多平台搜索 API │ 竞品识别 │ 舆情抓取 │ 官网检测              │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│                  输出层（Output Layer）                       │
│  JSON 结构化报告 (-diag-report.json)                         │
│  HTML 可视化报告 (-GEO诊断报告.html)                          │
└─────────────────────────────────────────────────────────────┘
```

## 2. 8 阶段流水线

### 2.1 阶段依赖图

```
Stage 1: 用户画像构建
    │
    ├──────────────┐
    ▼              ▼
Stage 2: 基建评估   Stage 3: 竞品分析    【并行】
    │              │
    └──────┬───────┘
           ▼
    Stage 4: AI 搜索测试
           │
    ┌──────┴───────┐
    ▼              ▼
Stage 5: GEO效果汇总 Stage 6: 舆情扫描   【并行】
    │              │
    └──────┬───────┘
           ▼
    Stage 7: 综合总览
           │
    Stage 8: AIVO 评分
           │
    Stage 9: 建议系统
```

### 2.2 各阶段职责

| 阶段 | 文件 | 函数签名 | 耗时 | 外部依赖 |
|------|------|----------|------|----------|
| 1 | `s1_user_profile.py` | `async def build(brand, category) -> dict` | 1-2s | LLM API |
| 2 | `s2_infra_eval.py` | `async def evaluate(brand, website) -> dict` | 3-5s | HTTP 抓取 + LLM |
| 3 | `s3_competitor.py` | `async def identify(brand, category, queries) -> dict` | 5-10s | 搜索 API + LLM |
| 4 | `s4_ai_search.py` | `async def test(brand, queries, competitors, platform) -> dict` | 15-60s | 豆包 Responses API（深度思考模型较慢） |
| 5 | `s5_geo_effect.py` | `def summarize(ai_search_results, competitors) -> dict` | 1-2s | 无（纯计算） |
| 6 | `s6_sentiment.py` | `async def scan(brand) -> dict` | 5-25s | 搜索 API / LLM fallback |
| 5 | `s5_geo_effect.py` | `def summarize(ai_search_results, competitors) -> dict` | 1-2s | 无（纯计算） |
| 6 | `s6_sentiment.py` | `async def scan(brand) -> dict` | 5-8s | 搜索 API |
| 7 | `s7_overview.py` | `def generate(...) -> dict` | 2-3s | 无（纯计算） |
| 8 | `s8_aivo_score.py` | `def calculate(...) -> dict` | 1-2s | 无（纯计算） |
| 9 | `s9_suggestion.py` | `def generate(...) -> dict` | 3-5s | 无（纯计算） |

### 2.3 数据流规范

每个阶段通过**标准字典**传递数据。阶段间接口契约：

1. **只传递，不依赖**：下游阶段只消费上游数据的内容，不依赖上游的具体实现
2. **最小可用**：若上游阶段降级，下游阶段应能基于部分数据继续运行
3. **版本兼容**：数据结构增加字段视为兼容升级

## 3. 核心模块说明

### 3.1 `main.py` — 流水线编排器

**职责**：串联 9 个阶段函数，控制并行策略，管理异常降级，输出最终报告。

**关键设计**：
- 使用 `asyncio.gather` 实现阶段 2&3 并行、阶段 5&6 并行
- 使用 `_StageTimer` 上下文管理器记录每阶段耗时和状态
- 任一阶段异常时捕获并填充降级数据，不打断流水线
- 最终调用 `json_repair.repair_json()` 修复中文引号等问题

### 3.2 `config.py` — 配置中心

**职责**：使用 `pydantic-settings` 从 `.env` 文件加载配置，支持环境变量覆盖。

**配置分组**：
- **AI 平台**：Kimi、豆包、OpenAI 的 API Key / URL / 模型
- **搜索 API**：SerpAPI、Bing、Google Custom Search
- **运行参数**：默认平台、并发数、超时、重试
- **调试参数**：DEBUG 开关、日志级别

### 3.3 `utils/api_client.py` — API 网关

**职责**：封装所有外部 API 调用，统一错误处理、重试、日志。兼容 Kimi（OpenAI 格式）、豆包（Responses API 格式）双后端。

| 函数 | 用途 | 降级策略 | 备注 |
|------|------|----------|------|
| `llm_chat()` | 通用 LLM Chat Completion（Kimi/OpenAI） | 返回空字符串，标记降级 | 自动映射 `gpt-4o` → `moonshot-v1-8k` |
| `doubao_chat()` | 豆包通用对话（Responses API） | 返回空字符串，标记降级 | 不支持 `role: system`，需合并到 user |
| `doubao_search()` | 豆包 AI 搜索（Responses API） | 返回空结果，标记降级 | 深度思考模型约 15-25s/请求 |

**重试策略**：指数退避，最多 2 次；4xx 错误直接降级不重试。豆包深度思考模型超时较长（60s）。

**URL 处理**：`_chat_url(base_url)` 智能检测 base_url 是否已包含 `/chat/completions`，避免重复拼接。

### 3.4 `utils/json_repair.py` — 数据修复器

**职责**：修复多阶段数据合并时的 JSON 格式问题。

**修复范围**：
- 中文引号 `"` `"` → 英文 `"`
- 未转义的换行符 `\n` → `\\n`
- 末尾多余逗号 `,}` → `}`
- 缺失闭合括号 → 自动补全
- 必填字段默认值填充

**调用时机**：`main.py` 最终合并报告后、输出文件前。

### 3.5 `report/template.html` — 报告渲染器

**职责**：Jinja2 模板，将 JSON 数据转化为可视化 HTML 报告。

**设计约束**：
- 全部 CSS 内嵌，无外部依赖
- 纯 CSS/SVG 图表（圆环图、条形图、饼图、时间轴）
- 响应式布局（768px-1920px）
- 文件大小控制在 500KB 以内

## 4. 数据实体规范

### 4.1 最终报告结构

```python
{
  "meta": {
    "diagnosisId": str,       # GEO-YYYYMMDD-HHMMSS
    "brandName": str,
    "productType": str,
    "officialWebsite": str | None,
    "platform": str,          # doubao / chatgpt / perplexity
    "diagnosisDate": str,     # ISO 8601
    "version": str,           # "1.0.0"
    "debug": bool
  },
  # 各阶段输出（顶层平铺，非嵌套）
  "userProfile": dict,      # Stage 1 输出 + _stageMeta
  "infrastructure": dict,   # Stage 2 输出 + _stageMeta
  "competitorAnalysis": dict, # Stage 3 输出 + _stageMeta
  "competitors": list,      # 竞品列表（扁平数组）
  "aiSearch": dict,         # Stage 4 输出 + _stageMeta
  "geoEffect": dict,        # Stage 5 输出 + _stageMeta
  "sentiment": dict,        # Stage 6 输出 + _stageMeta
  "overview": dict,         # Stage 7 输出 + _stageMeta
  "aivoScore": dict,        # Stage 8 输出 + _stageMeta
  "suggestions": dict,      # Stage 9 输出 + _stageMeta
  "jsonRepairApplied": bool   # 是否触发了 JSON 修复（快速路径已避免过度修复）
}
```

### 4.2 AIVO 评分结构

```python
{
  "total": int,               # 0-100
  "grade": str,               # "优秀"/"良好"/"中等"/"较差"/"差"
  "dimensions": [
    {
      "code": str,            # AI_SEARCH_VISIBILITY / INFRA_COMPLETENESS / COMPETITIVE_ADVANTAGE / SENTIMENT_HEALTH
      "name": str,
      "score": int,           # 0-100
      "weight": float,        # 0.25
      "weightedScore": float  # score * weight
    }
  ],
  "nextTierGap": int,         # 距下一等级差多少分
  "nextTierTarget": str       # 下一等级名称
}
```

## 5. 扩展指南

### 5.1 新增诊断平台

1. 在 `config.py` 中添加平台配置（API URL、模型名）
2. 在 `utils/api_client.py` 中添加平台搜索函数
3. 在 `s4_ai_search.py` 中添加平台路由逻辑
4. 在 `main.py` 的 `--platform` 参数中添加新选项

### 5.2 新增评分维度

1. 在 `s8_aivo_score.py` 中添加新维度计算逻辑
2. 调整权重分配（保持总和为 1.0）
3. 在 `report/template.html` 中添加新维度展示
4. 更新 PRD 文档

### 5.3 新增舆情数据源

1. 在 `s6_sentiment.py` 中添加新数据源的抓取函数
2. 调整数据源权重分配
3. 在平台推断函数中添加新域名识别

## 6. 调试技巧

### 6.1 单阶段调试

```python
# 直接运行单个阶段
import asyncio
from stages.s4_ai_search import test

result = asyncio.run(test(
    brand="听力熊",
    queries=[{"text": "儿童AI学习机推荐"}],
    competitors=[{"name": "小度"}],
    platform="doubao"
))
print(result)
```

### 6.2 查看阶段日志

```bash
# 启用 DEBUG 模式
DEBUG=true python main.py --brand "听力熊" --category "儿童AI对话智能体"
```

### 6.3 验证 JSON 输出

```bash
# 使用 jq 格式化查看
jq . output/*/听力熊_豆包_*-diag-report.json | less
```

## 7. 已知问题与待办

| 问题 | 状态 | 优先级 | 备注 |
|------|------|--------|------|
| s5_geo_effect.py 竞品字段名不一致（`brandName` vs `name`） | ✅ 已修复 | — | |
| Python 3.9 兼容性（`from __future__ import annotations`） | ✅ 已修复 | — | `s2_infra_eval.py` 已添加 |
| `.env` 被系统旧 Key 覆盖（`load_dotenv override=False`） | ✅ 已修复 | — | 改为 `override=True` |
| API Key 命名不匹配（`KIMI_API_KEY` vs `OPENAI_API_KEY`） | ✅ 已修复 | — | `api_client.py` 已兼容两者 |
| URL 重复拼接（`/chat/completions/chat/completions`） | ✅ 已修复 | — | 新增 `_chat_url()` 去重 |
| 模型名 `gpt-4o` 不被 Kimi 支持 | ✅ 已修复 | — | 新增 `_resolve_model()` 自动映射 |
| 豆包 API 端点错误（Chat Completions vs Responses） | ✅ 已修复 | — | 改用 Responses API + `_parse_doubao_response()` |
| 豆包不支持 `role: system` | ✅ 已修复 | — | System prompt 合并到 user message |
| `doubao-seed-evolving` 深度思考模型超时（96s） | ✅ 已修复 | — | 超时 60s + prompt 限制思考长度 |
| 权威媒体评估 LLM 并发偶发失败 | ⚠️ 已知 | 低 | 不影响总分，可串行化优化 |
| 舆情抓取依赖外部搜索 API，免费额度有限 | ⚠️ 已知 | 中 | 当前使用 LLM fallback 替代 |
| HTML 报告在移动端体验待优化 | ⚠️ 已知 | 低 | |
| 竞品 AIVO 分数为估算值，非真实测试 | ⚠️ 已知 | 中 | |

## 8. 相关文档

- `README.md` — 用户指南（快速开始、使用示例）
- `MEMORY.md` — 项目记忆（踩坑记录、联调经验、配置规范）⭐ **维护前必读**
- `GEO可见度诊断师-Agent-PRD.md` — 产品需求文档
- `GEO可见度诊断师-VibeCoding-实现方案.md` — 实现方案文档

- `README.md` — 用户指南（快速开始、使用示例）
- `GEO可见度诊断师-Agent-PRD.md` — 产品需求文档
- `GEO可见度诊断师-VibeCoding-实现方案.md` — 实现方案文档

---

*本文档供 AI Agent 和人类开发者共同维护。修改前请确保与 PRD 保持一致。*
