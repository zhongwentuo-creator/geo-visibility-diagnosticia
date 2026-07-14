from __future__ import annotations

"""Stage 2: 品牌基建评估 (INFRA_EVAL)

全面扫描品牌在互联网上的数字基础设施：
- 官网健康度 (Website Health)
- 自媒体矩阵 (Social Media Matrix)
- 权威媒体报道 (Authority Media Coverage)

评分权重：
- 官网健康度: 40%
- 自媒体矩阵: 35%
- 权威媒体: 25%

接口: async def evaluate(brand: str, website: str | None) -> dict
"""

import asyncio
import json
import re
import time
from typing import Any

import httpx

# 尝试导入 api_client，若不可用则提供降级
try:
    from utils.api_client import llm_chat
except ImportError:
    async def llm_chat(prompt: str, model: str = "gpt-4o", response_format: str = "text") -> str:
        """降级的 LLM 调用函数，始终返回空字符串。"""
        return ""


DEFAULT_TIMEOUT: float = 15.0
USER_AGENT: str = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)

# 自媒体平台基准列表
_SOCIAL_PLATFORMS: list[dict[str, str]] = [
    {"name": "微信公众号", "domain": "mp.weixin.qq.com", "keyword": "公众号"},
    {"name": "抖音", "domain": "douyin.com", "keyword": "抖音"},
    {"name": "小红书", "domain": "xiaohongshu.com", "keyword": "小红书"},
    {"name": "知乎", "domain": "zhihu.com", "keyword": "知乎"},
    {"name": "B站", "domain": "bilibili.com", "keyword": "B站"},
]

# 权威媒体基准列表
_AUTHORITY_MEDIA: list[dict[str, Any]] = [
    {"name": "36氪", "domain": "36kr.com", "weight": 0.20},
    {"name": "极客公园", "domain": "geekpark.net", "weight": 0.15},
    {"name": "虎嗅", "domain": "huxiu.com", "weight": 0.15},
    {"name": "DoNews", "domain": "donews.com", "weight": 0.15},
    {"name": "什么值得买", "domain": "smzdm.com", "weight": 0.15},
    {"name": "IT之家", "domain": "ithome.com", "weight": 0.10},
    {"name": "钛媒体", "domain": "tmtpost.com", "weight": 0.10},
]


# ==================== 辅助函数 ====================

def _normalize_url(url: str | None) -> str | None:
    """规范化 URL，补全协议前缀。

    Args:
        url: 原始 URL 字符串，可能缺少协议前缀。

    Returns:
        补全 https:// 前缀后的 URL，若输入为空则返回 None。
    """
    if not url:
        return None
    url = url.strip()
    if not url.startswith("http://") and not url.startswith("https://"):
        url = "https://" + url
    return url


def _clamp(value: int, min_val: int = 0, max_val: int = 100) -> int:
    """将数值限制在指定范围内。

    Args:
        value: 待限制的数值。
        min_val: 最小值，默认 0。
        max_val: 最大值，默认 100。

    Returns:
        限制后的整数值。
    """
    return max(min_val, min(max_val, value))


def _extract_count(raw: Any) -> int:
    """从各种输入格式中提取整数计数。

    Args:
        raw: 原始输入，可能是 int、str 或其他类型。

    Returns:
        提取出的整数，提取失败返回 0。
    """
    if isinstance(raw, int):
        return raw
    if isinstance(raw, str):
        try:
            return int(raw)
        except ValueError:
            digits = re.findall(r"\d+", raw)
            if digits:
                return int(digits[0])
    return 0


# ==================== 子评估函数 ====================

