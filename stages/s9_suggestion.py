"""阶段 9：建议系统 — 基于诊断数据生成可执行优化建议体系

Stage 9 接收前序阶段（AIVO 评分、基建评估、舆情扫描）的产出，通过规则引擎
生成可落地的优化建议、优先级排序、Quick Wins、三阶段路线图和得分预测。

接口约定：
    def generate(aivo_score: dict, infra_eval: dict, sentiment: dict) -> dict

返回结构：
    {
        "priorityActions": [...],   # 高优先级行动（最多 3 条）
        "suggestions": [...],      # 完整建议列表（按优先级排序）
        "quickWins": [...],        # 低投入高回报项
        "roadmap": {               # 三阶段路线图
            "P1": [...], "P2": [...], "P3": [...]
        },
        "scoreProjection": {       # 得分预测
            "current": int,
            "projected": int,
            "dimensionProjections": [...]
        }
    }
"""

from typing import Any


# ===== 辅助函数 =====


def _get_dim_score(dimensions: list[dict], code: str) -> int:
    """从维度列表中安全获取指定维度的得分。

    Args:
        dimensions: AIVO 评分中的 dimensions 列表。
        code: 维度代码，如 ``"AI_SEARCH_VISIBILITY"``。

    Returns:
        该维度的得分，未找到则返回 ``0``。
    """
    for dim in dimensions:
        if dim.get("code") == code:
            return dim.get("score", 0)
    return 0


def _get_infra_detail(infra_eval: dict, *path: str) -> Any:
    """安全地从基建评估 details 中按键路径获取嵌套值。

    Args:
        infra_eval: 基建评估结果字典，期望包含 ``details`` 键。
        *path: 键路径，如 ``("website", "schemaMarkup")``。

    Returns:
        路径对应的值，路径不存在或中间节点非字典则返回 ``None``。
    """
    data = infra_eval.get("details", {})
    for key in path:
        if not isinstance(data, dict):
            return None
        data = data.get(key)
    return data


def _determine_priority(impact_level: str, effort_level: str) -> str:
    """根据影响程度与实施难度判定建议优先级。

    规则（与 PRD 对齐）：
    - **高**：impactLevel = "高" 且 effortLevel ≠ "heavy"
    - **中**：impactLevel = "中" 或 (impactLevel = "高" 且 effortLevel = "heavy")
    - **低**：impactLevel = "低" 或 effortLevel = "heavy"（且 impactLevel ≠ "高"）

    Args:
        impact_level: 影响程度，取值 ``"高"`` / ``"中"`` / ``"低"``。
        effort_level: 实施难度，取值 ``"quick_win"`` / ``"moderate"`` / ``"heavy"``。

    Returns:
        优先级字符串 ``"高"`` / ``"中"`` / ``"低"``。
    """
    if impact_level == "高" and effort_level != "heavy":
        return "高"
    if impact_level == "中" or (impact_level == "高" and effort_level == "heavy"):
        return "中"
    return "低"


# ===== 规则引擎：按诊断维度生成建议 =====


