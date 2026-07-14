# GEO 可见度诊断师 — Vibe Coding 实现方案

**文档版本**：V1.0  
**创建日期**：2026-07-13  
**V1.0 冻结日期**：2026-07-14  
**文档状态**：✅ 已联调 / 已冻结  
**对应 PRD**：`GEO可见度诊断师-Agent-PRD.md`  

---

## 目录

1. [方案总览](#1-方案总览)
2. [方案 A：Python 脚本 MVP（推荐首选）](#2-方案-a-python-脚本-mvp推荐首选)
3. [方案 B：Dify / WorkBuddy 工作流](#3-方案-b-dify--workbuddy-工作流)
4. [方案 C：Next.js 全栈 SaaS](#4-方案-c-nextjs-全栈-saas)
5. [渐进式实施路线图](#5-渐进式实施路线图)
6. [Vibe Coding 操作手册](#6-vibe-coding-操作手册)
7. [风险与对策](#7-风险与对策)

---

## 1. 方案总览

### 1.1 为什么这个 Agent 高度适配 Vibe Coding？

| 产品特性 | Vibe Coding 适配性 | 说明 |
|----------|-------------------|------|
| **数据流驱动** | ✅ 极高 | 8 阶段流水线本质是数据转换管道，可完全用自然语言描述 |
| **结构固定** | ✅ 极高 | 输入输出规范清晰（3 要素入参 → JSON/HTML 双轨出参） |
| **无复杂 UI** | ✅ 极高 | 最终产物是报告文件，无需交互界面开发 |
| **外部 API 编排** | ⚠️ 中等 | 搜索 API、舆情抓取需要工程处理，但有现成库可用 |
| **JSON 合并风险** | ⚠️ 需注意 | 多阶段并行时中文引号、转义字符易出错（PRD 中已记录） |

### 1.2 三种方案对比

| 维度 | 方案 A：Python MVP | 方案 B：Dify 工作流 | 方案 C：Next.js SaaS |
|------|-------------------|-------------------|-------------------|
| **实现时间** | 2-4 小时 | 1-2 天 | 3-5 天 |
| **技术门槛** | 低（会 Python 即可） | 极低（无代码/低代码） | 中（需全栈基础） |
| **运行方式** | 本地脚本 / 命令行 | WorkBuddy / Dify 平台 | 部署为 Web 服务 |
| **可分享性** | 需手动发送文件 | 平台内直接对话 | 链接分享，多用户可用 |
| **历史记录** | 本地文件管理 | 平台自动保存 | 数据库存储 |
| **扩展性** | 有限 | 中等 | 高 |
| **推荐阶段** | **首选验证** | **产品化** | **商业化** |

### 1.4 V1.0 实际实现状态

> **V1.0 已于 2026-07-14 冻结**，9 阶段 Python MVP 经 9 Bug 联调修复后已可稳定运行。

| 指标 | 状态 |
|------|------|
| **9 阶段流水线** | ✅ 全部实现并联调通过 |
| **AIVO 评分** | ✅ 4 维度 × 25% 权重，实测 74/100 |
| **HTML 报告** | ✅ 已按 refer_1 设计规范重写（浅色主题） |
| **JSON 修复** | ✅ 中文引号/转义/末尾逗号自动修复 |
| **API 客户端** | ✅ Kimi + 豆包 + OpenAI 三端兼容 |
| **多平台支持** | ⚠️ 仅豆包（ChatGPT/Perplexity 待接入） |
| **搜索 API** | ❌ 未接入（SerpAPI/Bing 待接入） |
| **部署** | ❌ 仅本地脚本 |
| **测试** | ❌ 零测试覆盖 |

**V1.0 已知问题**：详见 `MEMORY.md` 中 10 个 Bug 修复记录，以及 `API诊断报告.md`。

### 1.3 核心结论

> **推荐路径：方案 A（Python MVP）→ 方案 B（Dify 工作流）→ 方案 C（Next.js SaaS）**

先用 Python 脚本在 2-4 小时内验证核心逻辑和数据流，确认算法正确后，再迁移到 Dify 工作流实现产品化，最终需要多用户支持时再升级为 Next.js 全栈。

---

## 2. 方案 A：Python 脚本 MVP（推荐首选）

### 2.1 技术栈

| 组件 | 选型 | 用途 |
|------|------|------|
| **语言** | Python 3.10+ | 主程序 |
| **HTTP 请求** | `httpx` / `aiohttp` | 异步 API 调用（豆包、搜索、抓取） |
| **HTML 生成** | `jinja2` | HTML 报告模板渲染 |
| **数据解析** | `BeautifulSoup4` | 官网结构分析、舆情内容抓取 |
| **JSON 处理** | 标准库 `json` | 阶段数据传递、最终合并 |
| **配置文件** | `.env` + `pydantic-settings` | API Key、平台参数管理 |

### 2.2 项目结构

```
geo-diagnosis/
├── main.py                  # 诊断入口（8 阶段编排）
├── config.py                # 配置管理（API Key、平台参数）
├── stages/
│   ├── __init__.py
│   ├── s1_user_profile.py   # 阶段 1：用户画像构建
│   ├── s2_infra_eval.py     # 阶段 2：基建评估
│   ├── s3_competitor.py     # 阶段 3：竞品分析
│   ├── s4_ai_search.py      # 阶段 4：AI 搜索测试
│   ├── s5_geo_effect.py     # 阶段 5：GEO 效果汇总
│   ├── s6_sentiment.py      # 阶段 6：舆情扫描
│   ├── s7_overview.py       # 阶段 7：综合总览
│   ├── s8_aivo_score.py     # 阶段 8：AIVO 评分
│   └── s9_suggestion.py     # 阶段 9：建议系统
├── report/
│   ├── template.html        # Jinja2 HTML 模板
│   └── styles.css           # 内嵌样式（最终合并到 HTML）
├── utils/
│   ├── json_repair.py       # JSON 修复工具（关键！）
│   ├── api_client.py        # API 调用封装
│   └── logger.py            # 阶段日志记录
├── output/                  # 输出目录（自动创建）
│   ├── {brand}-diag-report.json
│   └── {brand}-GEO诊断报告.html
├── .env                     # API Key 等敏感配置（不提交 Git）
└── requirements.txt
```

### 2.3 核心代码骨架

#### `main.py` — 诊断入口

```python
#!/usr/bin/env python3
"""
GEO 可见度诊断师 — 主入口
用法: python main.py --brand 听力熊 --category "儿童AI对话智能体" --platform doubao
"""

import asyncio
import json
import argparse
from datetime import datetime
from pathlib import Path

from config import Settings
from stages import (
    s1_user_profile,
    s2_infra_eval,
    s3_competitor,
    s4_ai_search,
    s5_geo_effect,
    s6_sentiment,
    s7_overview,
    s8_aivo_score,
    s9_suggestion,
)
from utils.json_repair import repair_json
from utils.logger import stage_logger

settings = Settings()


async def diagnose(brand: str, category: str, website: str | None = None, platform: str = "doubao") -> dict:
    """8 阶段流水线 — GEO 可见度诊断主函数"""
    
    diagnosis_id = f"GEO-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    output_dir = Path("output") / diagnosis_id
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # --- 阶段 1：用户画像构建 ---
    with stage_logger("Stage 1: USER_PROFILE"):
        user_profile = await s1_user_profile.build(brand, category)
    
    # --- 阶段 2 & 3：基建评估 + 竞品分析（并行） ---
    with stage_logger("Stage 2&3: INFRA_EVAL + COMPETITOR"):
        infra_eval, competitors = await asyncio.gather(
            s2_infra_eval.evaluate(brand, website),
            s3_competitor.identify(brand, category, user_profile["queries"])
        )
    
    # --- 阶段 4：AI 搜索测试 ---
    with stage_logger("Stage 4: AI_SEARCH"):
        ai_search_results = await s4_ai_search.test(
            brand=brand,
            queries=user_profile["queries"],
            competitors=competitors,
            platform=platform
        )
    
    # --- 阶段 5：GEO 效果汇总 ---
    with stage_logger("Stage 5: GEO_EFFECT"):
        geo_effect = s5_geo_effect.summarize(ai_search_results, competitors)
    
    # --- 阶段 6：舆情扫描（可与阶段 5 并行，但数据量小，串行更简单） ---
    with stage_logger("Stage 6: SENTIMENT"):
        sentiment = await s6_sentiment.scan(brand)
    
    # --- 阶段 7：综合总览 ---
    with stage_logger("Stage 7: OVERVIEW"):
        overview = s7_overview.generate(user_profile, infra_eval, geo_effect, sentiment)
    
    # --- 阶段 8：AIVO 评分 ---
    with stage_logger("Stage 8: AIVO_SCORE"):
        aivo_score = s8_aivo_score.calculate(infra_eval, ai_search_results, competitors, sentiment)
    
    # --- 阶段 9：建议系统 ---
    with stage_logger("Stage 9: SUGGESTION"):
        suggestions = s9_suggestion.generate(aivo_score, infra_eval, sentiment)
    
    # --- 合并最终报告 ---
    report = {
        "meta": {
            "diagnosisId": diagnosis_id,
            "brandName": brand,
            "productType": category,
            "officialWebsite": website,
            "platform": platform,
            "generatedAt": datetime.now().isoformat(),
            "version": "1.0.0"
        },
        "stages": {
            "userProfile": user_profile,
            "infraEval": infra_eval,
            "competitor": competitors,
            "aiSearch": ai_search_results,
            "geoEffect": geo_effect,
            "sentiment": sentiment,
            "overview": overview,
            "aivoScore": aivo_score,
            "suggestion": suggestions
        }
    }
    
    # JSON 修复（关键！处理中文引号、转义问题）
    report = repair_json(report)
    
    # 输出 JSON
    json_path = output_dir / f"{brand}-diag-report.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    # 生成 HTML 报告
    html_path = output_dir / f"{brand}-GEO诊断报告.html"
    await generate_html_report(report, html_path)
    
    return {
        "report": report,
        "jsonPath": str(json_path),
        "htmlPath": str(html_path)
    }


async def generate_html_report(report: dict, output_path: Path):
    """基于 Jinja2 模板生成 HTML 报告"""
    from jinja2 import Environment, FileSystemLoader
    
    env = Environment(loader=FileSystemLoader("report"))
    template = env.get_template("template.html")
    
    html_content = template.render(report=report)
    
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html_content)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="GEO 可见度诊断师")
    parser.add_argument("--brand", required=True, help="品牌名称")
    parser.add_argument("--category", required=True, help="产品类型")
    parser.add_argument("--website", default=None, help="官网地址（可选）")
    parser.add_argument("--platform", default="doubao", choices=["doubao", "chatgpt", "perplexity"], help="诊断平台")
    
    args = parser.parse_args()
    
    result = asyncio.run(diagnose(args.brand, args.category, args.website, args.platform))
    
    print(f"\n✅ 诊断完成！")
    print(f"   JSON 数据: {result['jsonPath']}")
    print(f"   HTML 报告: {result['htmlPath']}")
    print(f"   AIVO 总分: {result['report']['stages']['aivoScore']['total']} / 100")
```

#### `stages/s1_user_profile.py` — 阶段 1 示例

```python
"""阶段 1：用户画像构建 — 用 LLM 生成典型搜索问题"""

import json
from utils.api_client import llm_chat


async def build(brand: str, category: str) -> dict:
    """
    基于品牌名和品类，生成 3 个用户画像 × 每组 5-6 个搜索问题
    
    Vibe Coding 提示词：
    "你是一个市场研究员。给定品牌'听力熊'和产品类型'儿童AI对话智能体'，
     请识别 3 类核心目标用户，并为每类用户生成 5 个他们可能在 AI 搜索平台（如豆包）
     上询问的真实问题。输出 JSON 格式。"
    """
    
    prompt = f"""
你是一个专业的市场研究分析师。请基于以下品牌信息，生成用户画像和搜索意图分析。

品牌名称：{brand}
产品类型：{category}

请完成以下任务：
1. 识别 3 类核心目标用户群体（每类需包含：用户身份、核心诉求、典型使用场景）
2. 为每类用户生成 5 个他们可能在 AI 搜索平台（豆包/ChatGPT）上询问的真实问题
3. 问题需覆盖：信息型（"哪个好"）、对比型（"A和B哪个好"）、交易型（"值得买吗"）

输出严格 JSON 格式：
{{
  "segments": [
    {{
      "id": "UP001",
      "label": "用户群体名称",
      "description": "用户特征描述",
      "painPoints": ["痛点1", "痛点2"],
      "queries": [
        {{
          "text": "具体搜索问题",
          "intent": "信息型/对比型/交易型",
          "expectedAnswer": "用户期望得到的回答类型"
        }}
      ]
    }}
  ],
  "totalQueries": 15
}}
"""
    
    response = await llm_chat(prompt, model="gpt-4o", response_format="json")
    data = json.loads(response)
    
    # 校验：确保每个用户组有 5 个问题
    for segment in data["segments"]:
        assert len(segment["queries"]) >= 5, f"用户组 {segment['label']} 问题不足 5 个"
    
    return data
```

#### `stages/s4_ai_search.py` — 阶段 4 核心

```python
"""阶段 4：AI 搜索场景测试 — 在目标平台执行真实搜索"""

import asyncio
from typing import List, Dict
from utils.api_client import doubao_search  # 封装豆包 API


async def test(brand: str, queries: List[Dict], competitors: List[Dict], platform: str) -> Dict:
    """
    对每个问题执行 AI 搜索，记录品牌提及情况
    
    Vibe Coding 提示词：
    "写一个异步函数，接收一组搜索问题，调用豆包 API 逐个搜索，
     检查返回结果中是否包含品牌名，记录提及位置和语境"
    """
    
    results = []
    
    # 使用 asyncio.gather 并行搜索（控制并发数避免限流）
    semaphore = asyncio.Semaphore(3)  # 最多同时 3 个请求
    
    async def search_one(query: Dict) -> Dict:
        async with semaphore:
            query_text = query["text"]
            
            # 调用豆包 API 搜索
            response = await doubao_search(query_text)
            answer_text = response["answer"]
            
            # 分析提及情况
            mentioned = brand in answer_text
            position = _detect_position(answer_text, brand)
            sentiment = _detect_sentiment(answer_text, brand)
            competitors_mentioned = [c["name"] for c in competitors if c["name"] in answer_text]
            
            return {
                "query": query_text,
                "intent": query["intent"],
                "mentioned": mentioned,
                "position": position,  # "first_paragraph" / "body" / "not_mentioned"
                "sentiment": sentiment,  # "positive" / "neutral" / "negative"
                "competitorsMentioned": competitors_mentioned,
                "answerSnippet": answer_text[:300]  # 前 300 字摘要
            }
    
    # 并行执行所有搜索
    results = await asyncio.gather(*[search_one(q) for q in queries])
    
    # 计算汇总指标
    total = len(results)
    mentioned_count = sum(1 for r in results if r["mentioned"])
    first_para_count = sum(1 for r in results if r["position"] == "first_paragraph")
    
    return {
        "platform": platform,
        "totalQueries": total,
        "mentioned": mentioned_count,
        "mentionRate": round(mentioned_count / total * 100, 1),
        "firstParagraphMentions": first_para_count,
        "firstParagraphRate": round(first_para_count / total * 100, 1),
        "results": results
    }


def _detect_position(answer: str, brand: str) -> str:
    """检测品牌在回答中的位置"""
    # 简单实现：前 200 字为"首段"
    first_paragraph_end = answer.find("\n\n")
    if first_paragraph_end == -1:
        first_paragraph_end = min(200, len(answer))
    
    first_para = answer[:first_paragraph_end]
    if brand in first_para:
        return "first_paragraph"
    elif brand in answer:
        return "body"
    else:
        return "not_mentioned"


def _detect_sentiment(answer: str, brand: str) -> str:
    """检测品牌提及的语境情感（简化版，可用 NLP 库增强）"""
    # 获取品牌词前后 50 字上下文
    idx = answer.find(brand)
    if idx == -1:
        return "not_mentioned"
    
    context = answer[max(0, idx-50):min(len(answer), idx+50)]
    
    # 简单关键词匹配（实际可用 sentiment analysis 库）
    positive_words = ["推荐", "好", "优秀", "值得", "领先", "首选"]
    negative_words = ["不推荐", "差", "问题", "投诉", "缺点", "不建议"]
    
    pos_count = sum(1 for w in positive_words if w in context)
    neg_count = sum(1 for w in negative_words if w in context)
    
    if neg_count > pos_count:
        return "negative"
    elif pos_count > neg_count:
        return "positive"
    else:
        return "neutral"
```

#### `utils/json_repair.py` — JSON 修复（关键！）

```python
"""
JSON 修复工具 — 处理多阶段数据合并时的常见错误

这是 WorkBuddy 运行记录中实际遇到的问题：
"JSON解析出错，第69行中文双引号 `随身智能体` 破坏了JSON"
"""

import json
import re


def repair_json(data: dict) -> dict:
    """
    修复 JSON 数据中的常见问题：
    1. 中文引号 " " 替换为英文引号 "
    2. 未转义的特殊字符
    3. 末尾多余逗号
    4. 缺失的闭合括号
    """
    # 先序列化为字符串，再修复
    json_str = json.dumps(data, ensure_ascii=False, indent=2)
    
    # 修复中文引号（常见来源：LLM 生成的内容中包含中文引号）
    json_str = json_str.replace('"', '"').replace('"', '"')
    
    # 修复未转义的换行符（LLM 输出中常见）
    json_str = _escape_newlines_in_strings(json_str)
    
    # 修复末尾多余逗号
    json_str = re.sub(r',(\s*[}\]])', r'\1', json_str)
    
    # 重新解析验证
    try:
        return json.loads(json_str)
    except json.JSONDecodeError as e:
        # 如果仍失败，尝试更激进的修复
        json_str = _aggressive_repair(json_str)
        return json.loads(json_str)


def _escape_newlines_in_strings(json_str: str) -> str:
    """在 JSON 字符串值中转义未处理的换行符"""
    # 匹配字符串值中的原始换行符（不在转义状态）
    # 这是一个简化实现，实际可用更精确的解析
    result = []
    in_string = False
    i = 0
    
    while i < len(json_str):
        char = json_str[i]
        
        if char == '"' and (i == 0 or json_str[i-1] != '\\'):
            in_string = not in_string
        
        if in_string and char == '\n':
            result.append('\\n')
        else:
            result.append(char)
        
        i += 1
    
    return ''.join(result)


def _aggressive_repair(json_str: str) -> str:
    """激进修复：尝试补全缺失的括号"""
    open_braces = json_str.count('{') - json_str.count('}')
    open_brackets = json_str.count('[') - json_str.count(']')
    
    for _ in range(open_braces):
        json_str += '}'
    for _ in range(open_brackets):
        json_str += ']'
    
    return json_str
```

### 2.4 Vibe Coding 执行步骤（按顺序）

```bash
# Step 1: 创建项目目录
mkdir geo-diagnosis && cd geo-diagnosis
python -m venv venv && source venv/bin/activate

# Step 2: 安装依赖（让 AI 生成 requirements.txt）
pip install httpx jinja2 beautifulsoup4 python-dotenv pydantic

# Step 3: 创建 .env 文件
cat > .env << 'EOF'
DOUBAO_API_KEY=your_doubao_api_key_here
OPENAI_API_KEY=your_openai_key_here  # 用于阶段 1/7/9 的 LLM 推理
EOF

# Step 4: Vibe Coding 生成代码（依次执行以下提示词给 AI）
```

**提示词序列（每次一个，逐步推进）**：

| 步骤 | 提示词 | 预期产出 |
|------|--------|----------|
| 1 | "写一个 Python 函数，输入品牌名和产品类型，调用 LLM API 生成 3 个用户画像和 15 个搜索问题，输出 JSON" | `stages/s1_user_profile.py` |
| 2 | "写一个函数，用 requests 抓取给定官网，检查 HTTPS/结构化数据/核心页面完整性，返回 0-100 评分" | `stages/s2_infra_eval.py` |
| 3 | "写一个函数，用搜索 API 搜索'品牌名+竞品/排行榜'，从结果中提取高频共现品牌，返回竞品列表" | `stages/s3_competitor.py` |
| 4 | "写一个异步函数，接收问题列表，调用豆包 API 逐个搜索，记录品牌是否被提及及位置，返回汇总数据" | `stages/s4_ai_search.py` |
| 5 | "写一个函数，接收搜索测试结果，计算提及率/首段提及率/竞品共现矩阵" | `stages/s5_geo_effect.py` |
| 6 | "写一个函数，搜索黑猫投诉/小红书/微博的品牌相关内容，计算负面率和情感分布" | `stages/s6_sentiment.py` |
| 7 | "写一个函数，基于前面所有阶段数据，生成一句话总结+亮点列表+风险列表" | `stages/s7_overview.py` |
| 8 | "写一个函数，按 4 维度×25% 权重计算 AIVO 总分，返回各维度得分和等级" | `stages/s8_aivo_score.py` |
| 9 | "写一个函数，基于评分结果生成优化建议（含优先级/影响/预期提升/路线图）" | `stages/s9_suggestion.py` |
| 10 | "写一个 Jinja2 HTML 模板，展示 AIVO 评分圆环、竞品条形图、优化建议时间轴" | `report/template.html` |
| 11 | "写一个主函数，串联以上 9 个阶段，处理并行和异常降级，输出 JSON 和 HTML" | `main.py` |
| 12 | "写一个 JSON 修复工具，处理中文引号、未转义换行符、末尾逗号等问题" | `utils/json_repair.py` |

**关键原则**：每生成一个阶段，立即 `python -c "import stages.s1_user_profile; print('OK')"` 验证可运行，再进入下一个阶段。

---

## 3. 方案 B：Dify / WorkBuddy 工作流

### 3.1 适用场景

- 已在使用 WorkBuddy 或 Dify 平台
- 希望无代码/低代码实现
- 需要在平台内直接对话交互（无需命令行）

### 3.2 工作流节点设计

```
[开始节点]
   ↓
[对话收集节点] —— 收集：品牌名、产品类型、官网（可选）
   ↓
[LLM 节点: Stage 1] —— 生成用户画像和搜索问题（JSON 输出）
   ↓
[并行分支开始]
   ├─ [HTTP 节点: Stage 2] —— 抓取官网，评估基建
   └─ [LLM 节点: Stage 3] —— 识别 3-5 家竞品
   ↓
[并行分支合并]
   ↓
[代码节点: 合并 Stage 2+3 数据]
   ↓
[迭代节点: Stage 4] —— 循环调用搜索 API（每个问题一次）
   ↓
[代码节点: Stage 5] —— GEO 效果汇总计算
   ↓
[HTTP 节点: Stage 6] —— 舆情抓取（黑猫投诉/小红书等）
   ↓
[代码节点: Stage 7+8] —— 综合总览 + AIVO 评分
   ↓
[LLM 节点: Stage 9] —— 生成优化建议（自然语言）
   ↓
[代码节点: JSON 合并] —— 合并全部阶段数据（含修复）
   ↓
[模板节点: HTML 生成] —— 基于 Jinja2 模板渲染报告
   ↓
[结束节点] —— 输出报告文件路径 + 摘要
```

### 3.3 Dify 中的关键配置

**变量定义**：

| 变量名 | 类型 | 说明 |
|--------|------|------|
| `brand` | String | 品牌名称 |
| `category` | String | 产品类型 |
| `website` | String | 官网地址（可选） |
| `platform` | String | 诊断平台（默认豆包） |
| `stage1_output` | Object | 阶段 1 用户画像 JSON |
| `stage2_output` | Object | 阶段 2 基建评估 JSON |
| `stage3_output` | Object | 阶段 3 竞品分析 JSON |
| `stage4_output` | Object | 阶段 4 AI 搜索 JSON |
| `final_report` | Object | 合并后的完整报告 JSON |

**代码节点示例（Stage 8: AIVO 评分计算）**：

```python
# Dify 代码节点输入变量：infra_score, search_mention_rate, competitor_score, sentiment_negative_rate

def main(infra_score: int, search_mention_rate: float, competitor_score: int, sentiment_negative_rate: float) -> dict:
    """计算 AIVO 4 维度评分"""
    
    # 维度 1：AI 搜索可见度（提及率直接映射）
    visibility = min(100, search_mention_rate * 1.2)  # 小幅加权
    
    # 维度 2：基建完善度（直接传入）
    infra = infra_score
    
    # 维度 3：竞品对比优势（直接传入）
    competitive = competitor_score
    
    # 维度 4：舆情健康度（基于负面率）
    sentiment = max(0, 100 - sentiment_negative_rate * 2.5)
    
    # 加权总分
    total = round((visibility + infra + competitive + sentiment) / 4)
    
    # 等级判定
    grade = "优秀" if total >= 90 else \
            "良好" if total >= 80 else \
            "中等" if total >= 70 else \
            "较差" if total >= 60 else "差"
    
    return {
        "total": total,
        "grade": grade,
        "dimensions": {
            "visibility": round(visibility),
            "infra": infra,
            "competitive": competitive,
            "sentiment": round(sentiment)
        }
    }
```

### 3.4 WorkBuddy 特有注意事项

根据 WorkBuddy 运行记录，该平台存在以下特点：

| 特点 | 影响 | 应对策略 |
|------|------|----------|
| **工具调用权限管控** | Agent 调用搜索 API 前需用户确认 | 在对话中明确告知用户"即将调用搜索工具"，减少打断 |
| **JSON 解析严格** | 中文引号 `"` `"` 会直接破坏 JSON | 在代码节点中强制替换中文引号为英文 `"` |
| **文件输出限制** | 生成的 HTML 文件可能无法直接预览 | 将 HTML 内容直接输出到对话中（代码块形式），或提供下载链接 |
| **会话超时** | 长耗时流水线可能触发超时 | 将阶段 1+2+3 合并为第一批，阶段 4+5+6 合并为第二批，分步推进 |

---

## 4. 方案 C：Next.js 全栈 SaaS

### 4.1 适用场景

- 需要多用户支持
- 需要历史记录和趋势追踪
- 需要付费订阅或团队协作功能
- 计划商业化运营

### 4.2 技术栈

| 层级 | 技术 | 说明 |
|------|------|------|
| **前端** | Next.js 14 + Tailwind CSS | 品牌输入表单、报告预览页面 |
| **后端 API** | Next.js API Routes / tRPC | 诊断流水线接口 |
| **数据库** | PostgreSQL + Prisma | 诊断记录、用户数据、历史趋势 |
| **任务队列** | BullMQ + Redis | 异步执行诊断流水线（避免 HTTP 超时） |
| **文件存储** | AWS S3 / 阿里云 OSS | 报告文件持久化存储 |
| **部署** | Vercel / 阿里云 ECS | 全栈部署 |

### 4.3 核心 API 设计

```typescript
// POST /api/diagnose
// 请求体
interface DiagnoseRequest {
  brand: string;
  category: string;
  website?: string;
  platform: 'doubao' | 'chatgpt' | 'perplexity';
}

// 响应体（异步任务创建）
interface DiagnoseResponse {
  taskId: string;
  status: 'queued' | 'running' | 'completed' | 'failed';
  estimatedTime: number; // 秒
}

// GET /api/diagnose/:taskId
// 轮询获取诊断进度和结果
interface DiagnoseStatusResponse {
  taskId: string;
  status: 'queued' | 'running' | 'completed' | 'failed';
  progress: number; // 0-100
  currentStage: string;
  result?: {
    aivoScore: number;
    grade: string;
    reportUrl: string; // HTML 报告下载链接
    jsonUrl: string;   // JSON 数据下载链接
  };
  error?: string;
}
```

### 4.4 前端页面流程

```
/                     # 首页：产品价值展示 + 开始诊断按钮
/diagnose             # 诊断输入页：表单收集品牌信息
/diagnose/:taskId     # 诊断进度页：实时显示阶段进度（SSE 推送）
/report/:reportId     # 报告详情页：嵌入 HTML 报告预览
/dashboard            # 用户仪表盘：历史诊断记录列表
/dashboard/:brand     # 品牌趋势页：多次诊断的分数变化曲线
```

---

## 5. 渐进式实施路线图

### Phase 1：Python MVP（Day 1，2-4 小时）

**目标**：验证核心逻辑，确认 AIVO 评分算法合理

| 时间 | 任务 | 验证标准 |
|------|------|----------|
| 0:00-0:30 | 搭建项目骨架 + 安装依赖 | `python main.py --help` 正常输出 |
| 0:30-1:30 | 实现阶段 1-3（串行） | 输入"听力熊"，输出用户画像+基建评分+竞品列表 |
| 1:30-2:30 | 实现阶段 4（AI 搜索测试） | 15 个问题中品牌提及次数符合预期（约 7/15） |
| 2:30-3:30 | 实现阶段 5-9（串行） | 输出完整 JSON，包含 AIVO 总分和优化建议 |
| 3:30-4:00 | 生成 HTML 报告 | 双击打开 HTML，能看到评分圆环和竞品条形图 |

**交付物**：一个可运行的 Python 脚本，能对一个品牌输出 JSON + HTML 报告

### Phase 2：健壮性增强（Day 2-3，4-6 小时）

**目标**：处理真实世界的异常情况

| 任务 | 说明 |
|------|------|
| 添加异步并行 | 阶段 2&3 并行、阶段 4 内的问题搜索并行（控制并发数） |
| JSON 修复工具 | 处理中文引号、未转义字符、末尾逗号（参考 utils/json_repair.py） |
| 异常降级 | 某个阶段失败时，用默认值/缓存继续，不打断流水线 |
| 日志记录 | 每个阶段记录耗时、数据量级、成功/失败状态 |
| 配置文件 | 用 .env 管理 API Key，支持多平台切换 |

**交付物**：鲁棒的诊断脚本，能处理 90% 以上的异常情况

### Phase 3：Dify 工作流迁移（Day 4-5，1-2 天）

**目标**：产品化，支持对话式交互

| 任务 | 说明 |
|------|------|
| 拆解为工作流节点 | 将 Python 函数映射为 Dify 的 LLM/代码/HTTP 节点 |
| 对话交互设计 | 设计 9 个交互节点的文案和分支逻辑 |
| 模板迁移 | 将 Jinja2 模板转为 Dify 模板节点支持的格式 |
| 测试调优 | 在 Dify 中跑通 3-5 个品牌，修复节点间数据传递问题 |

**交付物**：Dify / WorkBuddy 中可运行的对话式 Agent

### Phase 4：Next.js 升级（Day 6-10，视需求）

**目标**：商业化，支持多用户和历史追踪

| 任务 | 说明 |
|------|------|
| 数据库设计 | 用户表、诊断记录表、品牌追踪表 |
| API 开发 | 异步诊断任务队列 + 进度查询接口 |
| 前端页面 | 诊断输入、进度展示、报告预览、历史趋势 |
| 部署上线 | Vercel / 阿里云部署 + 域名配置 |

**交付物**：可公开访问的 GEO 诊断 SaaS 服务

---

## 6. Vibe Coding 操作手册

### 6.1 与 AI 协作的最佳实践

| 实践 | 说明 | 示例 |
|------|------|------|
| **一次一个阶段** | 不要一次性让 AI 生成全部代码，逐阶段验证 | ❌ "帮我写整个诊断系统" → ✅ "先写阶段 1 的用户画像生成函数" |
| **提供具体输入输出** | 告诉 AI 输入什么、期望输出什么格式 | "输入：品牌名'听力熊'，输出：JSON 格式，包含 3 个用户群体和每组 5 个问题" |
| **用 print 验证** | 每阶段完成后立即打印输出，确认符合预期 | `print(json.dumps(result, indent=2, ensure_ascii=False))` |
| **遇到错误直接贴** | 把完整错误信息贴给 AI，让它修复 | "运行时报错：JSONDecodeError: Expecting ',' delimiter，完整代码如下..." |
| **保留上下文** | 在同一会话中持续迭代，不要新开对话 | 在同一个 Chat 中逐步推进 12 个阶段 |

### 6.2 典型提示词模板

**模板 1：生成阶段函数**

```
你是一个 Python 开发专家。请帮我写一个异步函数，实现 GEO 诊断流水线的阶段 X：[阶段名称]。

输入参数：
- brand: str（品牌名称，如"听力熊"）
- [其他参数]

期望输出（JSON 格式）：
{
  "[关键字段1]": ...,
  "[关键字段2]": ...
}

实现要求：
1. 使用 httpx 进行异步 HTTP 请求
2. 错误处理：API 失败时返回默认值，不打断流程
3. 添加类型注解
4. 包含 docstring 说明函数用途

请直接输出完整代码，不需要解释。
```

**模板 2：修复错误**

```
我运行以下代码时遇到了错误：

[粘贴完整错误堆栈]

代码如下：
[粘贴相关代码]

请帮我修复这个问题，直接输出修复后的代码。
```

**模板 3：生成 HTML 模板**

```
请帮我写一个 Jinja2 HTML 模板，用于展示 GEO 诊断报告。

需要展示的数据：
- AIVO 总分（0-100）+ 等级（优秀/良好/中等/较差/差）
- 4 维度雷达图或条形图（AI 搜索可见度、基建完善度、竞品对比优势、舆情健康度）
- 5 家竞品的横向对比条形图
- 优化建议列表（含优先级标签和时间轴）

设计要求：
1. 全部 CSS 内嵌，无外部依赖
2. 使用 Tailwind CSS 类名
3. 响应式布局
4. 颜色映射：优秀=绿色，良好=黄绿，中等=黄色，较差=橙色，差=红色

请输出完整的 HTML 模板代码（包含 {% raw %} 等 Jinja2 语法）。
```

### 6.3 常见陷阱与规避

| 陷阱 | 表现 | 规避方法 |
|------|------|----------|
| **JSON 合并错误** | 多阶段数据合并后解析失败 | 每个阶段输出前用 `json.dumps` 验证，合并后调用 `repair_json` |
| **API 限流** | 豆包/搜索 API 返回 429 | 用 `asyncio.Semaphore` 控制并发，添加指数退避重试 |
| **LLM 输出不稳定** | 阶段 1/7/9 的 LLM 输出格式不一致 | 设置 `response_format="json"`，添加输出 Schema 校验 |
| **中文编码问题** | HTML 报告中中文显示为乱码 | 所有文件读写指定 `encoding="utf-8"`，HTML 添加 `<meta charset="UTF-8">` |
| **路径依赖** | 代码中硬编码了本地路径 | 使用 `Path(__file__).parent` 获取相对路径 |

---

## 7. 风险与对策

### 7.1 技术风险

| 风险 | 影响 | 对策 |
|------|------|------|
| **豆包 API 不稳定** | 阶段 4 搜索测试失败，无法获取核心数据 | 1. 实现缓存机制，复用近期搜索结果<br>2. 支持多平台切换（ChatGPT/Perplexity 备用）<br>3. 降级为模拟数据（基于历史均值估算） |
| **官网反爬** | 阶段 2 基建评估无法抓取 | 1. 使用 Playwright 模拟真实浏览器<br>2. 控制请求频率（1 秒/次）<br>3. 失败时标记"无法访问"，不影响总分 |
| **舆情平台封禁** | 阶段 6 舆情数据缺失 | 1. 多源抓取（黑猫/小红书/微博互为备份）<br>2. 使用搜索 API 间接获取<br>3. 标记"数据暂缺"，用行业均值替代 |
| **LLM 幻觉** | 阶段 1/3/7/9 的 LLM 生成内容不准确 | 1. 增加校验层（如竞品必须在搜索结果中真实出现）<br>2. 用规则引擎兜底（如建议必须从知识库匹配）<br>3. 用户确认环节（竞品列表让用户确认） |

### 7.2 业务风险

| 风险 | 影响 | 对策 |
|------|------|------|
| **评分算法偏差** | AIVO 分数不能反映真实 GEO 水平 | 1. 用 10-20 个已知品牌校准算法<br>2. 收集用户反馈，季度调整权重<br>3. 公开评分逻辑，接受质疑 |
| **竞品识别错误** | 自动识别的竞品不符合用户认知 | 1. 输出候选列表让用户确认<br>2. 支持用户手动添加/删除竞品<br>3. 使用多信号交叉验证 |
| **建议不可执行** | 生成的优化建议过于空泛 | 1. 建议绑定具体指标（如"添加 Schema.org Product 标记"而非"优化官网"）<br>2. 附带操作步骤和资源链接<br>3. 区分 Quick Win 和长期项目 |

### 7.3 合规风险

| 风险 | 影响 | 对策 |
|------|------|------|
| **数据隐私** | 诊断过程中收集了品牌敏感信息 | 1. 不存储用户输入（除非用户主动保存）<br>2. 诊断完成后 24 小时自动清理临时数据<br>3. 隐私政策明确说明数据用途 |
| **爬虫合规** | 抓取官网/舆情可能违反 ToS | 1. 遵守 robots.txt<br>2. 控制请求频率（≤1 次/秒）<br>3. 使用公开 API 优先于直接抓取 |
| **API 滥用** | 大量调用搜索 API 导致账号封禁 | 1. 实现用量限制（单用户/单天上限）<br>2. 缓存结果避免重复查询<br>3. 监控异常用量 |

---

## 附录：快速启动模板

### `requirements.txt`

```
httpx>=0.27.0
jinja2>=3.1.0
beautifulsoup4>=4.12.0
python-dotenv>=1.0.0
pydantic>=2.0.0
pydantic-settings>=2.0.0
```

### `.env.example`

```bash
# AI 平台 API Key
DOUBAO_API_KEY=sk-xxxxxxxx
OPENAI_API_KEY=sk-xxxxxxxx

# 搜索 API（可选，如使用 SerpAPI 等第三方搜索）
SERPAPI_KEY=xxxxxxxx

# 配置
DEFAULT_PLATFORM=doubao
MAX_CONCURRENT_SEARCHES=3
REQUEST_TIMEOUT=30
```

### 运行命令

```bash
# 1. 克隆/创建项目
cd geo-diagnosis

# 2. 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. 安装依赖
pip install -r requirements.txt

# 4. 配置 API Key
cp .env.example .env
# 编辑 .env，填入你的 API Key

# 5. 运行诊断
python main.py --brand "听力熊" --category "儿童AI对话智能体" --platform doubao

# 6. 查看输出
open output/*/听力熊-GEO诊断报告.html  # macOS
start output/*/听力熊-GEO诊断报告.html  # Windows
```

---

---

## 附录：V2.0 演进路线

基于 VibeCoding 培训课程差距评审（详见 `VibeCoding-课程差距评审.md`），V2.0 按以下优先级演进：

```
Phase 1：工程化夯实（对应 DAY-03）
├── pytest 自动化测试覆盖 9 个阶段
├── FastAPI 包装为 Web 服务
└── AGENTS.md 改写为 MDC 标准格式

Phase 2：MCP 核心能力（对应 DAY-02）
├── 学习 MCP 协议，跑通官方示例
├── 将搜索/豆包 API 封装为 MCP Tool
└── 在诊断流程中实现 LLM LOOP

Phase 3：部署与服务化（对应 DAY-01）
├── Vercel/阿里云部署
├── Landing Page + 诊断表单
└── 用户历史记录（SQLite/PostgreSQL）

Phase 4：自主 Agent（对应 DAY-04）
├── LangGraph 重构流水线
├── 条件边：根据 AIVO 分数动态分支
└── 循环决策：阶段失败自动重试/换策略
```

**V2.0 核心目标**：从"固定流水线脚本（Script）"进化为"自主决策 Agent（Autonomous Agent）"。

---

*本文档为 GEO 可见度诊断师 V1.0 实现方案，V2.0 规划待执行。*
