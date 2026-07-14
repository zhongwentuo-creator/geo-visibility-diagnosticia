"""
Stage 1: 用户画像构建 — USER_PROFILE

基于品牌名称和产品类型，通过 LLM 生成 3 类核心用户画像及其搜索意图矩阵。
每类画像包含：用户身份标签、核心需求场景、典型搜索 Query 列表（5-8 条）。

接口规范：
    async def build(brand: str, category: str) -> dict
    返回 {"segments": [...], "totalQueries": int}

降级策略：
    - LLM API 不可用时，基于品类关键词模板生成默认用户画像与查询
"""

from __future__ import annotations

import json
import os
import random
from typing import Any

import httpx

# ---------------------------------------------------------------------------
# 常量与配置
# ---------------------------------------------------------------------------

DEFAULT_TIMEOUT: float = 30.0
"""HTTP 请求默认超时（秒）"""

LLM_API_URL: str = os.environ.get("LLM_API_URL", "https://api.openai.com/v1/chat/completions")
"""LLM API 端点，默认 OpenAI；可通过环境变量覆盖"""

LLM_API_KEY: str | None = os.environ.get("OPENAI_API_KEY")
"""LLM API Key，从环境变量读取，文件中不硬编码"""

LLM_MODEL: str = os.environ.get("LLM_MODEL", "gpt-4o")
"""默认 LLM 模型，可通过环境变量覆盖"""

DEFAULT_QUERIES_PER_SEGMENT: int = 6
"""每类用户默认生成的查询数量"""

# 品类 → 默认用户画像模板（API 完全不可用时的降级数据）
CATEGORY_TEMPLATES: dict[str, list[dict[str, Any]]] = {
    "default": [
        {
            "id": "UP001",
            "label": "潜在购买者（决策者）",
            "description": "正在对比选购、寻求购买建议的核心消费群体",
            "demographics": "25-45岁，中等以上收入，线上活跃",
            "searchIntent": ["信息型", "比较型", "交易型"],
            "queries": [
                {"text": "{brand} {category} 怎么样", "intent": "信息型", "expectedAnswer": "品牌评价与优缺点"},
                {"text": "{category} 推荐 哪个品牌好", "intent": "比较型", "expectedAnswer": "品牌排行榜或对比"},
                {"text": "{brand} 和 {competitor_placeholder} 哪个好", "intent": "对比型", "expectedAnswer": "直接竞品对比"},
                {"text": "{category} 值得买吗", "intent": "交易型", "expectedAnswer": "购买建议与性价比"},
                {"text": "{brand} {category} 价格", "intent": "交易型", "expectedAnswer": "价格区间与购买渠道"},
                {"text": "{category} 用户评价", "intent": "信息型", "expectedAnswer": "真实用户体验"},
            ],
        },
        {
            "id": "UP002",
            "label": "现有用户（使用者）",
            "description": "已购买产品，关注使用体验、售后与技巧",
            "demographics": "全年龄段，产品持有者，社群活跃",
            "searchIntent": ["信息型", "导航型"],
            "queries": [
                {"text": "{brand} {category} 使用教程", "intent": "导航型", "expectedAnswer": "操作指南或官方教程"},
                {"text": "{brand} 售后服务怎么样", "intent": "信息型", "expectedAnswer": "售后政策与体验"},
                {"text": "{brand} {category} 常见问题", "intent": "信息型", "expectedAnswer": "FAQ 与故障排查"},
                {"text": "{brand} 最新功能更新", "intent": "信息型", "expectedAnswer": "产品迭代信息"},
                {"text": "{brand} {category} 隐藏功能", "intent": "信息型", "expectedAnswer": "高级使用技巧"},
                {"text": "{brand} 维修 保修", "intent": "信息型", "expectedAnswer": "维修点与保修政策"},
            ],
        },
        {
            "id": "UP003",
            "label": "行业观察者/研究者",
            "description": "关注行业趋势、品牌竞争格局与投资价值",
            "demographics": "行业从业者、投资人、媒体记者",
            "searchIntent": ["信息型", "比较型"],
            "queries": [
                {"text": "{category} 行业趋势 2024", "intent": "信息型", "expectedAnswer": "市场分析与趋势预测"},
                {"text": "{brand} 市场份额 {category}", "intent": "信息型", "expectedAnswer": "市场占有率数据"},
                {"text": "{category} 品牌排名", "intent": "比较型", "expectedAnswer": "行业品牌排行榜"},
                {"text": "{brand} 公司背景 发展历程", "intent": "信息型", "expectedAnswer": "企业信息与品牌故事"},
                {"text": "{category} 新技术", "intent": "信息型", "expectedAnswer": "技术突破与创新点"},
                {"text": "{brand} 竞品分析", "intent": "比较型", "expectedAnswer": "竞争格局与对标分析"},
            ],
        },
    ]
}


