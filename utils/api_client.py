"""
GEO 可见度诊断师 — API 客户端封装模块

封装 LLM Chat 与豆包搜索的异步 HTTP 调用，统一提供：
- 超时与指数退避重试
- 错误降级（返回安全默认值，绝不抛未捕获异常）
- API Key 与 Base URL 从环境变量读取，文件中不残留密钥
"""

from __future__ import annotations

import asyncio
import os
from typing import Any

import httpx

# ───────────────────────────────────────────────
# 环境变量延迟读取（避免 .env 加载顺序问题）
# ───────────────────────────────────────────────

def _get_openai_key() -> str:
    """读取 OpenAI API Key，同时兼容 Kimi Key 作为 fallback。"""
    return os.environ.get("OPENAI_API_KEY") or os.environ.get("KIMI_API_KEY", "")

def _get_openai_url() -> str:
    """读取 OpenAI Base URL，同时兼容 Kimi URL 作为 fallback。"""
    openai_url = os.environ.get("OPENAI_BASE_URL")
    if openai_url:
        return openai_url
    kimi_url = os.environ.get("KIMI_API_URL")
    if kimi_url:
        return kimi_url
    if os.environ.get("KIMI_API_KEY") and not os.environ.get("OPENAI_API_KEY"):
        return "https://api.moonshot.cn/v1"
    return "https://api.openai.com/v1"

def _get_doubao_key() -> str:
    return os.environ.get("DOUBAO_API_KEY", "")

def _get_doubao_url() -> str:
    return os.environ.get("DOUBAO_BASE_URL", "https://ark.cn-beijing.volces.com/api/v3")

_DEFAULT_TIMEOUT: float = float(os.environ.get("REQUEST_TIMEOUT", "60"))
_MAX_RETRIES: int = int(os.environ.get("MAX_RETRIES", "2"))


# 模型名映射表：当目标端点不支持某些模型名时自动替换
_MODEL_NAME_ALIASES: dict[str, str] = {
    # Kimi 端点不支持 gpt-4o，映射到 moonshot-v1-8k
    "gpt-4o": "moonshot-v1-8k",
    "gpt-4o-mini": "moonshot-v1-8k",
    "gpt-4": "moonshot-v1-32k",
}


def _resolve_model(model: str, base_url: str) -> str:
    """根据目标端点解析正确的模型名。

    若 base_url 指向 Kimi（moonshot），且模型名为 OpenAI 专用名，
    则自动替换为 Kimi 支持的等效模型。
    """
    lowered_url = base_url.lower()
    if "moonshot" in lowered_url or "kimi" in lowered_url:
        return _MODEL_NAME_ALIASES.get(model, model)
    return model


def _chat_url(base_url: str) -> str:
    """构建 Chat Completions 完整 URL，避免重复拼接路径。"""
    base = base_url.rstrip("/")
    if base.endswith("/chat/completions"):
        return base
    return f"{base}/chat/completions"


def _select_endpoint(model: str) -> tuple[str, str]:
    """
    根据模型名称选择对应的 API Key 与 Base URL。

    参数：
        model: 模型标识字符串。

    返回：
        (api_key, base_url) 元组。
    """
    lowered = model.lower()
    if "doubao" in lowered or "ark" in lowered:
        key = _get_doubao_key()
        if key:
            return key, _get_doubao_url()
        return _get_openai_key(), _get_openai_url()
    key = _get_openai_key()
    if key:
        return key, _get_openai_url()
    return _get_doubao_key(), _get_doubao_url()


async def _post_with_retry(
    client: httpx.AsyncClient,
    url: str,
    headers: dict[str, str],
    payload: dict[str, Any],
) -> dict[str, Any] | None:
    """
    带指数退避的 POST 请求封装。

    参数：
        client: httpx 异步客户端实例。
        url: 请求地址。
        headers: HTTP 请求头。
        payload: JSON 请求体。

    返回：
        成功时返回解析后的 JSON 字典；失败（含重试耗尽）返回 None。
    """
    for attempt in range(1, _MAX_RETRIES + 1):
        try:
            resp = await client.post(url, headers=headers, json=payload)
            resp.raise_for_status()
            return resp.json()
        except httpx.HTTPStatusError as exc:
            # 4xx 客户端错误不再重试
            if exc.response.status_code < 500:
                return None
            # 5xx 在重试次数内继续退避
            if attempt < _MAX_RETRIES:
                await asyncio.sleep(2 ** attempt)
            continue
        except (httpx.ConnectError, httpx.TimeoutException, httpx.NetworkError):
            if attempt < _MAX_RETRIES:
                await asyncio.sleep(2 ** attempt)
            continue
        except Exception:
            # 未知异常静默吞掉，返回 None
            return None
    return None


