"""PrintMind 数据访问层（SQLite，基于标准库 sqlite3）。"""

import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional

import config

SCHEMA_PATH = Path(__file__).resolve().parent / "schema.sql"

_DIAGNOSIS_COLUMNS = (
    "created_at",
    "material",
    "data_source",
    "image_path",
    "defect",
    "defect_label",
    "severity",
    "confidence",
    "nozzle_temp",
    "bed_temp",
    "print_speed",
    "fan_speed",
    "layer_height",
    "retraction",
    "recommended_nozzle_temp",
    "recommended_bed_temp",
    "recommended_print_speed",
    "recommended_fan_speed",
    "recommended_retraction",
    "explanation",
    "warning",
)


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(str(config.DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """初始化数据库表结构（幂等），并做轻量字段迁移。"""
    conn = get_connection()
    try:
        conn.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
        _migrate(conn)
        conn.commit()
    finally:
        conn.close()


def _migrate(conn: sqlite3.Connection) -> None:
    """为已存在的旧表补充新增字段。"""
    existing = {
        row["name"]
        for row in conn.execute("PRAGMA table_info(diagnosis_records)").fetchall()
    }
    if "data_source" not in existing:
        conn.execute(
            "ALTER TABLE diagnosis_records "
            "ADD COLUMN data_source TEXT NOT NULL DEFAULT 'real'"
        )


def _row_to_dict(row: Optional[sqlite3.Row]) -> Optional[Dict[str, Any]]:
    if row is None:
        return None
    data = dict(row)
    if data.get("defect_improved") is not None:
        data["defect_improved"] = bool(data["defect_improved"])
    if data.get("verified") is not None:
        data["verified"] = bool(data["verified"])
    return data


def insert_diagnosis(record: Dict[str, Any]) -> int:
    """插入一条诊断记录，返回自增 id。"""
    values = [record.get(column) for column in _DIAGNOSIS_COLUMNS]
    placeholders = ", ".join(["?"] * len(_DIAGNOSIS_COLUMNS))
    columns = ", ".join(_DIAGNOSIS_COLUMNS)

    conn = get_connection()
    try:
        cursor = conn.execute(
            f"INSERT INTO diagnosis_records ({columns}) VALUES ({placeholders})",
            values,
        )
        conn.commit()
        return int(cursor.lastrowid)
    finally:
        conn.close()


def list_diagnoses(limit: int = 20) -> List[Dict[str, Any]]:
    """返回最近的诊断记录（按时间倒序）。"""
    try:
        limit = max(1, min(int(limit), 200))
    except (TypeError, ValueError):
        limit = 20

    conn = get_connection()
    try:
        rows = conn.execute(
            """
            SELECT d.*,
                   (SELECT COUNT(*) FROM experiment_records e
                     WHERE e.diagnosis_record_id = d.id) AS experiment_count
              FROM diagnosis_records d
             ORDER BY d.id DESC
             LIMIT ?
            """,
            (limit,),
        ).fetchall()
        return [_row_to_dict(row) for row in rows]
    finally:
        conn.close()


def get_diagnosis(record_id: int) -> Optional[Dict[str, Any]]:
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT * FROM diagnosis_records WHERE id = ?",
            (record_id,),
        ).fetchone()
        return _row_to_dict(row)
    finally:
        conn.close()


def save_result(
    record_id: int,
    result_image_path: Optional[str],
    quality_before: Optional[float],
    quality_after: Optional[float],
    defect_improved: Optional[bool],
    notes: Optional[str],
    created_at: str,
    verified: bool = False,
) -> Optional[Dict[str, Any]]:
    """保存二次打印 / 优化验证结果。

    verified 由调用方决定：只有明确选择“是/否”并填写优化后评分时才为 True。
    基准实验（未验证）允许 defect_improved 与 quality_after 为 NULL。
    """
    conn = get_connection()
    try:
        cursor = conn.execute(
            """
            UPDATE diagnosis_records
               SET result_image_path = ?,
                   quality_before = ?,
                   quality_after = ?,
                   defect_improved = ?,
                   notes = ?,
                   verified = ?,
                   result_created_at = ?
             WHERE id = ?
            """,
            (
                result_image_path,
                quality_before,
                quality_after,
                None if defect_improved is None else int(bool(defect_improved)),
                notes,
                int(bool(verified)),
                created_at,
                record_id,
            ),
        )
        conn.commit()
        if cursor.rowcount == 0:
            return None
    finally:
        conn.close()

    return get_diagnosis(record_id)


def stats() -> Dict[str, int]:
    """统计诊断总数与已完成优化验证的数量（历史页使用，含所有数据源）。"""
    conn = get_connection()
    try:
        row = conn.execute(
            """
            SELECT COUNT(*) AS total,
                   COALESCE(SUM(verified), 0) AS verified
              FROM diagnosis_records
            """
        ).fetchone()
        return {
            "total": int(row["total"] or 0),
            "verified": int(row["verified"] or 0),
        }
    finally:
        conn.close()


def stats_overview(include_simulated: bool = False) -> Dict[str, Any]:
    """比赛统计：默认仅统计 real 数据；include_simulated=True 才包含模拟数据。

    所有数值均来自 SQLite 真实记录，无数据时返回 0，不编造成功率。
    优化效果只统计 verified=1 的记录。
    """
    where = "" if include_simulated else "WHERE data_source = 'real'"

    conn = get_connection()
    try:
        row = conn.execute(
            f"""
            SELECT COUNT(*) AS total,
                   COALESCE(SUM(verified), 0) AS verified,
                   COALESCE(SUM(CASE WHEN verified = 1 AND defect_improved = 1
                                     THEN 1 ELSE 0 END), 0) AS improved,
                   AVG(CASE WHEN verified = 1 THEN quality_before END) AS avg_before,
                   AVG(CASE WHEN verified = 1 THEN quality_after END) AS avg_after,
                   AVG(CASE WHEN verified = 1
                             AND quality_before IS NOT NULL
                             AND quality_after IS NOT NULL
                            THEN quality_after - quality_before END) AS avg_gain
              FROM diagnosis_records
              {where}
            """
        ).fetchone()

        defect_rows = conn.execute(
            f"""
            SELECT defect, COUNT(*) AS amount
              FROM diagnosis_records
              {where}
             GROUP BY defect
            """
        ).fetchall()
    finally:
        conn.close()

    total = int(row["total"] or 0)
    verified = int(row["verified"] or 0)
    improved = int(row["improved"] or 0)
    improvement_rate = round(improved / verified, 4) if verified else 0.0

    distribution: Dict[str, int] = {
        "stringing": 0,
        "under_extrusion": 0,
        "first_layer_issue": 0,
    }
    for item in defect_rows:
        key = item["defect"] or "unknown"
        distribution[key] = distribution.get(key, 0) + int(item["amount"] or 0)

    def _round(value: Any) -> float:
        return round(float(value), 2) if value is not None else 0.0

    return {
        "total_diagnoses": total,
        "verified_cases": verified,
        "improved_cases": improved,
        "improvement_rate": improvement_rate,
        "avg_quality_before": _round(row["avg_before"]),
        "avg_quality_after": _round(row["avg_after"]),
        "avg_quality_gain": _round(row["avg_gain"]),
        "defect_distribution": distribution,
    }


EXPERIMENT_TYPES = (
    "baseline",
    "single_variable",
    "repeatability",
    "manual_comparison",
)

_EXPERIMENT_COLUMNS = (
    "created_at",
    "diagnosis_record_id",
    "experiment_id",
    "experiment_type",
    "reference_record_id",
    "quality_score",
    "notes",
    "result_image_path",
)


def _experiment_to_dict(row: Optional[sqlite3.Row]) -> Optional[Dict[str, Any]]:
    if row is None:
        return None
    return dict(row)


def insert_experiment(record: Dict[str, Any]) -> int:
    """插入一条实验记录（基准组/单变量/重复性/人工对照），不影响 verified 统计。"""
    values = [record.get(column) for column in _EXPERIMENT_COLUMNS]
    placeholders = ", ".join(["?"] * len(_EXPERIMENT_COLUMNS))
    columns = ", ".join(_EXPERIMENT_COLUMNS)

    conn = get_connection()
    try:
        cursor = conn.execute(
            f"INSERT INTO experiment_records ({columns}) VALUES ({placeholders})",
            values,
        )
        conn.commit()
        return int(cursor.lastrowid)
    finally:
        conn.close()


def list_experiments(diagnosis_record_id: int) -> List[Dict[str, Any]]:
    """返回某条诊断记录下的全部实验记录（按时间倒序）。"""
    conn = get_connection()
    try:
        rows = conn.execute(
            """
            SELECT * FROM experiment_records
             WHERE diagnosis_record_id = ?
             ORDER BY id DESC
            """,
            (diagnosis_record_id,),
        ).fetchall()
        return [_experiment_to_dict(row) for row in rows]
    finally:
        conn.close()


def get_experiment(experiment_record_id: int) -> Optional[Dict[str, Any]]:
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT * FROM experiment_records WHERE id = ?",
            (experiment_record_id,),
        ).fetchone()
        return _experiment_to_dict(row)
    finally:
        conn.close()