def _generate_dimension_suggestions(aivo_score: dict) -> list[dict]:
    """基于 AIVO 各维度得分生成系统性改进建议。

    触发规则：维度得分 < 70 时生成该维度对应的改进建议。

    Args:
        aivo_score: AIVO 评分结果，需包含 ``dimensions`` 列表。

    Returns:
        系统性改进建议列表，每项为符合 7 属性标准的字典。
    """
    dimensions = aivo_score.get("dimensions", [])
    suggestions: list[dict] = []

    dim_templates: dict[str, dict] = {
        "AI_SEARCH_VISIBILITY": {
            "category": "内容优化",
            "title": "提升 AI 搜索平台品牌提及率",
            "description": (
                "品牌在 AI 搜索中的可见度不足，建议围绕核心产品词和用户需求场景，"
                "在官网、自媒体和权威媒体中布局高质量内容，提升 AI 平台引用概率。"
                "重点优化 FAQ、产品对比、使用场景等结构化内容。"
            ),
            "impactLevel": "高",
            "effortLevel": "moderate",
            "timeline": "2-4 周",
            "expectedImprovement": 8,
            "responsibleParty": "内容运营 / SEO 团队",
        },
        "INFRA_COMPLETENESS": {
            "category": "基建升级",
            "title": "补齐品牌数字基础设施短板",
            "description": (
                "品牌基建完善度较低，官网、自媒体矩阵或权威媒体覆盖存在不足。"
                "建议优先补齐缺失的基建模块，确保 AI 平台能获取完整、准确的品牌信息。"
            ),
            "impactLevel": "高",
            "effortLevel": "moderate",
            "timeline": "1-3 月",
            "expectedImprovement": 10,
            "responsibleParty": "技术团队 / 品牌运营",
        },
        "COMPETITIVE_ADVANTAGE": {
            "category": "竞争策略",
            "title": "缩小与竞品在 AI 搜索中的差距",
            "description": (
                "品牌在竞品对比中处于劣势，建议对标行业领先竞品，"
                "分析其内容策略和基建布局，制定差异化赶超方案。"
                "重点关注竞品在 AI 搜索中高频出现的内容类型。"
            ),
            "impactLevel": "高",
            "effortLevel": "heavy",
            "timeline": "3-6 月",
            "expectedImprovement": 12,
            "responsibleParty": "市场战略 / 品牌负责人",
        },
        "SENTIMENT_HEALTH": {
            "category": "舆情管理",
            "title": "改善品牌舆情健康度",
            "description": (
                "品牌舆情健康度偏低，负面信息可能影响 AI 平台对品牌的推荐意愿。"
                "建议建立舆情监测和快速响应机制，主动管理用户口碑，增加正面声量。"
            ),
            "impactLevel": "高",
            "effortLevel": "moderate",
            "timeline": "1-3 月",
            "expectedImprovement": 8,
            "responsibleParty": "公关 / 用户运营团队",
        },
    }

    for code, template in dim_templates.items():
        score = _get_dim_score(dimensions, code)
        if score < 70:
            priority = _determine_priority(
                template["impactLevel"], template["effortLevel"]
            )
            suggestions.append(
                {
                    "id": f"SUGG-{len(suggestions) + 1:03d}",
                    "priority": priority,
                    "category": template["category"],
                    "dimension": code,
                    "title": template["title"],
                    "description": template["description"],
                    "impactLevel": template["impactLevel"],
                    "effortLevel": template["effortLevel"],
                    "timeline": template["timeline"],
                    "expectedImprovement": template["expectedImprovement"],
                    "responsibleParty": template["responsibleParty"],
                }
            )

    return suggestions


