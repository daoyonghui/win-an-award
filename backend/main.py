import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import ValidationError

import config
from database import db
from diagnosis import fusion
from learning import experience_engine
from learning.experiment_summary import get_experiment_summary
from rules import petg_rules
from schemas import DiagnoseRequest, DiagnoseResponse
from vision import vision_service

app = FastAPI(
    title="PrintMind",
    description="基于多模态智能体与工艺闭环优化的 FDM 3D 打印质量控制系统",
    version="0.5.0",
)

db.init_db()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5173",
        "http://localhost:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

_FORM_FIELDS = (
    "material",
    "nozzle_temp",
    "bed_temp",
    "print_speed",
    "fan_speed",
    "layer_height",
    "retraction",
    "symptom",
    "data_source",
)


def _validation_detail(exc: ValidationError):
    return [
        {
            "loc": list(err.get("loc", [])),
            "msg": err.get("msg", ""),
            "type": err.get("type", ""),
        }
        for err in exc.errors()
    ]


def _parse_json(data: dict) -> DiagnoseRequest:
    try:
        return DiagnoseRequest(**data)
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=_validation_detail(exc))


def _parse_form(values: dict) -> DiagnoseRequest:
    data = {k: v for k, v in values.items() if v is not None and v != ""}
    try:
        return DiagnoseRequest(**data)
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=_validation_detail(exc))


def _looks_like_image(content: bytes) -> bool:
    if content[:3] == b"\xff\xd8\xff":
        return True
    if content[:8] == b"\x89PNG\r\n\x1a\n":
        return True
    return False


async def _save_upload(upload) -> str:
    filename = getattr(upload, "filename", "") or ""
    suffix = Path(filename).suffix.lower()
    content_type = (getattr(upload, "content_type", "") or "").lower()

    if suffix not in config.ALLOWED_IMAGE_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail="仅支持 jpg / jpeg / png 格式的图片。",
        )

    if content_type and not (
        content_type.startswith("image/") or content_type == "application/octet-stream"
    ):
        raise HTTPException(
            status_code=400,
            detail=f"不支持的文件类型：{content_type}，仅支持 jpg / jpeg / png。",
        )

    content = await upload.read()
    if not content:
        raise HTTPException(status_code=400, detail="上传的图片内容为空。")

    if len(content) > config.MAX_IMAGE_SIZE:
        raise HTTPException(status_code=413, detail="图片超过 10MB 限制。")

    if not _looks_like_image(content):
        raise HTTPException(
            status_code=400,
            detail="文件内容不是有效的 JPG/PNG 图片，请重新选择。",
        )

    safe_name = f"{datetime.now():%Y%m%d_%H%M%S}_{uuid.uuid4().hex[:8]}{suffix}"
    dest = config.UPLOAD_DIR / safe_name
    dest.write_bytes(content)
    return str(dest)


def _to_float(value: Any) -> Optional[float]:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _to_bool(value: Any) -> Optional[bool]:
    if value is None or value == "":
        return None
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "y", "on", "是"}


def _persist_diagnosis(payload: DiagnoseRequest, result: dict, image_path: Optional[str]) -> int:
    recommended = result.get("recommended_parameters") or {}
    record = {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "material": payload.material,
        "data_source": payload.data_source,
        "image_path": Path(image_path).name if image_path else None,
        "defect": result.get("defect"),
        "defect_label": result.get("defect_label"),
        "severity": result.get("severity"),
        "confidence": result.get("confidence"),
        "nozzle_temp": payload.nozzle_temp,
        "bed_temp": payload.bed_temp,
        "print_speed": payload.print_speed,
        "fan_speed": payload.fan_speed,
        "layer_height": payload.layer_height,
        "retraction": payload.retraction,
        "recommended_nozzle_temp": recommended.get("nozzle_temp"),
        "recommended_bed_temp": recommended.get("bed_temp"),
        "recommended_print_speed": recommended.get("print_speed"),
        "recommended_fan_speed": recommended.get("fan_speed"),
        "recommended_retraction": recommended.get("retraction"),
        "explanation": result.get("explanation"),
        "warning": result.get("warning"),
    }
    return db.insert_diagnosis(record)


@app.get("/")
def root():
    return {
        "name": "PrintMind",
        "status": "running",
    }


