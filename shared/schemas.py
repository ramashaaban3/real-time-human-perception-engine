from typing import Literal, Optional
from pydantic import BaseModel, Field


PositionType = Literal["left", "center", "right"]
ActionType = Literal["GREET", "ALIGN_REQUEST", "MULTI_PERSON_WARN", "NO_ACTION"]


class PrimaryPerson(BaseModel):
    detected: bool = Field(..., description="Whether a primary person was detected")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Detection confidence")
    position: Optional[PositionType] = Field(
        default=None, description="Primary person's horizontal position in the frame"
    )


class PerceptionResult(BaseModel):
    people_count: int = Field(..., ge=0, description="Number of detected people")
    primary_person: PrimaryPerson
    inference_time_ms: float = Field(
        ..., ge=0.0, description="Perception inference time in milliseconds"
    )
    fps: float = Field(..., ge=0.0, description="Estimated frames per second")


class DecisionResult(BaseModel):
    action: ActionType = Field(..., description="Reasoning decision output")
    reason: str = Field(..., description="Why this action was selected")
    stable_detection: bool = Field(
        ..., description="Whether detection was stabilized over recent frames"
    )
    cooldown_active: bool = Field(
        ..., description="Whether cooldown is currently active"
    )
    cooldown_remaining_sec: float = Field(
        ..., ge=0.0, description="Remaining cooldown duration in seconds"
    )


class EventRecord(BaseModel):
    id: int
    created_at: str
    people_count: int
    detected: bool
    confidence: float
    position: Optional[str]
    inference_time_ms: float
    fps: float
    action: str
    reason: str
    stable_detection: bool
    cooldown_active: bool
    cooldown_remaining_sec: float
    e2e_latency_ms: float

# LLM katmanı için dönecek yeni response modeli
class LLMDecisionResult(BaseModel):

    # Son karar
    action: str

    # Robotun Türkçe söyleyeceği cümle
    utterance_tr: str

    # Güven skoru
    certainty: float = Field(..., ge=0.0, le=1.0)

    # Sonucun kaynağı
    # örnek: "rules", "llm", "llm_fallback_rules"
    source: str

    # Açıklama / sebep
    reason: Optional[str] = None

    # Aşağıdaki alanlar debug ve analiz için yararlı
    stable_detection: Optional[bool] = None
    cooldown_active: Optional[bool] = None
    cooldown_remaining_sec: Optional[float] = None