async def _evaluate_website(website: str | None, brand: str) -> dict:
    """评估官网健康度，返回 0-100 评分及详细指标。

    检查项：
    - 可访问性 (20分): HTTP 200 响应
    - HTTPS (15分): 使用安全协议
    - 响应速度 (10分): <1s 满分, <3s 得 5 分
    - 结构化数据 (25分): JSON-LD / Schema.org / Open Graph
    - 核心页面 (15分): 关于 / 产品 / 联系页面
    - 移动端适配 (15分): viewport meta 标签

    Args:
        website: 官网 URL（可能为空）。
        brand: 品牌名称，用于降级信息标记。

    Returns:
        包含 score (0-100) 和详细检查指标的字典。
        若官网不可访问，返回全零降级数据结构。
    """
    if not website:
        return {
            "score": 0,
            "url": None,
            "accessible": False,
            "hasHttps": False,
            "responseTimeMs": 0,
            "hasStructuredData": False,
            "structuredDataTypes": [],
            "hasAboutPage": False,
            "hasProductPage": False,
            "hasContactPage": False,
            "hasMobileViewport": False,
            "checks": {
                "accessibility": 0,
                "https": 0,
                "responseSpeed": 0,
                "structuredData": 0,
                "corePages": 0,
                "mobileViewport": 0,
            },
            "status": "missing_url",
        }

    url = _normalize_url(website)
    result: dict[str, Any] = {
        "score": 0,
        "url": url,
        "accessible": False,
        "hasHttps": False,
        "responseTimeMs": 0,
        "hasStructuredData": False,
        "structuredDataTypes": [],
        "hasAboutPage": False,
        "hasProductPage": False,
        "hasContactPage": False,
        "hasMobileViewport": False,
        "checks": {},
        "status": "unknown",
    }

    try:
        async with httpx.AsyncClient(
            timeout=DEFAULT_TIMEOUT,
            follow_redirects=True,
            headers={"User-Agent": USER_AGENT},
        ) as client:
            start_time = time.time()
            response = await client.get(url)
            response_time = (time.time() - start_time) * 1000
            result["responseTimeMs"] = round(response_time)

            # 1. 可访问性 (20分)
            result["accessible"] = response.status_code == 200
            access_score = 20 if response.status_code == 200 else 0

            # 2. HTTPS (15分)
            result["hasHttps"] = url.startswith("https://")
            https_score = 15 if result["hasHttps"] else 0

            # 3. 响应速度 (10分)
            if response_time < 1000:
                speed_score = 10
            elif response_time < 3000:
                speed_score = 5
            else:
                speed_score = 0

            # 4. 结构化数据 (25分)
            html = response.text
            structured_score = 0
            structured_types: list[str] = []

            # JSON-LD
            if "application/ld+json" in html:
                jsonld_types = re.findall(r'"@type"\s*:\s*"([^"]+)"', html)
                structured_types.extend(jsonld_types)
                if jsonld_types:
                    structured_score += 15

            # Schema.org 微数据
            schema_matches = re.findall(
                r'itemtype="[^"]*schema\.org/([^"]+)"', html, re.IGNORECASE
            )
            if schema_matches:
                structured_types.extend(schema_matches)
                if structured_score < 15:
                    structured_score = 10 if structured_score == 0 else structured_score

            # Open Graph / Twitter Card
            if "og:" in html or "twitter:" in html:
                structured_types.append("OpenGraph")
                if structured_score < 15:
                    structured_score = max(structured_score, 5)

            result["hasStructuredData"] = structured_score > 0
            result["structuredDataTypes"] = list(set(structured_types))[:5]

            # 5. 核心页面完整度 (15分)
            core_score = 0
            html_lower = html.lower()

            about_pattern = re.compile(
                r'href=["\'][^"\']*?(about|关于|guanyu|company|企业)[^"\']*?["\']',
                re.IGNORECASE,
            )
            if about_pattern.search(html_lower):
                result["hasAboutPage"] = True
                core_score += 5

            product_pattern = re.compile(
                r'href=["\'][^"\']*?(product|产品|chanpin|service|服务|solution|解决方案)[^"\']*?["\']',
                re.IGNORECASE,
            )
            if product_pattern.search(html_lower):
                result["hasProductPage"] = True
                core_score += 5

            contact_pattern = re.compile(
                r'href=["\'][^"\']*?(contact|联系|lianxi|support|支持|help|帮助)[^"\']*?["\']',
                re.IGNORECASE,
            )
            if contact_pattern.search(html_lower):
                result["hasContactPage"] = True
                core_score += 5

            # 6. 移动端适配 (15分)
            result["hasMobileViewport"] = (
                'name="viewport"' in html or "name='viewport'" in html
            )
            mobile_score = 15 if result["hasMobileViewport"] else 0

            # 计算总分
            total = (
                access_score + https_score + speed_score
                + structured_score + core_score + mobile_score
            )
            result["score"] = _clamp(total)
            result["checks"] = {
                "accessibility": access_score,
                "https": https_score,
                "responseSpeed": speed_score,
                "structuredData": structured_score,
                "corePages": core_score,
                "mobileViewport": mobile_score,
            }
            result["status"] = (
                "ok" if response.status_code == 200 else f"http_{response.status_code}"
            )

    except httpx.TimeoutException:
        result["status"] = "timeout"
    except httpx.ConnectError:
        result["status"] = "connection_error"
    except httpx.HTTPStatusError as e:
        result["status"] = f"http_error_{e.response.status_code}"
    except Exception as e:
        result["status"] = f"error: {type(e).__name__}"

    return result