# ───────────────────────────────────────────────
# 公共接口
# ───────────────────────────────────────────────

async def llm_chat(
    prompt: str,
    model: str = "gpt-4o",
    response_format: str = "text",
    temperature: float = 0.7,
    max_tokens: int = 4096,
    system_message: str | None = None,
) -> str:
    """
    调用 LLM Chat Completion API，兼容 OpenAI 及豆包 Ark 格式。

    API Key 与 Base URL 根据 model 名称自动路由：
    - 若 model 包含 "doubao" 或 "ark"，使用 DOUBAO_API_KEY / DOUBAO_BASE_URL；
    - 否则使用 OPENAI_API_KEY / OPENAI_BASE_URL；
    - 任一未配置时尝试回退到另一组密钥。

    参数：
        prompt: 用户输入的提示词内容。
        model: 模型名称，如 "gpt-4o"、"doubao-pro-32k" 等。
        response_format: 返回格式，支持 "text" 或 "json"。
        temperature: 采样温度，默认 0.7。
        max_tokens: 最大生成 token 数，默认 4096。
        system_message: 可选的系统角色消息。

    返回：
        LLM 生成的文本字符串。若 API 调用失败或密钥未配置，
        返回空字符串 ""，绝不抛出异常。

    示例：
        >>> answer = await llm_chat("请介绍 Python 异步编程", model="gpt-4o")
    """
    api_key, base_url = _select_endpoint(model)
    if not api_key:
        return ""

    # 解析为端点实际支持的模型名
    resolved_model = _resolve_model(model, base_url)

    messages: list[dict[str, str]] = []
    if system_message:
        messages.append({"role": "system", "content": system_message})
    messages.append({"role": "user", "content": prompt})

    payload: dict[str, Any] = {
        "model": resolved_model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    if response_format == "json":
        payload["response_format"] = {"type": "json_object"}

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    async with httpx.AsyncClient(timeout=_DEFAULT_TIMEOUT) as client:
        data = await _post_with_retry(
            client, _chat_url(base_url), headers, payload
        )

    if data is None:
        return ""

    try:
        choices = data.get("choices", [])
        if choices:
            content = choices[0].get("message", {}).get("content", "")
            return content.strip() if content else ""
    except Exception:
        pass

    return ""


# ═──────────────────────────────────────────────
# 豆包 Responses API 封装
# ═──────────────────────────────────────────────


def _parse_doubao_response(data: dict[str, Any]) -> str:
    """从豆包 Responses API 返回中提取助手文本内容。

    响应结构：
        output: [
            {type: "reasoning", ...},
            {type: "message", role: "assistant", content: [
                {type: "output_text", text: "..."}
            ]}
        ]
    """
    for out in data.get("output", []):
        if out.get("type") == "message" and out.get("role") == "assistant":
            for c in out.get("content", []):
                if c.get("type") == "output_text":
                    return c.get("text", "")
    return ""


async def _post_doubao_responses(
    client: httpx.AsyncClient,
    payload: dict[str, Any],
) -> dict[str, Any] | None:
    """调用豆包 Responses API，带重试。"""
    # 构建正确端点：去掉可能的 /chat/completions 后缀，追加 /responses
    base = _get_doubao_url().rstrip("/")
    if base.endswith("/chat/completions"):
        base = base[: -len("/chat/completions")]
    url = f"{base}/responses"
    headers = {
        "Authorization": f"Bearer {_get_doubao_key()}",
        "Content-Type": "application/json",
    }
    for attempt in range(1, _MAX_RETRIES + 1):
        try:
            resp = await client.post(url, headers=headers, json=payload)
            resp.raise_for_status()
            return resp.json()
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code < 500:
                return None
            if attempt < _MAX_RETRIES:
                await asyncio.sleep(2 ** attempt)
            continue
        except (httpx.ConnectError, httpx.TimeoutException, httpx.NetworkError):
            if attempt < _MAX_RETRIES:
                await asyncio.sleep(2 ** attempt)
            continue
        except Exception:
            return None
    return None


async def doubao_chat(
    prompt: str,
    model: str = "doubao-seed-evolving",
    system_prompt: str | None = None,
    temperature: float = 0.7,
    max_tokens: int = 4096,
) -> str:
    """调用豆包 Responses API 进行通用对话。

    参数：
        prompt: 用户输入文本。
        model: 豆包模型，默认 "doubao-seed-evolving"。
        system_prompt: 可选系统提示。
        temperature: 采样温度。
        max_tokens: 最大输出 token 数。

    返回：
        助手生成的文本字符串。失败返回空字符串。
    """
    if not _get_doubao_key():
        return ""

    input_items: list[dict[str, Any]] = []
    if system_prompt:
        # 豆包 Responses API 不支持 role: system，将 system prompt 前置到 user 内容中
        combined_prompt = (
            f"【系统指令】{system_prompt}\n"
            "请直接给出答案，不需要展示思考过程，控制在300字以内。\n\n"
            f"【用户问题】{prompt}"
        )
        input_items.append({
            "role": "user",
            "content": [{"type": "input_text", "text": combined_prompt}],
        })
    else:
        input_items.append({
            "role": "user",
            "content": [{"type": "input_text", "text": prompt}],
        })

    payload: dict[str, Any] = {
        "model": model,
        "input": input_items,
    }

    async with httpx.AsyncClient(timeout=_DEFAULT_TIMEOUT) as client:
        data = await _post_doubao_responses(client, payload)

    if data is None:
        return ""

    text = _parse_doubao_response(data)
    return text.strip() if text else ""


async def doubao_search(
    query_text: str,
    model: str = "doubao-seed-evolving",
    temperature: float = 0.3,
    max_tokens: int = 4096,
) -> dict:
    """
    调用豆包搜索能力，基于 Ark Responses API。

    通过 system prompt 引导模型针对用户 query 给出信息完整的搜索式回答。

    参数：
        query_text: 搜索查询文本。
        model: 豆包模型标识，默认 "doubao-seed-evolving"。
        temperature: 采样温度，默认 0.3（降低幻觉）。
        max_tokens: 最大生成 token 数，默认 4096。

    返回：
        {
            "answer": str,          # 回答前 800 字符摘要
            "raw_response": str,    # 完整原始回答
            "success": bool,        # 调用是否成功
            "error": str | None,    # 错误信息（成功时为 None）
        }

    错误降级：
        若 API 密钥缺失、超时或任何异常，返回 answer="" 的降级字典，
        绝不抛出未捕获异常。
    """
    if not _get_doubao_key():
        return {
            "answer": "",
            "raw_response": "",
            "success": False,
            "error": "DOUBAO_API_KEY not configured",
        }

    system_prompt: str = (
        "你是一个智能搜索助手。请针对用户的搜索问题，"
        "给出准确、客观、信息完整的回答。"
        "请直接给出答案，不需要展示思考过程，控制在300字以内。"
    )

    payload: dict[str, Any] = {
        "model": model,
        "input": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "input_text",
                        "text": f"【系统指令】{system_prompt}\n\n【用户搜索问题】{query_text}",
                    }
                ],
            },
        ],
    }

    async with httpx.AsyncClient(timeout=_DEFAULT_TIMEOUT) as client:
        data = await _post_doubao_responses(client, payload)

    if data is None:
        return {
            "answer": "",
            "raw_response": "",
            "success": False,
            "error": "API request failed after retries",
        }

    raw_answer = _parse_doubao_response(data)
    if raw_answer:
        snippet = raw_answer[:800] if raw_answer else ""
        return {
            "answer": snippet,
            "raw_response": raw_answer,
            "success": True,
            "error": None,
        }
    return {
        "answer": "",
        "raw_response": "",
        "success": False,
        "error": "Empty response from API",
    }
