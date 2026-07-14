"""
utils/json_repair.py
===================

JSON 修复工具 — 处理多阶段数据合并时的常见格式问题。

修复策略：
1. 中文引号（" " / 「 」）替换为英文引号
2. 未转义的特殊字符（换行、制表符等）
3. 末尾多余逗号
4. 缺失的闭合括号
5. 缺失的必填字段填充默认值

该模块不依赖外部 HTTP 库，为纯计算工具，所有函数使用同步定义。
"""

from __future__ import annotations

import json
import re
from typing import Any


# ── 必填字段默认值映射（遵循 PRD 4.4 节规范） ──
_DEFAULT_REQUIRED_VALUES: dict[str, Any] = {
    "aivoScore.total": 0,
    "sentiment.negativeRate": -1,
    "competitors": [],
    "suggestions.actions": [],
}


def repair_json(data: dict) -> dict:
    """
    修复字典数据中的 JSON 格式问题，确保可序列化和反序列化。

    流程：
    1. 先尝试直接序列化 + 反序列化；若成功，直接返回原数据
    2. 否则将字典序列化为 JSON 字符串
    3. 修复字符串中的中文引号、未转义换行、末尾逗号等
    4. 重新解析为字典
    5. 填充缺失的必填字段默认值

    Args:
        data: 需要修复的字典数据（通常来自 LLM 生成或多阶段合并）。

    Returns:
        修复后的合法字典。若彻底失败则返回包含错误信息的部分结果，
        不会抛出未捕获的异常。
    """
    if not isinstance(data, dict):
        return {
            "error": f"Expected dict, got {type(data).__name__}",
            "partial_data": str(data)[:1000],
            "jsonRepairApplied": True,
        }

    # 快速路径：如果数据已经可正常序列化 / 反序列化，直接返回
    try:
        json_str = json.dumps(data, ensure_ascii=False, indent=2)
        parsed = json.loads(json_str)
        if isinstance(parsed, dict):
            # 仍然填充默认值，但标记为未修复
            parsed = _fill_required_defaults(parsed)
            parsed["jsonRepairApplied"] = False
            return parsed
    except (TypeError, ValueError, json.JSONDecodeError):
        pass  # 继续下面的修复流程

    # 步骤 1：序列化为 JSON 字符串（再次尝试，可能走不到这里）
    try:
        json_str = json.dumps(data, ensure_ascii=False, indent=2)
    except (TypeError, ValueError) as exc:
        # 尝试递归清理不可序列化对象
        cleaned = _sanitize_for_json(data)
        try:
            json_str = json.dumps(cleaned, ensure_ascii=False, indent=2)
        except (TypeError, ValueError) as exc2:
            return {
                "error": f"JSON serialization failed: {exc2}",
                "partial_data": str(data)[:1000],
                "jsonRepairApplied": True,
            }

    # 步骤 2：字符串级修复（只在必要时执行）
    json_str = _repair_chinese_quotes(json_str)
    json_str = _escape_unescaped_chars(json_str)
    json_str = _remove_trailing_commas(json_str)
    json_str = _fix_unbalanced_brackets(json_str)

    # 步骤 3：重新解析
    try:
        repaired = json.loads(json_str)
    except json.JSONDecodeError as exc:
        # 激进修复：截断到错误位置并补全结构
        json_str = _aggressive_repair(json_str, exc)
        try:
            repaired = json.loads(json_str)
        except json.JSONDecodeError as exc2:
            return {
                "error": f"JSON repair failed after aggressive repair: {exc2}",
                "partial_data": data,
                "jsonRepairApplied": True,
            }

    # 步骤 4：填充缺失的必填字段
    if isinstance(repaired, dict):
        repaired = _fill_required_defaults(repaired)
        repaired["jsonRepairApplied"] = True
    else:
        repaired = {
            "error": "Parsed JSON is not a dict",
            "partial_data": repaired,
            "jsonRepairApplied": True,
        }

    return repaired


