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