def _generate_infra_fix_suggestions(infra_eval: dict) -> list[dict]:
    """基于基建评估具体检查项生成修复建议。

    触发规则：
    - 官网缺少结构化数据标记 → 添加 Schema.org
    - 官网未启用 HTTPS → 配置 SSL
    - 官网移动端不适配 → 响应式改造
    - 自媒体平台缺失 → 补齐官方账号
    - 权威媒体报道 < 3 篇 → 加强媒体合作

    Args:
        infra_eval: 基建评估结果，需包含 ``details`` 嵌套结构。

    Returns:
        基建修复建议列表。
    """
    suggestions: list[dict] = []

    # 1. 结构化数据标记
    if _get_infra_detail(infra_eval, "website", "schemaMarkup") is False:
        suggestions.append(
            {
                "id": "SUGG-INF-001",
                "priority": "高",
                "category": "基建升级",
                "dimension": "INFRA_COMPLETENESS",
                "title": "官网添加结构化数据标记（Schema.org）",
                "description": (
                    "当前官网缺少 Schema.org 结构化数据，导致 AI 平台难以准确解析品牌信息。"
                    "建议在产品页添加 Product 类型的 JSON-LD 标记，包含品牌、价格、评分等字段。"
                ),
                "impactLevel": "高",
                "effortLevel": "quick_win",
                "timeline": "1-2 周",
                "expectedImprovement": 5,
                "responsibleParty": "技术团队 / 前端开发",
            }
        )

    # 2. HTTPS
    if _get_infra_detail(infra_eval, "website", "https") is False:
        suggestions.append(
            {
                "id": "SUGG-INF-002",
                "priority": "高",
                "category": "基建升级",
                "dimension": "INFRA_COMPLETENESS",
                "title": "启用官网 HTTPS 安全协议",
                "description": (
                    "官网未启用 HTTPS，影响用户信任度和 AI 平台收录权重。"
                    "建议尽快配置 SSL 证书，全站强制跳转 HTTPS。"
                ),
                "impactLevel": "高",
                "effortLevel": "quick_win",
                "timeline": "1 周内",
                "expectedImprovement": 3,
                "responsibleParty": "技术团队 / 运维",
            }
        )

    # 3. 移动端适配
    if _get_infra_detail(infra_eval, "website", "mobileFriendly") is False:
        suggestions.append(
            {
                "id": "SUGG-INF-003",
                "priority": "中",
                "category": "基建升级",
                "dimension": "INFRA_COMPLETENESS",
                "title": "优化官网移动端适配",
                "description": (
                    "官网在移动设备上的体验不佳，可能影响 AI 平台对网站质量的评估。"
                    "建议采用响应式设计，优化移动端加载速度和交互体验。"
                ),
                "impactLevel": "中",
                "effortLevel": "moderate",
                "timeline": "2-4 周",
                "expectedImprovement": 4,
                "responsibleParty": "技术团队 / 前端开发",
            }
        )

    # 4. 自媒体矩阵
    social_media = _get_infra_detail(infra_eval, "socialMedia")
    if isinstance(social_media, dict):
        missing_platforms = [
            name for name, present in social_media.items() if present is False
        ]
        if missing_platforms:
            display = ", ".join(missing_platforms[:3])
            suggestions.append(
                {
                    "id": "SUGG-INF-004",
                    "priority": "中",
                    "category": "基建升级",
                    "dimension": "INFRA_COMPLETENESS",
                    "title": f"补齐自媒体平台矩阵：{display} 等",
                    "description": (
                        f"品牌在以下自媒体平台尚未建立官方账号：{display}。"
                        "建议尽快注册并认证官方账号，定期发布品牌内容，扩大 AI 平台信息来源。"
                    ),
                    "impactLevel": "中",
                    "effortLevel": "moderate",
                    "timeline": "2-4 周",
                    "expectedImprovement": 6,
                    "responsibleParty": "品牌运营 / 社媒团队",
                }
            )

    # 5. 权威媒体覆盖
    authority = _get_infra_detail(infra_eval, "authorityMedia")
    if isinstance(authority, dict):
        count = authority.get("count", 0)
        if count < 3:
            suggestions.append(
                {
                    "id": "SUGG-INF-005",
                    "priority": "中",
                    "category": "媒体关系",
                    "dimension": "INFRA_COMPLETENESS",
                    "title": "增加权威媒体报道覆盖",
                    "description": (
                        f"品牌当前权威媒体报道数量较少（{count} 篇），"
                        "难以支撑 AI 平台对品牌权威性的判断。"
                        "建议与 36 氪、极客公园、DoNews 等行业媒体建立合作，"
                        "争取评测和报道机会。"
                    ),
                    "impactLevel": "中",
                    "effortLevel": "moderate",
                    "timeline": "1-3 月",
                    "expectedImprovement": 5,
                    "responsibleParty": "公关 / 媒体关系团队",
                }
            )

    return suggestions