@app.get("/health")
def health():
    return {
        "status": "ok",
    }


@app.post("/diagnose", response_model=DiagnoseResponse)
async def diagnose(request: Request):
    content_type = request.headers.get("content-type", "").lower()

    image_path = None

    if content_type.startswith("multipart/form-data"):
        form = await request.form()
        if not hasattr(form, "get"):
            raise HTTPException(status_code=400, detail="请求格式无效。")

        values = {field: form.get(field) for field in _FORM_FIELDS}
        image = form.get("image")
        if image is not None and getattr(image, "filename", ""):
            image_path = await _save_upload(image)

        payload = _parse_form(values)
    elif content_type.startswith("application/json"):
        try:
            data = await request.json()
        except Exception:
            raise HTTPException(status_code=400, detail="JSON 请求体解析失败。")
        payload = _parse_json(data)
    else:
        raise HTTPException(
            status_code=415,
            detail="仅支持 application/json 或 multipart/form-data。",
        )

    if payload.material.upper() != petg_rules.MATERIAL:
        raise HTTPException(
            status_code=400,
            detail=f"当前仅支持材料 {petg_rules.MATERIAL}（{petg_rules.DEVICE}, PETG）。",
        )

    params = {
        "nozzle_temp": payload.nozzle_temp,
        "bed_temp": payload.bed_temp,
        "print_speed": payload.print_speed,
        "fan_speed": payload.fan_speed,
        "layer_height": payload.layer_height,
        "retraction": payload.retraction,
    }

    rule_result = petg_rules.diagnose(params, payload.symptom)

    if image_path:
        vision_result = vision_service.analyze_print_image(image_path)
        result = fusion.fuse_diagnosis(vision_result, rule_result)
    else:
        result = fusion.rule_only_diagnosis(rule_result)
        result["fallback_reason"] = "no_image"

    # 历史实验经验：优先级 真实实验 > PETG 规则，采用最小改动策略
    summary = experience_engine.get_experience_summary(
        printer=petg_rules.DEVICE,
        material=payload.material,
        defect=result.get("defect"),
    )
    rule_recommended = result.get("recommended_parameters") or {}
    minimal = experience_engine.build_minimal_change_recommendation(
        params, rule_recommended, summary
    )
    exp_warning = None
    if minimal is not None:
        result["recommended_parameters"] = minimal
        result["optimization_strategy"] = experience_engine.MINIMAL_CHANGE_STRATEGY
        if minimal != rule_recommended:
            exp_warning = experience_engine.CONFLICT_WARNING
    else:
        result["optimization_strategy"] = "rule_based"

    result["experience_used"] = bool(summary.get("insights"))
    result["experience_count"] = summary.get("verified_experiments", 0)
    result["experience_summary"] = summary.get("insights", [])
    if exp_warning:
        existing = result.get("warning")
        result["warning"] = f"{existing} {exp_warning}".strip() if existing else exp_warning

    try:
        result["record_id"] = _persist_diagnosis(payload, result, image_path)
    except Exception:
        result["record_id"] = None

    return result


@app.get("/uploads/{filename}")
def get_upload(filename: str):
    safe_name = Path(filename).name
    path = config.UPLOAD_DIR / safe_name
    if not path.exists():
        raise HTTPException(status_code=404, detail="图片不存在。")
    return FileResponse(path)


@app.get("/history")
def history(limit: int = 20):
    return {
        "items": db.list_diagnoses(limit=limit),
        "stats": db.stats(),
    }


@app.get("/stats")
def stats(include_simulated: bool = False):
    """比赛统计。默认仅统计 real 数据；include_simulated=true 才包含模拟数据。"""
    return db.stats_overview(include_simulated=include_simulated)


@app.get("/experience-summary")
def experience_summary(
    printer: Optional[str] = None,
    material: Optional[str] = None,
    defect: Optional[str] = None,
):
    """当前真实实验经验总结（全部由数据库动态计算）。"""
    return experience_engine.get_experience_summary(
        printer=printer or petg_rules.DEVICE,
        material=material,
        defect=defect,
    )


@app.get("/experiment-summary")
def experiment_summary():
    """实验结论总览（全部由数据库动态聚合）。"""
    return get_experiment_summary()


