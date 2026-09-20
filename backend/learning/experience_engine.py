"""历史实验经验引擎。

从 SQLite 的 experiment_records + diagnosis_records 动态计算
「参数变化 → 质量评分变化」的经验，不硬编码任何实验结论。

数据来源约定（与现有表结构一致）：
- experiment_records.diagnosis_record_id → 该实验所用参数所在的诊断记录
- experiment_records.reference_record_id → 参照的基准诊断记录 id
- 基准质量分 = 其 diagnosis_record_id 等于 reference_record_id 的实验记录的 quality_score

本模块只做“单次实验证据”的汇总，不声称统计显著性。
"""

from typing import Any, Dict, List, Optional, Tuple

from database import db

# 参与归因的参数
FACTORS = (
    "nozzle_temp",
    "bed_temp",
    "print_speed",
    "fan_speed",
    "layer_height",
    "retraction",
)

# 可推荐参数（与 RecommendedParameters 对齐）
RECOMMENDED_FACTORS = (
    "nozzle_temp",
    "bed_temp",
    "print_speed",
    "fan_speed",
    "retraction",
)

FACTOR_LABELS = {
    "nozzle_temp": "喷嘴温度",
    "bed_temp": "热床温度",
    "print_speed": "打印速度",
    "fan_speed": "风扇",
    "layer_height": "层高",
    "retraction": "回抽",
}

CONFIDENCE_ORDER = {"low": 0, "medium": 1, "high": 2}

CONFLICT_WARNING = (
    "当前设备与材料的历史实验结果与通用规则存在冲突，本次建议优先参考真实实验。"
)

MINIMAL_CHANGE_STRATEGY = "minimal_change"


def _confidence(evidence_count: int) -> str:
    """证据强度：1 条 low；2~3 条 medium；4 条以上 high。"""
    if evidence_count >= 4:
        return "high"
    if evidence_count >= 2:
        return "medium"
    return "low"


def _fetch_experiments() -> List[Dict[str, Any]]:
    conn = db.get_connection()
    try:
        rows = conn.execute("SELECT * FROM experiment_records ORDER BY id").fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


def _fetch_diagnoses() -> Dict[int, Dict[str, Any]]:
    conn = db.get_connection()
    try:
        rows = conn.execute("SELECT * FROM diagnosis_records").fetchall()
        return {int(row["id"]): dict(row) for row in rows}
    finally:
        conn.close()


def _to_float(value: Any) -> Optional[float]:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def get_experience_summary(
    printer: Optional[str] = None,
    material: Optional[str] = None,
    defect: Optional[str] = None,
) -> Dict[str, Any]:
    """汇总真实实验经验。

    返回:
        {
          "verified_experiments": N,
          "insights": [
            {"factor", "factor_label", "direction", "effect",
             "quality_delta", "evidence_count", "confidence",
             "tested_value", "baseline_value"}
          ]
        }
    """
    experiments = _fetch_experiments()
    diagnoses = _fetch_diagnoses()

    # diagnosis_id -> 该诊断对应实验的 quality_score（用于取基准质量分）
    quality_by_diag: Dict[int, float] = {}
    for exp in experiments:
        diag_id = exp.get("diagnosis_record_id")
        quality = _to_float(exp.get("quality_score"))
        if diag_id is not None and quality is not None:
            quality_by_diag[int(diag_id)] = quality

    included: List[Dict[str, Any]] = []
    # (factor, direction) -> 样本列表
    buckets: Dict[Tuple[str, str], List[Dict[str, Any]]] = {}

    for exp in experiments:
        diag_id = exp.get("diagnosis_record_id")
        diag = diagnoses.get(int(diag_id)) if diag_id is not None else None

        # 过滤（无关联诊断的记录无法确认材料/缺陷，仍计入总数但不参与归因）
        if diag is not None:
            if material and str(diag.get("material") or "").upper() != material.upper():
                continue
            if defect and diag.get("defect") != defect:
                continue

        included.append(exp)

        ref_id = exp.get("reference_record_id")
        if diag is None or ref_id is None:
            continue

        ref_diag = diagnoses.get(int(ref_id))
        ref_quality = quality_by_diag.get(int(ref_id))
        exp_quality = _to_float(exp.get("quality_score"))
        if ref_diag is None or ref_quality is None or exp_quality is None:
            continue

        delta = exp_quality - ref_quality

        for factor in FACTORS:
            new_value = _to_float(diag.get(factor))
            base_value = _to_float(ref_diag.get(factor))
            if new_value is None or base_value is None or new_value == base_value:
                continue
            direction = "increase" if new_value > base_value else "decrease"
            buckets.setdefault((factor, direction), []).append(
                {"delta": delta, "tested": new_value, "base": base_value}
            )

    insights: List[Dict[str, Any]] = []
    for (factor, direction), samples in buckets.items():
        deltas = [sample["delta"] for sample in samples]
        average = sum(deltas) / len(deltas)
        if average > 0:
            effect = "improved"
        elif average < 0:
            effect = "worsened"
        else:
            effect = "unchanged"

        # 代表样本：改善取 delta 最大，恶化取 delta 最小
        if effect == "improved":
            representative = max(samples, key=lambda s: s["delta"])
        elif effect == "worsened":
            representative = min(samples, key=lambda s: s["delta"])
        else:
            representative = samples[0]

        evidence_count = len(samples)
        insights.append(
            {
                "factor": factor,
                "factor_label": FACTOR_LABELS.get(factor, factor),
                "direction": direction,
                "effect": effect,
                "quality_delta": round(average, 1),
                "evidence_count": evidence_count,
                "confidence": _confidence(evidence_count),
                "tested_value": representative["tested"],
                "baseline_value": representative["base"],
            }
        )

    insights.sort(key=lambda item: (item["factor"], item["direction"]))

    return {
        "printer": printer,
        "material": material,
        "defect": defect,
        "verified_experiments": len(included),
        "insights": insights,
    }


def build_minimal_change_recommendation(
    current: Dict[str, Any],
    rule_recommended: Dict[str, Any],
    summary: Dict[str, Any],
) -> Optional[Dict[str, Any]]:
    """最小改动推荐策略。

    存在真实实验经验时：
    - 默认保持当前值（无经验支持的参数不改动）；
    - 只对具有 "improved" 证据的单一参数做主动修改；
    - 推荐值取历史成功实验中的实测值，不外推到更大/更小的未验证范围。

    返回 None 表示无可用经验（由调用方继续使用规则推荐）。
    """
    insights = summary.get("insights") or []
    if not insights:
        return None

    adjusted: Dict[str, Any] = {}
    for factor in RECOMMENDED_FACTORS:
        current_value = _to_float(current.get(factor))
        if current_value is not None:
            adjusted[factor] = current_value
        else:
            adjusted[factor] = rule_recommended.get(factor)

    improved = [
        item
        for item in insights
        if item.get("effect") == "improved" and _to_float(item.get("tested_value")) is not None
    ]
    if improved:
        improved.sort(
            key=lambda item: (
                CONFIDENCE_ORDER.get(item.get("confidence"), 0),
                abs(item.get("quality_delta") or 0),
            ),
            reverse=True,
        )
        best = improved[0]
        factor = best.get("factor")
        target = _to_float(best.get("tested_value"))
        current_value = _to_float(current.get(factor))

        if factor in adjusted and target is not None:
            if best.get("direction") == "increase":
                # 仅向历史已验证的改善值靠近，不外推超过该值
                if current_value is None or target > current_value:
                    adjusted[factor] = target
            else:
                if current_value is None or target < current_value:
                    adjusted[factor] = target

    return adjusted
