"""PETG 打印规则库（Bambu Lab P1S）。

本模块使用纯规则方式对打印参数进行缺陷风险评分，
不依赖任何大模型或外部 API。

V0.2 支持三类缺陷：
- stringing           拉丝
- under_extrusion     欠挤出
- first_layer_issue   首层附着异常
"""

DEVICE = "Bambu Lab P1S"
MATERIAL = "PETG"

# PETG 在 P1S 上的经验基准参数
BASELINE = {
    "nozzle_temp": 240,
    "bed_temp": 80,
    "print_speed": 150,
    "fan_speed": 60,
    "layer_height": 0.2,
    "retraction": 0.8,
}

SUPPORTED_DEFECTS = ("stringing", "under_extrusion", "first_layer_issue")

DEFECT_LABELS = {
    "stringing": "拉丝",
    "under_extrusion": "欠挤出",
    "first_layer_issue": "首层附着异常",
}

# 症状关键词 → 缺陷映射
SYMPTOM_KEYWORDS = {
    "stringing": ["拉丝", "毛丝", "细丝", "丝状", "string", "oop"],
    "under_extrusion": ["欠挤", "挤出不足", "缺料", "断料", "孔洞", "under"],
    "first_layer_issue": [
        "首层",
        "底层",
        "附着",
        "翘边",
        "翘曲",
        "不粘",
        "脱离",
        "first",
        "adhesion",
        "warp",
    ],
}


def _clamp(value, low=0.0, high=1.0):
    return max(low, min(high, value))


def _cause(name, factor):
    """将风险因子转换为 0~0.9 的原因得分。"""
    return {"cause": name, "score": round(_clamp(factor) * 0.9, 2)}


def _score_stringing(p):
    causes = []
    temp_factor = _clamp((p["nozzle_temp"] - 235) / 25.0)
    if temp_factor > 0:
        causes.append(_cause("喷嘴温度偏高", temp_factor))

    # 回抽为可选参数：未提供时不纳入“回抽不足”判断
    retraction = p.get("retraction")
    if retraction is not None:
        retract_factor = _clamp((1.0 - retraction) / 0.8)
        if retract_factor > 0:
            causes.append(_cause("回抽不足", retract_factor))
    return causes


def _score_under_extrusion(p):
    causes = []
    speed_factor = _clamp((p["print_speed"] - 150) / 150.0)
    if speed_factor > 0:
        causes.append(_cause("打印速度过高", speed_factor))
    temp_factor = _clamp((235 - p["nozzle_temp"]) / 35.0)
    if temp_factor > 0:
        causes.append(_cause("喷嘴温度偏低", temp_factor))
    return causes


def _score_first_layer(p):
    causes = []
    bed_factor = _clamp((80 - p["bed_temp"]) / 30.0)
    if bed_factor > 0:
        causes.append(_cause("热床温度偏低", bed_factor))
    speed_factor = _clamp((p["print_speed"] - 120) / 150.0)
    if speed_factor > 0:
        causes.append(_cause("打印速度过高", speed_factor))
    return causes


_SCORERS = {
    "stringing": _score_stringing,
    "under_extrusion": _score_under_extrusion,
    "first_layer_issue": _score_first_layer,
}


def _total(causes):
    return round(sum(c["score"] for c in causes), 2)


def severity_from_total(total):
    if total >= 1.2:
        return "high"
    if total >= 0.6:
        return "medium"
    return "low"


def detect_defect(params, symptom):
    """根据症状关键词优先判断，否则取风险总分最高的缺陷。"""
    text = (symptom or "").lower()
    for defect, keywords in SYMPTOM_KEYWORDS.items():
        if any(k in text for k in keywords):
            return defect, "symptom"

    scored = {d: _total(_SCORERS[d](params)) for d in SUPPORTED_DEFECTS}
    best = max(scored, key=scored.get)
    return best, "parameter"


def recommend_parameters(defect, params):
    rec = {
        "nozzle_temp": BASELINE["nozzle_temp"],
        "bed_temp": BASELINE["bed_temp"],
        "print_speed": BASELINE["print_speed"],
        "fan_speed": BASELINE["fan_speed"],
        "retraction": BASELINE["retraction"],
    }
    if defect == "stringing":
        rec["nozzle_temp"] = min(int(params["nozzle_temp"]), 235)
        retraction = params.get("retraction")
        if retraction is None:
            rec["retraction"] = BASELINE["retraction"]
        else:
            rec["retraction"] = round(max(retraction + 0.3, 1.0), 2)
        rec["fan_speed"] = max(int(params["fan_speed"]), 70)
    elif defect == "under_extrusion":
        rec["nozzle_temp"] = max(int(params["nozzle_temp"]), 240)
        rec["print_speed"] = min(int(params["print_speed"]), 150)
    elif defect == "first_layer_issue":
        rec["bed_temp"] = max(int(params["bed_temp"]), 80)
        rec["print_speed"] = min(int(params["print_speed"]), 120)
    return rec


def build_explanation(defect, cause_names):
    label = DEFECT_LABELS[defect]
    if cause_names:
        cause_text = "、".join(cause_names)
        return (
            f"根据输入的 PETG 参数，主要缺陷判定为“{label}”，"
            f"最可能的原因是：{cause_text}。"
            "建议参考下方推荐参数进行微调后重新打印观察。"
        )
    return (
        f"当前参数未触发明显的“{label}”风险阈值，"
        "建议保持参数并观察打印结果，如有异常请补充症状描述。"
    )


def diagnose(params, symptom=""):
    defect, basis = detect_defect(params, symptom)
    causes = _SCORERS[defect](params)
    causes.sort(key=lambda c: c["score"], reverse=True)
    total = _total(causes)
    severity = severity_from_total(total)
    recommended = recommend_parameters(defect, params)
    explanation = build_explanation(defect, [c["cause"] for c in causes])
    if params.get("retraction") is None:
        explanation += " 回抽参数未提供，本次诊断未纳入回抽因素。"
    return {
        "defect": defect,
        "defect_label": DEFECT_LABELS[defect],
        "severity": severity,
        "possible_causes": causes,
        "recommended_parameters": recommended,
        "explanation": explanation,
    }