def repair_json_str(raw_str: str) -> dict:
    """
    从原始字符串修复 JSON（常用于 LLM 返回的原始文本）。

    会移除 Markdown 代码块标记，然后进行常规修复。

    Args:
        raw_str: 可能包含格式错误的 JSON 字符串。

    Returns:
        解析后的合法字典。失败时返回包含错误信息的部分结果。
    """
    if not isinstance(raw_str, str):
        return {
            "error": f"Expected str, got {type(raw_str).__name__}",
            "partial_data": str(raw_str)[:1000],
            "jsonRepairApplied": True,
        }

    # 去除 Markdown 代码块
    cleaned_str = _strip_code_blocks(raw_str)

    # 字符串级修复
    cleaned_str = _repair_chinese_quotes(cleaned_str)
    cleaned_str = _escape_unescaped_chars(cleaned_str)
    cleaned_str = _remove_trailing_commas(cleaned_str)
    cleaned_str = _fix_unbalanced_brackets(cleaned_str)

    # 尝试解析
    try:
        parsed = json.loads(cleaned_str)
    except json.JSONDecodeError as exc:
        cleaned_str = _aggressive_repair(cleaned_str, exc)
        try:
            parsed = json.loads(cleaned_str)
        except json.JSONDecodeError as exc2:
            return {
                "error": f"JSON repair failed: {exc2}",
                "partial_data": raw_str[:2000],
                "jsonRepairApplied": True,
            }

    if isinstance(parsed, dict):
        parsed = _fill_required_defaults(parsed)
        parsed["jsonRepairApplied"] = True
        return parsed

    return {
        "error": "Parsed JSON is not a dict",
        "partial_data": parsed,
        "jsonRepairApplied": True,
    }


# ── 内部辅助函数 ──


def _repair_chinese_quotes(s: str) -> str:
    """
    将中文引号替换为英文引号。

    替换范围：
    - 中文双引号：左 " 和右 "
    - 中文单引号：' 和 '
    - 直角引号：「」和『』
    - 全角引号：＂ 和 ＇
    """
    s = s.replace("\"", '"').replace("\"", '"')
    s = s.replace("'", "'").replace("'", "'")
    s = s.replace("＂", '"').replace("＇", "'")
    s = s.replace("「", '"').replace("」", '"')
    s = s.replace("『", '"').replace("』", '"')
    return s


def _escape_unescaped_chars(s: str) -> str:
    """
    在 JSON 字符串值中转义未处理的换行符、回车和制表符。

    仅在双引号字符串内部进行转义，避免破坏 JSON 结构。
    正确处理转义序列（如 \\\", \\\"）以避免误判字符串边界。
    """
    result: list[str] = []
    i = 0
    in_string = False

    while i < len(s):
        char = s[i]

        if not in_string:
            if char == '"':
                in_string = True
            result.append(char)
            i += 1
            continue

        # 在字符串内部
        if char == "\\":
            # 转义序列：复制 \ 和下一个字符
            result.append(char)
            i += 1
            if i < len(s):
                result.append(s[i])
                i += 1
            continue

        if char == '"':
            # 非转义的引号，结束字符串
            in_string = False
            result.append(char)
            i += 1
            continue

        if char == "\n":
            result.append("\\n")
            i += 1
            continue

        if char == "\r":
            result.append("\\r")
            i += 1
            continue

        if char == "\t":
            result.append("\\t")
            i += 1
            continue

        result.append(char)
        i += 1

    return "".join(result)


def _remove_trailing_commas(s: str) -> str:
    """
    移除对象或数组末尾的冗余逗号。

    例如：{"a": 1,} → {"a": 1}，[1, 2,] → [1, 2]
    """
    # 重复执行直到没有变化，处理嵌套末尾逗号
    prev = None
    while prev != s:
        prev = s
        s = re.sub(r",(\s*[}\]])", r"\1", s)
    return s


