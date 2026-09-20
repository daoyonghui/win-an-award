"""实验结论总览（动态聚合）。

从 SQLite 的 experiment_records / diagnosis_records 动态生成比赛展示用的
实验结论总览，不硬编码任何实验结论或数值。

- 实验记录来自 experiment_records；
- 系统闭环验证来自 diagnosis_records 中 verified=1 的真实记录（不伪造 experiment_record）；
- 结论来自 experience_engine 的动态归因 + 闭环验证数据；
- DISPLAY_META 仅为当前实验项目的展示元数据（不写回数据库）。
"""

import re
from typing import Any, Dict, List, Optional

from database import db
from learning import experience_engine
from rules import petg_rules

TYPE_LABELS = {
    "baseline": "基准组",
    "single_variable": "单变量实验",
    "repeatability": "重复性验证",
    "manual_comparison": "人工对照实验",
    "system_optimization": "系统闭环验证",
}

EXPLORATION_LABEL = "进一步参数探索"

# 当前实验项目的展示元数据（不改动数据库中的 material 字段）
DISPLAY_META = {
    "material_variant": "Bambu PETG HF",
    "color": "红色",
    "nozzle_diameter": "0.4 mm",
}

REAL_CODE_RE = re.compile(r"REAL-\d+")


def _real_index(experiment_id: Optional[str]) -> int:
    match = re.search(r"(\d+)", experiment_id or "")
    return int(match.group(1)) if match else 9999


def _score_text(value: Any) -> str:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return str(value)
    return str(int(number)) if number.is_integer() else str(number)


def _fetch() -> tuple:
    conn = db.get_connection()
    try:
        experiments = [
            dict(row)
            for row in conn.execute(
                "SELECT * FROM experiment_records ORDER BY id"
            ).fetchall()
        ]
        diagnoses = {
            int(row["id"]): dict(row)
            for row in conn.execute("SELECT * FROM diagnosis_records").fetchall()
        }
    finally:
        conn.close()
    return experiments, diagnoses


def _repeatability_groups(experiments: List[dict]) -> Dict[Any, List[dict]]:
    groups: Dict[Any, List[dict]] = {}
    for exp in experiments:
        if exp.get("experiment_type") == "repeatability" and exp.get("quality_score") is not None:
            groups.setdefault(exp.get("reference_record_id"), []).append(exp)
    return groups


def _best_repeatability_group(experiments: List[dict]) -> List[dict]:
    groups = _repeatability_groups(experiments)
    if not groups:
        return []
    return max(groups.values(), key=lambda g: max(x["quality_score"] for x in g))


def _later_explorations(experiments: List[dict]) -> List[dict]:
    """重复性验证之后、评分未超过其最佳结果的进一步探索实验。"""
    best_group = _best_repeatability_group(experiments)
    if not best_group:
        return []
    group_ids = {x["id"] for x in best_group}
    best_score = max(x["quality_score"] for x in best_group)
    return [
        exp
        for exp in experiments
        if exp["id"] not in group_ids
        and exp["id"] > max(group_ids)
        and exp.get("quality_score") is not None
        and exp["quality_score"] < best_score
    ]


def _build_timeline(experiments: List[dict], diagnoses: Dict[int, dict]) -> List[dict]:
    exploration_ids = {e["experiment_id"] for e in _later_explorations(experiments)}

    timeline: List[dict] = []
    for exp in experiments:
        experiment_id = exp.get("experiment_id")
        type_label = TYPE_LABELS.get(exp.get("experiment_type"), exp.get("experiment_type"))
        display_label = EXPLORATION_LABEL if experiment_id in exploration_ids else type_label
        timeline.append(
            {
                "experiment_id": experiment_id,
                "type": exp.get("experiment_type"),
                "type_label": type_label,
                "display_label": display_label,
                "quality_score": exp.get("quality_score"),
                "result_image_path": exp.get("result_image_path"),
                "source": "experiment",
            }
        )

    for diag in diagnoses.values():
        if not diag.get("verified") or diag.get("data_source") != "real":
            continue
        notes = diag.get("notes") or ""
        match = REAL_CODE_RE.search(notes)
        experiment_id = match.group(0) if match else f"闭环验证#{diag['id']}"
        if any(item["experiment_id"] == experiment_id for item in timeline):
            continue
        timeline.append(
            {
                "experiment_id": experiment_id,
                "type": "system_optimization",
                "type_label": TYPE_LABELS["system_optimization"],
                "display_label": TYPE_LABELS["system_optimization"],
                "quality_score": diag.get("quality_after"),
                "quality_before": diag.get("quality_before"),
                "quality_after": diag.get("quality_after"),
                "result_image_path": diag.get("result_image_path"),
                "source": "system_verification",
            }
        )

    timeline.sort(key=lambda item: _real_index(item["experiment_id"]))
    return timeline