def _generate_sentiment_suggestions(sentiment: dict) -> list[dict]:
    """基于舆情扫描结果生成舆情管理建议。

    触发规则：
    - 负面率 > 20% 或风险等级为 ``"中风险"`` / ``"高风险"`` → 建立快速响应机制
    - 存在具体负面来源 → 针对性处理
    - 负面率 > 30% → 启动口碑修复专项

    Args:
        sentiment: 舆情扫描结果，需包含 ``negativeRate``、``riskLevel`` 等键。

    Returns:
        舆情管理建议列表。
    """
    suggestions: list[dict] = []
    negative_rate = sentiment.get("negativeRate", 0)
    risk_level = sentiment.get("riskLevel", "低风险")

    # 1. 快速响应机制（负面率 > 20% 或中/高风险）
    if negative_rate > 20 or risk_level in ("中风险", "高风险"):
        suggestions.append(
            {
                "id": "SUGG-SEN-001",
                "priority": "高",
                "category": "舆情管理",
                "dimension": "SENTIMENT_HEALTH",
                "title": "建立负面舆情快速响应机制",
                "description": (
                    f"品牌负面率已达 {negative_rate:.1f}%（{risk_level}），"
                    "可能影响 AI 平台推荐意愿。"
                    "建议建立 7×24 小时舆情监测，针对黑猫投诉、社交媒体等平台的"
                    "负面信息制定快速响应 SOP。"
                ),
                "impactLevel": "高",
                "effortLevel": "moderate",
                "timeline": "1-2 月",
                "expectedImprovement": 10,
                "responsibleParty": "公关 / 用户运营团队",
            }
        )

        # 2. 针对性处理（如有具体负面来源）
        negative_sources = sentiment.get("negativeSources", [])
        if negative_sources:
            top = negative_sources[0]
            platform = top.get("platform", "相关平台")
            issue = top.get("issue", "负面反馈")
            suggestions.append(
                {
                    "id": "SUGG-SEN-002",
                    "priority": "中",
                    "category": "舆情管理",
                    "dimension": "SENTIMENT_HEALTH",
                    "title": f"重点处理 {platform} 上的 {issue} 问题",
                    "description": (
                        f"{platform} 上存在较多关于“{issue}”的负面反馈，"
                        "建议主动联系平台用户，提供解决方案并引导正面评价。"
                    ),
                    "impactLevel": "中",
                    "effortLevel": "moderate",
                    "timeline": "2-4 周",
                    "expectedImprovement": 5,
                    "responsibleParty": "用户运营 / 客服团队",
                }
            )

    # 3. 口碑修复专项（负面率 > 30%）
    if negative_rate > 30:
        suggestions.append(
            {
                "id": "SUGG-SEN-003",
                "priority": "高",
                "category": "舆情管理",
                "dimension": "SENTIMENT_HEALTH",
                "title": "启动品牌口碑修复专项",
                "description": (
                    "负面率超过 30%（高风险），品牌口碑已处于危机边缘。"
                    "建议启动专项修复计划，包括：高层公开回应、核心用户一对一沟通、"
                    "权威媒体正面发声、产品体验改进等组合拳。"
                ),
                "impactLevel": "高",
                "effortLevel": "heavy",
                "timeline": "3-6 月",
                "expectedImprovement": 15,
                "responsibleParty": "品牌总监 / 公关团队",
            }
        )

    return suggestions


# ===== 得分预测与路线图构建 =====


def _calculate_projections(aivo_score: dict, all_suggestions: list[dict]) -> dict:
    """计算执行建议后的得分预测。

    预测逻辑（与 PRD 对齐）：
    - 按维度分组，取该维度下最高的 ``expectedImprovement``
    - 同一维度多条建议不重复累加，单维度提升上限 30 分
    - 总分预测 = min(100, 当前总分 + 各维度最高提升之和)

    Args:
        aivo_score: AIVO 评分结果，需包含 ``total`` 和 ``dimensions``。
        all_suggestions: 全部建议列表。

    Returns:
        得分预测字典，包含 ``current``、``projected``、``dimensionProjections``。
    """
    current_total = aivo_score.get("total", 0)
    dimensions = aivo_score.get("dimensions", [])

    # 按维度取最高提升值
    dim_improvements: dict[str, float] = {}
    for sugg in all_suggestions:
        dim = sugg.get("dimension", "OTHER")
        improvement = float(sugg.get("expectedImprovement", 0))
        dim_improvements[dim] = max(dim_improvements.get(dim, 0.0), improvement)

    # 各维度预测
    dimension_projections: list[dict] = []
    total_projection = 0.0

    for dim in dimensions:
        code = dim.get("code", "UNKNOWN")
        current = dim.get("score", 0)
        improvement = min(dim_improvements.get(code, 0.0), 30.0)  # 单维度上限 30
        projected = min(100, current + improvement)
        total_projection += improvement
        dimension_projections.append(
            {
                "code": code,
                "name": dim.get("name", code),
                "current": current,
                "projected": round(projected),
                "improvement": round(improvement),
            }
        )

    projected_total = min(100, current_total + round(total_projection))

    return {
        "current": current_total,
        "projected": projected_total,
        "improvement": projected_total - current_total,
        "dimensionProjections": dimension_projections,
    }