def _fix_unbalanced_brackets(s: str) -> str:
    """
    检测并补全缺失的闭合括号。

    使用状态机扫描，仅在字符串外部计数 { } 和 [ ]。
    如果括号不匹配，则在末尾补全缺失的闭合括号。
    """
    open_braces = 0
    open_brackets = 0
    in_string = False
    i = 0

    while i < len(s):
        char = s[i]

        if char == "\\" and in_string:
            # 跳过转义序列（反斜杠 + 下一个字符）
            i += 2
            continue

        if char == '"':
            in_string = not in_string
            i += 1
            continue

        if in_string:
            i += 1
            continue

        # 在字符串外部
        if char == "{":
            open_braces += 1
        elif char == "}":
            open_braces -= 1
        elif char == "[":
            open_brackets += 1
        elif char == "]":
            open_brackets -= 1

        i += 1

    # 补全缺失的括号
    if open_braces > 0:
        s += "}" * open_braces
    if open_brackets > 0:
        s += "]" * open_brackets

    # 如果闭合括号过多，尝试截断到有效结构
    if open_braces < 0 or open_brackets < 0:
        s = _truncate_to_valid_json(s)

    return s


def _truncate_to_valid_json(s: str) -> str:
    """
    如果闭合括号过多，从末尾开始尝试截断到有效的 JSON 结构。
    """
    # 先尝试去掉末尾多余的闭合括号
    stripped = s.rstrip()
    while stripped and stripped[-1] in "}]":
        stripped = stripped[:-1].rstrip()
        try:
            json.loads(stripped)
            return stripped
        except json.JSONDecodeError:
            continue

    # 如果还是不行，从后往前逐字符尝试
    for i in range(len(s), 0, -1):
        try:
            json.loads(s[:i])
            return s[:i]
        except json.JSONDecodeError:
            continue
    return s


def _aggressive_repair(s: str, exc: json.JSONDecodeError | None = None) -> str:
    """
    激进修复策略：当常规修复失败时尝试。

    1. 截断到错误位置之前的最近有效结构
    2. 补全缺失的括号
    3. 移除末尾逗号
    """
    if exc is not None and exc.lineno is not None and exc.colno is not None:
        lines = s.split("\n")
        if 1 <= exc.lineno <= len(lines):
            error_line = lines[exc.lineno - 1]
            # 截断到错误列之前
            if exc.colno > 1:
                lines[exc.lineno - 1] = error_line[: exc.colno - 1]
            else:
                lines = lines[: exc.lineno - 1]
            s = "\n".join(lines)

    # 补全括号
    s = _fix_unbalanced_brackets(s)
    # 移除末尾逗号
    s = _remove_trailing_commas(s)

    # 如果字符串不以 { 或 [ 开头，尝试提取第一个 JSON 结构
    s = s.strip()
    if not (s.startswith("{") or s.startswith("[")):
        first_brace = s.find("{")
        first_bracket = s.find("[")
        starts = [x for x in (first_brace, first_bracket) if x != -1]
        if starts:
            s = s[min(starts):]

    return s


def _strip_code_blocks(s: str) -> str:
    """移除 Markdown 代码块标记（如 ```json ... ```）。"""
    s = s.strip()
    if s.startswith("```json"):
        s = s[7:]
    elif s.startswith("```"):
        s = s[3:]
    if s.endswith("```"):
        s = s[:-3]
    return s.strip()


def _sanitize_for_json(data: Any) -> Any:
    """递归清理数据，确保所有内容可 JSON 序列化（去除非标准类型）。"""
    if isinstance(data, dict):
        return {k: _sanitize_for_json(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [_sanitize_for_json(item) for item in data]
    elif isinstance(data, (str, int, float, bool, type(None))):
        return data
    else:
        return str(data)


def _fill_required_defaults(data: dict) -> dict:
    """填充 PRD 中定义的缺失必填字段默认值。"""
    # aivoScore.total
    if "aivoScore" in data and isinstance(data.get("aivoScore"), dict):
        if "total" not in data["aivoScore"]:
            data["aivoScore"]["total"] = 0

    # sentiment.negativeRate
    if "sentiment" in data and isinstance(data.get("sentiment"), dict):
        if "negativeRate" not in data["sentiment"]:
            data["sentiment"]["negativeRate"] = -1

    # competitors
    if "competitors" not in data:
        data["competitors"] = []

    # suggestions.actions
    if "suggestions" in data and isinstance(data.get("suggestions"), dict):
        if "actions" not in data["suggestions"]:
            data["suggestions"]["actions"] = []

    return data