def _build_metrics(experiments: List[dict], diagnoses: Dict[int, dict]) -> dict:
    verified = [
        d
        for d in diagnoses.values()
        if d.get("verified") and d.get("data_source") == "real"
    ]
    scores = [e["quality_score"] for e in experiments if e.get("quality_score") is not None]
    baseline = next(
        (e["quality_score"] for e in experiments if e.get("experiment_type") == "baseline"),
        None,
    )
    gains = [
        d["quality_after"] - d["quality_before"]
        for d in verified
        if d.get("quality_before") is not None and d.get("quality_after") is not None
    ]
    return {
        "experiment_records": len(experiments),
        "baseline_score": baseline,
        "max_experiment_score": max(scores) if scores else None,
        "closed_loop_verified": len(verified),
        "closed_loop_improved": sum(1 for d in verified if d.get("defect_improved")),
        "closed_loop_quality_gain": round(sum(gains) / len(gains), 1) if gains else None,
        "repeatability_count": sum(
            1 for e in experiments if e.get("experiment_type") == "repeatability"
        ),
    }


def _build_candidate(experiments: List[dict], diagnoses: Dict[int, dict]) -> Optional[dict]:
    linked = [
        e
        for e in experiments
        if e.get("diagnosis_record_id") is not None and e.get("quality_score") is not None
    ]
    if not linked:
        return None
    linked.sort(key=lambda e: e["quality_score"], reverse=True)
    base = diagnoses.get(int(linked[0]["diagnosis_record_id"]))
    if base is None:
        return None

    fans = []
    for exp in experiments:
        if exp.get("diagnosis_record_id") is None:
            continue
        diag = diagnoses.get(int(exp["diagnosis_record_id"]))
        if diag and diag.get("fan_speed") is not None:
            fans.append(diag["fan_speed"])

    return {
        "printer": petg_rules.DEVICE,
        "material": base.get("material"),
        "material_variant": DISPLAY_META["material_variant"],
        "color": DISPLAY_META["color"],
        "nozzle_diameter": DISPLAY_META["nozzle_diameter"],
        "nozzle_temp": base.get("nozzle_temp"),
        "bed_temp": base.get("bed_temp"),
        "print_speed": base.get("print_speed"),
        "fan_speed_range": [min(fans), max(fans)] if fans else None,
        "layer_height": base.get("layer_height"),
        "retraction": base.get("retraction"),
    }


def _build_conclusions(
    experiments: List[dict],
    diagnoses: Dict[int, dict],
    insights: List[dict],
) -> List[str]:
    conclusions: List[str] = []

    for item in insights:
        label = item.get("factor_label") or item.get("factor")
        direction = item.get("direction")
        effect = item.get("effect")
        if effect == "improved":
            conclusions.append(
                f"增强{label}显示改善趋势。" if direction == "increase" else f"降低{label}显示改善趋势。"
            )
        elif effect == "worsened":
            conclusions.append(
                f"提高{label}曾出现质量下降。" if direction == "increase" else f"降低{label}未显示改善趋势。"
            )
        else:
            conclusions.append(
                f"{label}{'提高' if direction == 'increase' else '降低'}后质量无明显变化。"
            )

    verified = [
        d
        for d in diagnoses.values()
        if d.get("verified") and d.get("data_source") == "real"
    ]
    befores = [d["quality_before"] for d in verified if d.get("quality_before") is not None]
    afters = [d["quality_after"] for d in verified if d.get("quality_after") is not None]
    if befores and afters:
        before_avg = round(sum(befores) / len(befores), 1)
        after_avg = round(sum(afters) / len(afters), 1)
        conclusions.append(
            f"PrintMind 基于历史实验采用最小改动策略后，正式闭环验证质量由 {_score_text(before_avg)} 提升至 {_score_text(after_avg)}。"
        )

    best_group = _best_repeatability_group(experiments)
    if best_group:
        ordered = sorted(best_group, key=lambda x: x["quality_score"], reverse=True)
        score_text = "、".join(_score_text(x["quality_score"]) for x in ordered)
        conclusions.append(
            f"相同推荐参数的重复实验达到 {score_text}，表明当前设置存在重复改善趋势。"
        )

    later = _later_explorations(experiments)
    if later:
        best_score = max(x["quality_score"] for x in best_group)
        ids = "、".join(e["experiment_id"] for e in later)
        scores = "、".join(_score_text(e["quality_score"]) for e in later)
        conclusions.append(
            f"在重复性验证之后进一步调整参数（{ids}，评分 {scores}）未超过重复性验证的最佳结果"
            f"（{_score_text(best_score)}），当前实验条件下重复性验证采用的参数是更合适的候选。"
        )

    if conclusions:
        conclusions.append("以上结论基于当前少量实验的改善趋势，不代表统计显著性。")

    return conclusions


def get_experiment_summary() -> dict:
    experiments, diagnoses = _fetch()
    insights = experience_engine.get_experience_summary(
        printer=petg_rules.DEVICE, material="PETG"
    )["insights"]

    return {
        "metrics": _build_metrics(experiments, diagnoses),
        "timeline": _build_timeline(experiments, diagnoses),
        "candidate_parameters": _build_candidate(experiments, diagnoses),
        "conclusions": _build_conclusions(experiments, diagnoses, insights),
        "insights": insights,
        "display": DISPLAY_META,
    }