async def _evaluate_social_media(brand: str) -> dict:
    """评估自媒体矩阵覆盖度。

    检查平台：微信公众号、抖音、小红书、知乎、B站。
    每个平台满分 20 分：账号存在得 10 分，近期活跃再加 10 分。

    评估方式：优先通过 LLM 辅助判断各平台账号存在性与活跃度；
    LLM 不可用时降级为数据缺失状态。

    Args:
        brand: 品牌名称。

    Returns:
        包含 score (0-100) 和各平台详细评估的字典。
    """
    valid_names = {p["name"] for p in _SOCIAL_PLATFORMS}
    max_possible = len(_SOCIAL_PLATFORMS) * 20
    platform_results: list[dict] = []
    total_score = 0

    # 使用 LLM 进行辅助评估
    prompt = (
        f'请评估品牌"{brand}"在以下社交媒体平台的官方账号存在情况和活跃度。'
        "请仅输出 JSON 格式，不要添加任何其他文字。\n\n"
        f'平台列表：{json.dumps([p["name"] for p in _SOCIAL_PLATFORMS], ensure_ascii=False)}\n\n'
        '输出格式：{"platforms": [{"name": "平台名称", "exists": true/false, "active": true/false, "note": "简要说明（可选）"}]}'
    )

    try:
        llm_response = await llm_chat(prompt, model="gpt-4o", response_format="json")
        if not llm_response or not llm_response.strip():
            raise ValueError("Empty LLM response")

        llm_data = json.loads(llm_response.strip())

        if "platforms" in llm_data and isinstance(llm_data["platforms"], list):
            for item in llm_data["platforms"]:
                name = item.get("name", "")
                if name not in valid_names:
                    continue

                exists = bool(item.get("exists", False))
                active = bool(item.get("active", False))
                score = (10 if exists else 0) + (10 if active else 0)
                total_score += score
                platform_results.append({
                    "platform": name,
                    "exists": exists,
                    "active": active,
                    "score": score,
                    "maxScore": 20,
                    "note": item.get("note", ""),
                })
    except Exception:
        # LLM 失败：不填充任何平台数据，后续降级处理
        pass

    # 降级：未评估到的平台标记为数据缺失
    evaluated_names = {p["platform"] for p in platform_results}
    for p in _SOCIAL_PLATFORMS:
        if p["name"] not in evaluated_names:
            platform_results.append({
                "platform": p["name"],
                "exists": None,
                "active": None,
                "score": 0,
                "maxScore": 20,
                "note": "数据暂缺",
            })

    normalized_score = round((total_score / max_possible) * 100) if max_possible > 0 else 0
    status = "llm_evaluated" if total_score > 0 else "degraded"

    return {
        "score": normalized_score,
        "rawScore": total_score,
        "maxPossible": max_possible,
        "platforms": platform_results,
        "status": status,
    }


