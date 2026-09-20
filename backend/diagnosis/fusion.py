"""诊断融合模块。

职责：将「视觉结果 + 工艺参数规则」融合为最终诊断结果。

规则约定：
- 视觉模型成功识别缺陷时，以视觉结论作为主要证据（主缺陷）；
- 工艺规则负责判断该缺陷在当前参数下是否合理（规则结论是否一致）；
- 视觉与规则一致 → 提高综合置信度；
- 视觉与规则冲突 → 不强行覆盖视觉结论，返回 warning；
- 规则评分统一命名为 risk_score，不称为“概率”。

公开接口：
- fuse_diagnosis(vision_result, rule_result)：带视觉的融合诊断；
- rule_only_diagnosis(rule_result)：纯规则回退（V0.2 逻辑）。
"""

from typing import List, Optional

from rules import petg_rules

SEVERITY_ORDER = {"low": 0, "medium": 1, "high": 2}

# 视觉模型可识别的缺陷（unknown 视为不可用，回退规则）
VISION_DEFECTS = {"stringing", "under_extrusion", "first_layer_issue"}

# 视觉服务失败 / 未配置的状态
VISION_UNAVAILABLE_STATUSES = {"vision_not_configured", "vision_error"}

# 视觉失败原因码 → 中文说明（仅用于展示 warning，不新增数据库字段）
VISION_REASON_LABELS = {
    "timeout": "请求超时",
    "network_error": "网络异常",
    "http_4xx": "服务请求失败",
    "http_5xx": "服务端异常",
    "invalid_model_response": "模型返回格式异常",
    "json_parse_error": "模型结果解析失败",
    "analysis_failed": "视觉分析异常",
    "image_not_found": "图片不存在",
    "unsupported_image_type": "图片格式不支持",
    "image_read_failed": "图片读取失败",
    "empty_image": "图片内容为空",
    "vision_adapter_not_implemented": "视觉适配器未实现",
}

UNKNOWN_DEFECT_WARNING = (
    "视觉模型已返回结果，但无法归类为当前支持的缺陷类型，已回退到工艺参数规则诊断。"
)

CONSISTENCY_BONUS = 0.05


def _clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, value))


def _to_risk_causes(causes: Optional[List[dict]]) -> List[dict]:
    """将规则原因转换为统一结构：cause + risk_score（保留 score 兼容旧前端）。"""
    result = []
    for item in causes or []:
        if not isinstance(item, dict):
            continue
        raw = item.get("risk_score", item.get("score", 0.0))
        try:
            risk = round(float(raw), 2)
        except (TypeError, ValueError):
            risk = 0.0
        result.append(
            {
                "cause": item.get("cause", ""),
                "risk_score": risk,
                "score": risk,
            }
        )
    return result


def _more_severe(a: Optional[str], b: Optional[str]) -> str:
    a = a if a in SEVERITY_ORDER else "low"
    b = b if b in SEVERITY_ORDER else "low"
    return a if SEVERITY_ORDER[a] >= SEVERITY_ORDER[b] else b


def _vision_defect(vision_result: Optional[dict]) -> Optional[str]:
    """提取可用的视觉缺陷；不可用（未配置 / 失败 / unknown）时返回 None。"""
    if not isinstance(vision_result, dict):
        return None
    if vision_result.get("status") in VISION_UNAVAILABLE_STATUSES:
        return None
    defect = str(vision_result.get("defect", "")).strip().lower()
    return defect if defect in VISION_DEFECTS else None


def _vision_evidence(vision_result: dict) -> List[str]:
    evidence = vision_result.get("visual_evidence") or []
    if isinstance(evidence, str):
        evidence = [evidence]
    if not isinstance(evidence, list):
        return []
    return [str(item).strip() for item in evidence if str(item).strip()]


def _confidence(vision_result: dict) -> float:
    try:
        value = float(vision_result.get("confidence", 0.0))
    except (TypeError, ValueError):
        value = 0.0
    return round(_clamp(value), 2)


def _rule_label(rule_result: dict) -> str:
    defect = rule_result.get("defect", "")
    return rule_result.get("defect_label") or petg_rules.DEFECT_LABELS.get(defect, defect)