def _build_roadmap(all_suggestions: list[dict]) -> dict[str, list[str]]:
    """构建三阶段优化路线图。

    阶段划分（与 PRD 对齐）：
    - **P1 即时**（0-4 周）：quick_win 或 timeline 含 "周"
    - **P2 短期**（1-3 月）：timeline 含 "月" 且 effort 非 heavy
    - **P3 长期**（3-6 月）：timeline 含 "月" 且 effort 为 heavy，或 timeline > 3 月

    Args:
        all_suggestions: 全部建议列表。

    Returns:
        三阶段路线图字典，键为 ``"P1"`` / ``"P2"`` / ``"P3"``。
    """
    p1_items: list[str] = []
    p2_items: list[str] = []
    p3_items: list[str] = []

    for sugg in all_suggestions:
        effort = sugg.get("effortLevel", "moderate")
        timeline = sugg.get("timeline", "2-4 周")
        title = sugg.get("title", "")

        if effort == "quick_win" or "周" in timeline:
            p1_items.append(title)
        elif "月" in timeline and effort != "heavy":
            p2_items.append(title)
        else:
            p3_items.append(title)

    # 去重并保持顺序，每阶段最多 5 条
    def _unique_limit(items: list[str], limit: int = 5) -> list[str]:
        seen: set[str] = set()
        result: list[str] = []
        for item in items:
            if item not in seen:
                seen.add(item)
                result.append(item)
                if len(result) >= limit:
                    break
        return result

    p1 = _unique_limit(p1_items)
    p2 = _unique_limit(p2_items)
    p3 = _unique_limit(p3_items)

    # 兜底：若某阶段为空，填充默认项
    if not p1:
        p1 = ["完善官网基础信息"]
    if not p2:
        p2 = ["建立内容运营规范"]
    if not p3:
        p3 = ["构建品牌长期 GEO 策略"]

    return {"P1": p1, "P2": p2, "P3": p3}


# ===== 主入口 =====