async def _evaluate_authority_media(brand: str) -> dict:
    """评估权威媒体报道覆盖度。

    检查媒体：36氪、极客公园、虎嗅、DoNews、什么值得买、IT之家、钛媒体。
    按权重加权计算总分（0-100）：有报道即得基础分，报道质量修正系数为
    高(1.0) / 中(0.7) / 低(0.4)。

    评估方式：优先通过 LLM 辅助判断各媒体报道数量与质量；
    LLM 不可用时降级为数据缺失状态。

    Args:
        brand: 品牌名称。

    Returns:
        包含 score (0-100) 和各媒体详细评估的字典。
    """
    valid_names = {m["name"] for m in _AUTHORITY_MEDIA}
    weight_map = {m["name"]: m["weight"] for m in _AUTHORITY_MEDIA}
    media_results: list[dict] = []
    total_score = 0

    # 使用 LLM 进行辅助评估
    prompt = (
        f'请评估品牌"{brand}"在以下科技/消费媒体上的报道数量和质量。'
        "请仅输出 JSON 格式，不要添加任何其他文字。\n\n"
        f'媒体列表：{json.dumps([m["name"] for m in _AUTHORITY_MEDIA], ensure_ascii=False)}\n\n'
        '输出格式：{"media": [{"name": "媒体名称", "count": 0, "quality": "高/中/低/无"}]}'
    )

    try:
        llm_response = await llm_chat(prompt, model="gpt-4o", response_format="json")
        if not llm_response or not llm_response.strip():
            raise ValueError("Empty LLM response")

        llm_data = json.loads(llm_response.strip())

        if "media" in llm_data and isinstance(llm_data["media"], list):
            for item in llm_data["media"]:
                name = item.get("name", "")
                if name not in valid_names:
                    continue

                count = _extract_count(item.get("count", 0))
                quality = str(item.get("quality", "无")).strip()
                weight = weight_map.get(name, 0.1)

                if count > 0:
                    base_score = 100 * weight
                    if quality == "高":
                        multiplier = 1.0
                    elif quality == "中":
                        multiplier = 0.7
                    else:
                        multiplier = 0.4
                    score = round(base_score * multiplier)
                else:
                    score = 0

                total_score += score
                media_results.append({
                    "source": name,
                    "count": count,
                    "quality": quality,
                    "score": score,
                    "weight": weight,
                })
    except Exception:
        # LLM 失败：不填充任何媒体数据，后续降级处理
        pass

    # 降级：未评估到的媒体标记为数据缺失
    evaluated_names = {m["source"] for m in media_results}
    for m in _AUTHORITY_MEDIA:
        if m["name"] not in evaluated_names:
            media_results.append({
                "source": m["name"],
                "count": 0,
                "quality": "无",
                "score": 0,
                "weight": m["weight"],
            })

    total_score = _clamp(total_score, 0, 100)
    status = "llm_evaluated" if total_score > 0 else "degraded"

    return {
        "score": total_score,
        "media": media_results,
        "status": status,
    }


# ==================== 主接口 ====================

async def evaluate(brand: str, website: str | None) -> dict:
    """Stage 2 主函数：品牌基建评估。

    并行评估官网健康度、自媒体矩阵和权威媒体报道，
    按 40% / 35% / 25% 权重计算加权总分。

    任一子评估失败时，该维度得 0 分并标记降级状态，
    不会中断整个评估流程。

    Args:
        brand: 品牌名称。
        website: 官网 URL（可选，为空则官网维度评分为 0）。

    Returns:
        {
            "websiteScore": int,         # 0-100
            "socialMediaScore": int,     # 0-100
            "authorityMediaScore": int,  # 0-100
            "total": int,                # 加权总分 0-100
            "details": {
                "website": {...},        # 官网详细评估数据
                "socialMedia": {...},    # 自媒体详细评估数据
                "authorityMedia": {...}, # 权威媒体详细评估数据
            }
        }
    """
    # 并行执行三个子评估，允许个别任务失败
    website_result, social_result, media_result = await asyncio.gather(
        _evaluate_website(website, brand),
        _evaluate_social_media(brand),
        _evaluate_authority_media(brand),
        return_exceptions=True,
    )

    # 处理可能的异常（返回降级数据，不打断流程）
    if isinstance(website_result, Exception):
        website_result = {
            "score": 0,
            "url": website,
            "status": f"error: {type(website_result).__name__}",
            "checks": {},
        }
    if isinstance(social_result, Exception):
        social_result = {
            "score": 0,
            "platforms": [],
            "status": f"error: {type(social_result).__name__}",
        }
    if isinstance(media_result, Exception):
        media_result = {
            "score": 0,
            "media": [],
            "status": f"error: {type(media_result).__name__}",
        }

    # 提取各维度分数
    website_score = website_result.get("score", 0)
    social_score = social_result.get("score", 0)
    media_score = media_result.get("score", 0)

    # 计算加权总分：官网 40% + 自媒体 35% + 权威媒体 25%
    total = round(
        website_score * 0.40
        + social_score * 0.35
        + media_score * 0.25
    )

    return {
        "websiteScore": website_score,
        "socialMediaScore": social_score,
        "authorityMediaScore": media_score,
        "total": total,
        "details": {
            "website": website_result,
            "socialMedia": social_result,
            "authorityMedia": media_result,
        },
    }