# ---------------------------------------------------------------------------
# 内部辅助函数
# ---------------------------------------------------------------------------

def _build_llm_prompt(brand: str, category: str, queries_per_segment: int = 6) -> str:
    """
    构建调用 LLM 生成用户画像的 prompt。

    Args:
        brand: 品牌名称
        category: 产品类型
        queries_per_segment: 每类用户生成的查询数量

    Returns:
        完整的 prompt 字符串
    """
    return f"""你是一个专业的中国市场研究分析师，擅长消费者洞察与搜索行为分析。

请基于以下品牌信息，生成核心用户画像与 AI 搜索意图矩阵：

品牌名称：{brand}
产品类型：{category}

任务要求：
1. 识别 3 类核心目标用户群体，每类需包含：
   - id: 格式 "UP001"、"UP002"、"UP003"
   - label: 用户群体名称（如"潜在购买者"）
   - description: 该群体的特征描述（1-2句话）
   - demographics: 人口统计特征（年龄、地域、收入等）
   - searchIntent: 列表，如["信息型", "比较型"]
   - queries: {queries_per_segment} 条典型搜索问题

2. 每个查询需包含：
   - text: 搜索问题文本（自然口语化，如用户真实在 AI 平台输入的问题）
   - intent: 信息型/对比型/交易型/导航型 之一
   - expectedAnswer: 用户期望得到的回答类型（1句话）

3. 搜索问题需覆盖以下意图类型：
   - 信息型：了解品牌/产品基本信息（"怎么样"、"好用吗"）
   - 对比型：与竞品对比（"A和B哪个好"）
   - 交易型：购买决策相关（"值得买吗"、"价格"、"推荐"）
   - 导航型：寻找特定信息（"使用教程"、"售后"）

4. 问题中必须自然地包含品牌名 "{brand}" 或品类 "{category}"，模拟真实用户搜索习惯。

输出严格为以下 JSON 格式（不要包含 Markdown 代码块标记）：
{{
  "segments": [
    {{
      "id": "UP001",
      "label": "用户群体名称",
      "description": "特征描述",
      "demographics": "人口统计特征",
      "searchIntent": ["信息型", "比较型"],
      "queries": [
        {{
          "text": "具体搜索问题",
          "intent": "信息型",
          "expectedAnswer": "期望回答类型"
        }}
      ]
    }}
  ],
  "totalQueries": 18
}}
"""


def _fallback_user_profiles(brand: str, category: str) -> dict[str, Any]:
    """
    API 完全不可用时的降级数据生成器。

    基于品类模板生成默认用户画像，将占位符替换为实际品牌名与品类名。

    Args:
        brand: 品牌名称
        category: 产品类型

    Returns:
        符合规范的用户画像字典
    """
    template_key = "default"
    templates = CATEGORY_TEMPLATES.get(template_key, CATEGORY_TEMPLATES["default"])

    segments: list[dict[str, Any]] = []
    total_queries = 0

    for tmpl in templates:
        segment = {
            "id": tmpl["id"],
            "label": tmpl["label"],
            "description": tmpl["description"],
            "demographics": tmpl["demographics"],
            "searchIntent": list(tmpl["searchIntent"]),
            "queries": [],
        }

        for q in tmpl["queries"]:
            text = q["text"].format(
                brand=brand,
                category=category,
                competitor_placeholder="竞品",
            )
            segment["queries"].append(
                {
                    "text": text,
                    "intent": q["intent"],
                    "expectedAnswer": q["expectedAnswer"],
                }
            )
            total_queries += 1

        segments.append(segment)

    return {"segments": segments, "totalQueries": total_queries}


def _parse_llm_response(response_text: str) -> dict[str, Any] | None:
    """
    解析 LLM 返回的文本，提取 JSON 并校验结构。

    Args:
        response_text: LLM 原始返回文本

    Returns:
        解析后的字典，若解析失败或结构不合法则返回 None
    """
    # 1. 尝试直接解析（LLM 有时返回 JSON 代码块）
    text = response_text.strip()
    if text.startswith("```json"):
        text = text[7:]
    if text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    text = text.strip()

    # 2. 尝试解析 JSON
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        # 尝试提取文本中第一个 JSON 对象
        try:
            start = text.index("{")
            end = text.rindex("}") + 1
            data = json.loads(text[start:end])
        except (ValueError, json.JSONDecodeError):
            return None

    # 3. 结构校验
    if not isinstance(data, dict):
        return None
    if "segments" not in data or not isinstance(data["segments"], list):
        return None

    # 确保每个 segment 都有必要字段
    for seg in data["segments"]:
        if not isinstance(seg, dict):
            return None
        if "queries" not in seg or not isinstance(seg["queries"], list):
            return None
        # 确保每个 query 都有 text 字段
        for q in seg.get("queries", []):
            if not isinstance(q, dict) or "text" not in q:
                return None

    # 4. 如果没有 totalQueries，自动计算
    if "totalQueries" not in data or not isinstance(data["totalQueries"], int):
        data["totalQueries"] = sum(len(seg.get("queries", [])) for seg in data["segments"])

    return data