def generate(aivo_score: dict, infra_eval: dict, sentiment: dict) -> dict:
    """生成基于诊断数据的优化建议体系。

    基于 AIVO 评分、基建评估和舆情扫描结果，通过规则引擎生成：

    - **优先级行动清单**：按 ``impactLevel × effortLevel`` 矩阵排序的高优先级行动
    - **完整建议列表**：包含维度改进、基建修复、舆情管理三大类
    - **Quick Wins**：低投入高回报（effortLevel = ``"quick_win"``）项
    - **三阶段路线图**：P1（即时 0-4 周）、P2（短期 1-3 月）、P3（长期 3-6 月）
    - **得分预测**：当前分 → 执行建议后预期得分，含各维度分解

    建议生成规则（与 PRD 对齐）：
    1. 维度得分 < 70 → 该维度系统性改进建议
    2. 基建检查项缺失 → 具体修复项（结构化数据、HTTPS、移动端、自媒体、权威媒体）
    3. 负面率 > 20% 或风险等级中/高 → 舆情管理建议
    4. 综合影响程度和实施难度计算优先级

    降级策略：
    - 若输入数据异常或处理过程中出错，返回空建议体系 + 降级标记，不打断主流程。

    Args:
        aivo_score: AIVO 评分结果，包含 ``total``、``grade``、``dimensions``、
            ``nextTierGap``、``nextTierTarget`` 等。
        infra_eval: 基建评估结果，包含 ``websiteScore``、``socialMediaScore``、
            ``authorityMediaScore``、``total``、``details`` 等。
        sentiment: 舆情扫描结果，包含 ``negativeRate``、``riskLevel``、
            ``sentimentDistribution``、``topIssues``、``negativeSources``、
            ``positiveSources`` 等。

    Returns:
        建议体系字典，结构如下：

        .. code-block:: python

            {
                "priorityActions": [
                    {
                        "id": str,
                        "title": str,
                        "priority": str,
                        "category": str,
                        "dimension": str,
                        "timeline": str,
                        "expectedImprovement": int,
                        "description": str,
                    }
                ],
                "suggestions": [
                    {
                        "id": str,
                        "priority": str,
                        "category": str,
                        "dimension": str,
                        "title": str,
                        "description": str,
                        "impactLevel": str,
                        "effortLevel": str,
                        "timeline": str,
                        "expectedImprovement": int,
                        "responsibleParty": str,
                    }
                ],
                "quickWins": [
                    {
                        "id": str,
                        "title": str,
                        "description": str,
                        "effort": str,
                        "timeline": str,
                        "expectedImprovement": int,
                    }
                ],
                "roadmap": {
                    "P1": [str, ...],
                    "P2": [str, ...],
                    "P3": [str, ...],
                },
                "scoreProjection": {
                    "current": int,
                    "projected": int,
                    "dimensionProjections": [
                        {
                            "code": str,
                            "name": str,
                            "current": int,
                            "projected": int,
                            "improvement": int,
                        }
                    ],
                },
            }
    """
    try:
        # 1. 生成各维度系统性建议
        dim_suggestions = _generate_dimension_suggestions(aivo_score)

        # 2. 生成基建修复建议
        infra_suggestions = _generate_infra_fix_suggestions(infra_eval)

        # 3. 生成舆情管理建议
        sentiment_suggestions = _generate_sentiment_suggestions(sentiment)

        # 合并所有建议
        all_suggestions = dim_suggestions + infra_suggestions + sentiment_suggestions

        # 4. 排序：高优先级在前，同优先级按 expectedImprovement 降序
        priority_order = {"高": 0, "中": 1, "低": 2}
        all_suggestions.sort(
            key=lambda x: (
                priority_order.get(x.get("priority", "低"), 2),
                -x.get("expectedImprovement", 0),
            )
        )

        # 重新分配连续 ID
        for idx, sugg in enumerate(all_suggestions, start=1):
            sugg["id"] = f"SUGG-{idx:03d}"

        # 5. 提取优先级行动（高优先级，最多 3 条）
        priority_actions = [
            {
                "id": s["id"],
                "title": s["title"],
                "priority": s["priority"],
                "category": s["category"],
                "dimension": s["dimension"],
                "timeline": s["timeline"],
                "expectedImprovement": s["expectedImprovement"],
                "description": s["description"],
            }
            for s in all_suggestions
            if s["priority"] == "高"
        ][:3]

        # 6. 提取 Quick Wins（低投入高回报）
        quick_wins = [
            {
                "id": s["id"],
                "title": s["title"],
                "description": s["description"],
                "effort": s["effortLevel"],
                "timeline": s["timeline"],
                "expectedImprovement": s["expectedImprovement"],
            }
            for s in all_suggestions
            if s.get("effortLevel") == "quick_win"
        ]

        # 7. 构建三阶段路线图
        roadmap = _build_roadmap(all_suggestions)

        # 8. 计算得分预测
        score_projection = _calculate_projections(aivo_score, all_suggestions)

        return {
            "priorityActions": priority_actions,
            "suggestions": all_suggestions,
            "quickWins": quick_wins,
            "roadmap": roadmap,
            "scoreProjection": score_projection,
        }

    except Exception as e:
        # 降级策略：返回空建议体系 + 降级标记，确保不打断主流程
        current_score = (
            aivo_score.get("total", 0) if isinstance(aivo_score, dict) else 0
        )
        return {
            "priorityActions": [],
            "suggestions": [],
            "quickWins": [],
            "roadmap": {
                "P1": ["完善品牌基础信息"],
                "P2": ["建立内容运营体系"],
                "P3": ["构建长期 GEO 策略"],
            },
            "scoreProjection": {
                "current": current_score,
                "projected": current_score,
                "dimensionProjections": [],
            },
            "error": str(e),
            "dataQuality": "degraded",
        }