def rule_only_diagnosis(rule_result: dict, warning: Optional[str] = None) -> dict:
    """纯规则诊断结果（V0.2 逻辑），输出统一结构。"""
    return {
        "defect": rule_result.get("defect"),
        "defect_label": _rule_label(rule_result),
        "severity": rule_result.get("severity"),
        "confidence": None,
        "visual_evidence": [],
        "possible_causes": _to_risk_causes(rule_result.get("possible_causes")),
        "recommended_parameters": rule_result.get("recommended_parameters"),
        "warning": warning,
        "explanation": rule_result.get("explanation", ""),
        "fallback_used": True,
        "fallback_type": "rule_based",
        "fallback_reason": None,
    }


def _build_explanation(
    defect_label: str,
    evidence: List[str],
    consistent: bool,
    rule_explanation: str,
) -> str:
    if evidence:
        vision_part = f"视觉分析显示：{'、'.join(evidence)}。"
    else:
        vision_part = "视觉分析未提供具体证据。"

    if consistent:
        consistency_part = "该结论与当前工艺参数规则一致，综合置信度已相应提高。"
    else:
        consistency_part = "视觉结论与工艺参数规则不完全一致，请结合实物进一步复核。"

    return (
        f"综合视觉与工艺参数，主要缺陷判定为“{defect_label}”。"
        f"{vision_part}{consistency_part}{rule_explanation}"
    )


def _vision_fallback_warning(vision_result: Optional[dict]) -> Optional[str]:
    """根据视觉结果状态给出可区分的中文回退提示。"""
    if not isinstance(vision_result, dict):
        return "视觉分析不可用，已回退到工艺参数规则诊断。"

    status = vision_result.get("status")
    if status == "vision_error":
        reason = str(vision_result.get("reason") or "analysis_failed")
        label = VISION_REASON_LABELS.get(reason, reason)
        return f"视觉分析不可用（原因：{label}），已回退到工艺参数规则诊断。"
    if status == "vision_not_configured":
        return "视觉模型未配置，已回退到工艺参数规则诊断。"

    # 视觉调用成功返回，但 defect 无法归类（unknown）
    return UNKNOWN_DEFECT_WARNING


def fuse_diagnosis(vision_result: Optional[dict], rule_result: dict) -> dict:
    """融合视觉与规则结果。

    参数:
        vision_result: analyze_print_image 的返回（可能为失败/未配置结构）；
        rule_result:   petg_rules.diagnose 的返回。

    返回:
        统一结构：defect / defect_label / severity / confidence /
        visual_evidence / possible_causes(risk_score) /
        recommended_parameters / warning / explanation
    """
    vision_defect = _vision_defect(vision_result)

    # 视觉不可用 → 纯规则回退（区分 失败原因 / 未配置 / unknown）
    if vision_defect is None:
        status = vision_result.get("status") if isinstance(vision_result, dict) else None
        if status == "vision_error":
            reason = str(vision_result.get("reason") or "analysis_failed")
        elif status == "vision_not_configured":
            reason = "vision_not_configured"
        else:
            reason = "defect_unknown"
        result = rule_only_diagnosis(
            rule_result, warning=_vision_fallback_warning(vision_result)
        )
        result["fallback_reason"] = reason
        return result

    rule_defect = rule_result.get("defect")
    consistent = rule_defect == vision_defect

    vision_conf = _confidence(vision_result)
    confidence = round(min(1.0, vision_conf + CONSISTENCY_BONUS), 2) if consistent else vision_conf

    if consistent:
        warning = None
    else:
        warning = (
            f"视觉判定为“{petg_rules.DEFECT_LABELS.get(vision_defect, vision_defect)}”，"
            f"但工艺参数规则更倾向“{_rule_label(rule_result)}”，两者存在冲突，"
            "已保留视觉结论，请人工复核。"
        )

    severity = _more_severe(vision_result.get("severity"), rule_result.get("severity"))
    evidence = _vision_evidence(vision_result)
    defect_label = petg_rules.DEFECT_LABELS.get(vision_defect, vision_defect)

    return {
        "defect": vision_defect,
        "defect_label": defect_label,
        "severity": severity,
        "confidence": confidence,
        "visual_evidence": evidence,
        "possible_causes": _to_risk_causes(rule_result.get("possible_causes")),
        "recommended_parameters": rule_result.get("recommended_parameters"),
        "warning": warning,
        "explanation": _build_explanation(
            defect_label, evidence, consistent, rule_result.get("explanation", "")
        ),
        "fallback_used": False,
        "fallback_type": None,
        "fallback_reason": None,
    }