@app.get("/history/{record_id}")
def history_detail(record_id: int):
    record = db.get_diagnosis(record_id)
    if record is None:
        raise HTTPException(status_code=404, detail="记录不存在。")
    record["experiments"] = db.list_experiments(record_id)
    return record


@app.post("/history/{record_id}/result")
async def history_result(record_id: int, request: Request):
    if db.get_diagnosis(record_id) is None:
        raise HTTPException(status_code=404, detail="记录不存在。")

    content_type = request.headers.get("content-type", "").lower()
    result_image_path = None

    if content_type.startswith("multipart/form-data"):
        form = await request.form()
        if not hasattr(form, "get"):
            raise HTTPException(status_code=400, detail="请求格式无效。")
        image = form.get("result_image")
        if image is not None and getattr(image, "filename", ""):
            result_image_path = await _save_upload(image)
        data = {
            "quality_before": form.get("quality_before"),
            "quality_after": form.get("quality_after"),
            "defect_improved": form.get("defect_improved"),
            "notes": form.get("notes"),
        }
    elif content_type.startswith("application/json"):
        try:
            data = await request.json()
        except Exception:
            raise HTTPException(status_code=400, detail="JSON 请求体解析失败。")
    else:
        raise HTTPException(
            status_code=415,
            detail="仅支持 application/json 或 multipart/form-data。",
        )

    quality_before = _to_float(data.get("quality_before"))
    quality_after = _to_float(data.get("quality_after"))
    defect_improved = _to_bool(data.get("defect_improved"))
    # 只有明确选择“是/否”并填写优化后评分，才算已验证
    verified = defect_improved is not None and quality_after is not None

    updated = db.save_result(
        record_id=record_id,
        result_image_path=Path(result_image_path).name if result_image_path else None,
        quality_before=quality_before,
        quality_after=quality_after,
        defect_improved=defect_improved,
        notes=(data.get("notes") or None),
        created_at=datetime.now().isoformat(timespec="seconds"),
        verified=verified,
    )
    if updated is None:
        raise HTTPException(status_code=404, detail="记录不存在。")
    return updated


@app.post("/history/{record_id}/experiment")
async def history_experiment(record_id: int, request: Request):
    """新增一条实验记录（基准组 / 单变量 / 重复性 / 人工对照）。

    与“系统优化验证”独立，不影响 verified 优化统计。
    """
    if db.get_diagnosis(record_id) is None:
        raise HTTPException(status_code=404, detail="记录不存在。")

    content_type = request.headers.get("content-type", "").lower()
    result_image_path = None

    if content_type.startswith("multipart/form-data"):
        form = await request.form()
        if not hasattr(form, "get"):
            raise HTTPException(status_code=400, detail="请求格式无效。")
        image = form.get("result_image")
        if image is not None and getattr(image, "filename", ""):
            result_image_path = await _save_upload(image)
        data = {
            "experiment_id": form.get("experiment_id"),
            "experiment_type": form.get("experiment_type"),
            "reference_record_id": form.get("reference_record_id"),
            "quality_score": form.get("quality_score"),
            "notes": form.get("notes"),
        }
    elif content_type.startswith("application/json"):
        try:
            data = await request.json()
        except Exception:
            raise HTTPException(status_code=400, detail="JSON 请求体解析失败。")
    else:
        raise HTTPException(
            status_code=415,
            detail="仅支持 application/json 或 multipart/form-data。",
        )

    experiment_type = (data.get("experiment_type") or "baseline").strip()
    if experiment_type not in db.EXPERIMENT_TYPES:
        raise HTTPException(
            status_code=422,
            detail=f"experiment_type 必须为 {list(db.EXPERIMENT_TYPES)} 之一。",
        )

    reference_id = _to_float(data.get("reference_record_id"))
    record = {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "diagnosis_record_id": record_id,
        "experiment_id": (data.get("experiment_id") or None),
        "experiment_type": experiment_type,
        "reference_record_id": int(reference_id) if reference_id is not None else None,
        "quality_score": _to_float(data.get("quality_score")),
        "notes": (data.get("notes") or None),
        "result_image_path": Path(result_image_path).name if result_image_path else None,
    }
    new_id = db.insert_experiment(record)
    created = db.get_experiment(new_id)
    return created
