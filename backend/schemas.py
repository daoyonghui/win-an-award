"""PrintMind 后端请求 / 响应模型。"""

from typing import List, Literal, Optional

from pydantic import BaseModel, Field

from config import PARAM_RANGES


def _field(name: str, description: str):
    low, high = PARAM_RANGES[name]
    return Field(..., ge=low, le=high, description=f"{description}（{low}~{high}）")


class DiagnoseRequest(BaseModel):
    material: str = Field(default="PETG", description="材料，当前仅支持 PETG")
    nozzle_temp: float = _field("nozzle_temp", "喷嘴温度 (℃)")
    bed_temp: float = _field("bed_temp", "热床温度 (℃)")
    print_speed: float = _field("print_speed", "打印速度 (mm/s)")
    fan_speed: float = _field("fan_speed", "风扇速度 (%)")
    layer_height: float = _field("layer_height", "层高 (mm)")
    retraction: Optional[float] = Field(
        default=None, ge=0, le=10, description="回抽距离 (mm)，可选（0~10），留空则不计入回抽因素"
    )
    symptom: Optional[str] = Field(default="", description="症状描述")
    data_source: Literal["real", "simulated", "external"] = Field(
        default="real",
        description="数据来源：real（真实实验）/ simulated（模拟数据）/ external（外部公开样本）",
    )


class PossibleCause(BaseModel):
    cause: str
    risk_score: Optional[float] = Field(default=None, description="规则风险分（非概率）")
    score: Optional[float] = Field(default=None, description="兼容旧字段，等同 risk_score")


class RecommendedParameters(BaseModel):
    nozzle_temp: float
    bed_temp: float
    print_speed: float
    fan_speed: float
    retraction: float


class DiagnoseResponse(BaseModel):
    defect: str
    defect_label: Optional[str] = None
    severity: str
    confidence: Optional[float] = None
    visual_evidence: List[str] = Field(default_factory=list)
    possible_causes: List[PossibleCause]
    recommended_parameters: RecommendedParameters
    warning: Optional[str] = None
    explanation: str
    record_id: Optional[int] = None
    experience_used: bool = False
    experience_count: int = 0
    experience_summary: List[dict] = Field(default_factory=list)
    optimization_strategy: Optional[str] = None
    fallback_used: bool = False
    fallback_type: Optional[str] = None
    fallback_reason: Optional[str] = None