def _repair_chinese_quotes(data: dict[str, Any]) -> dict[str, Any]:
    """
    递归修复数据中可能包含的中英文引号混用问题。

    Args:
        data: 需要修复的字典

    Returns:
        修复后的字典
    """
    json_str = json.dumps(data, ensure_ascii=False, indent=2)
    # 中文引号替换为英文引号
    json_str = json_str.replace("\u201c", '"').replace("\u201d", '"')
    json_str = json_str.replace("\u2018", "'").replace("\u2019", "'")
    return json.loads(json_str)


# ---------------------------------------------------------------------------
# 核心 API 调用
# ---------------------------------------------------------------------------

async def _call_llm_api(prompt: str, model: str = LLM_MODEL) -> str | None:
    """
    通过 httpx 异步调用 LLM API 获取用户画像 JSON。

    Args:
        prompt: 发送给 LLM 的完整 prompt
        model: 使用的模型名称

    Returns:
        LLM 返回的文本字符串；若调用失败则返回 None
    """
    if not LLM_API_KEY:
        return None

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {LLM_API_KEY}",
    }

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": "你是一个专业的中国市场研究分析师，只输出严格的 JSON 格式数据，不要添加任何解释或 Markdown 标记。"},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.7,
        "max_tokens": 2048,
    }

    try:
        async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
            resp = await client.post(LLM_API_URL, headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()

            # 提取 choices[0].message.content
            if "choices" in data and len(data["choices"]) > 0:
                content = data["choices"][0].get("message", {}).get("content", "")
                if content:
                    return content.strip()
            return None
    except (httpx.HTTPStatusError, httpx.RequestError, httpx.TimeoutException, KeyError, json.JSONDecodeError) as exc:
        # 静默失败：记录问题类型但不抛出异常，由上游降级处理
        return None


# ---------------------------------------------------------------------------
# 阶段接口
# ---------------------------------------------------------------------------

async def build(brand: str, category: str) -> dict[str, Any]:
    """
    Stage 1：用户画像构建

    基于品牌名称和产品类型，生成 3 类核心用户画像及其搜索意图矩阵。
    每类画像包含：用户身份标签、核心需求场景、典型搜索 Query 列表。

    优先通过 LLM API 生成高质量画像；API 失败时自动降级为基于模板的默认数据。

    Args:
        brand: 品牌名称，例如 "听力熊"
        category: 产品类型，例如 "儿童AI对话智能体"

    Returns:
        包含用户画像的数据字典，结构如下：
        {
            "segments": [
                {
                    "id": "UP001",
                    "label": "潜在购买者（决策者）",
                    "description": "正在对比选购的核心消费群体",
                    "demographics": "25-45岁，中等以上收入",
                    "searchIntent": ["信息型", "比较型"],
                    "queries": [
                        {
                            "text": "听力熊儿童AI对话智能体怎么样",
                            "intent": "信息型",
                            "expectedAnswer": "品牌评价与优缺点"
                        }
                    ]
                }
            ],
            "totalQueries": 18
        }
    """
    # 1. 构建 LLM prompt
    prompt = _build_llm_prompt(brand, category, queries_per_segment=DEFAULT_QUERIES_PER_SEGMENT)

    # 2. 尝试调用 LLM API
    llm_response = await _call_llm_api(prompt, model=LLM_MODEL)

    # 3. 解析 LLM 返回
    if llm_response:
        parsed = _parse_llm_response(llm_response)
        if parsed is not None:
            # 修复中文引号问题
            parsed = _repair_chinese_quotes(parsed)
            # 确保品牌名出现在查询中（简单校验）
            for seg in parsed.get("segments", []):
                for q in seg.get("queries", []):
                    if brand not in q.get("text", "") and category not in q.get("text", ""):
                        # 如果查询中既没有品牌名也没有品类，简单追加品类名
                        q["text"] = f"{brand} {q['text']}"
            return parsed

    # 4. 降级：使用模板生成默认数据
    fallback = _fallback_user_profiles(brand, category)
    return fallback


# ---------------------------------------------------------------------------
# 测试入口（仅用于本地验证）
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import asyncio

    async def _test() -> None:
        result = await build("听力熊", "儿童AI对话智能体")
        print(json.dumps(result, ensure_ascii=False, indent=2))
        print(f"\nTotal queries: {result['totalQueries']}")
        print(f"Segments: {len(result['segments'])}")

    asyncio.run(_test())
