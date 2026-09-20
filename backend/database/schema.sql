-- PrintMind 诊断历史表
-- 使用 Python 标准库 sqlite3，无需 ORM。

CREATE TABLE IF NOT EXISTS diagnosis_records (
    id                          INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at                  TEXT    NOT NULL,

    -- 输入
    material                    TEXT,
    data_source                 TEXT    NOT NULL DEFAULT 'real',  -- real | simulated
    image_path                  TEXT,

    -- 诊断结果
    defect                      TEXT,
    defect_label                TEXT,
    severity                    TEXT,
    confidence                  REAL,

    -- 原始参数
    nozzle_temp                 REAL,
    bed_temp                    REAL,
    print_speed                 REAL,
    fan_speed                   REAL,
    layer_height                REAL,
    retraction                  REAL,

    -- 推荐参数
    recommended_nozzle_temp     REAL,
    recommended_bed_temp        REAL,
    recommended_print_speed     REAL,
    recommended_fan_speed       REAL,
    recommended_retraction      REAL,

    explanation                 TEXT,
    warning                     TEXT,

    -- 二次打印 / 优化验证结果
    result_image_path           TEXT,
    quality_before              REAL,
    quality_after               REAL,
    defect_improved             INTEGER,
    notes                       TEXT,
    verified                    INTEGER NOT NULL DEFAULT 0,
    result_created_at           TEXT
);

CREATE INDEX IF NOT EXISTS idx_diagnosis_created_at
    ON diagnosis_records (created_at DESC);

-- 实验记录表（与“系统优化验证”相互独立）
-- 用于：基准组 / 单变量实验 / 重复性验证 / 人工对照实验
-- 该表不参与 verified 优化统计（/stats 只统计 diagnosis_records.verified=1）
CREATE TABLE IF NOT EXISTS experiment_records (
    id                      INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at              TEXT    NOT NULL,
    diagnosis_record_id     INTEGER,
    experiment_id           TEXT,
    experiment_type         TEXT,   -- baseline | single_variable | repeatability | manual_comparison
    reference_record_id     INTEGER,
    quality_score           REAL,
    notes                   TEXT,
    result_image_path       TEXT
);

CREATE INDEX IF NOT EXISTS idx_experiment_diagnosis
    ON experiment_records (diagnosis_record_id);
