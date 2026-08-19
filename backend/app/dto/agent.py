from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from typing import Literal

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field
from pydantic import model_validator


AgentSurface = Literal["chatbot", "recommendation_explanation", "admin_assistant"]
EvidenceStatus = Literal["complete", "partial", "insufficient_evidence"]


class AgentMessageDto(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=2000)


class AgentContextDto(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    surface: AgentSurface
    run_id: str | None = Field(default=None, min_length=1, max_length=36)
    catalog_id: str | None = Field(default=None, min_length=1, max_length=120)
    booking_id: str | None = Field(default=None, min_length=1, max_length=36)

    @model_validator(mode="after")
    def validate_page_context(self) -> "AgentContextDto":
        if self.surface == "recommendation_explanation" and (
            not self.run_id or not self.catalog_id
        ):
            raise ValueError(
                "recommendation_explanation requires run_id and catalog_id"
            )
        return self


class AgentQueryDto(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    message: str = Field(min_length=1, max_length=2000)
    context: AgentContextDto
    conversation_history: list[AgentMessageDto] = Field(
        default_factory=list,
        max_length=12,
    )


class AgentWhatIfChangesDto(BaseModel):
    model_config = ConfigDict(extra="forbid")

    skill_level: Literal["beginner", "intermediate", "advanced"] | None = None
    playing_style: Literal["attacking", "balanced", "control_defensive"] | None = None
    preferred_tension: float | None = Field(default=None, ge=16, le=35)
    frequency_per_week: int | None = Field(default=None, ge=0, le=14)
    preferred_feel: Literal["soft", "medium", "hard"] | None = None
    preferred_gauge: Literal["no_preference", "thin", "medium", "thick"] | None = None
    recent_goal: (
        Literal[
            "balanced",
            "power",
            "control",
            "durability",
            "comfort",
            "tension_retention",
            "value_for_money",
        ]
        | None
    ) = None
    attack: int | None = Field(default=None, ge=1, le=10)
    comfort: int | None = Field(default=None, ge=1, le=10)
    control: int | None = Field(default=None, ge=1, le=10)
    durability: int | None = Field(default=None, ge=1, le=10)
    elasticity: int | None = Field(default=None, ge=1, le=10)
    sound: int | None = Field(default=None, ge=1, le=10)
    string_movement: int | None = Field(default=None, ge=1, le=10)
    tension_retention: int | None = Field(default=None, ge=1, le=10)
    value_for_money: int | None = Field(default=None, ge=1, le=10)
    budget_rm: float | None = Field(default=None, ge=0, le=1000)
    racket_id: str | None = Field(default=None, min_length=1, max_length=36)

    @model_validator(mode="after")
    def validate_change(self) -> "AgentWhatIfChangesDto":
        if not self.model_dump(exclude_none=True):
            raise ValueError("At least one What-if change is required")
        return self


class AgentSourceDto(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_type: str
    source_id: str
    label: str
    version: str | None = None


class AgentActionDto(BaseModel):
    model_config = ConfigDict(extra="forbid")

    action: Literal[
        "open_string",
        "open_recommendation",
        "open_booking",
        "request_human_handoff",
        "open_admin_booking",
        "open_admin_inventory",
        "open_admin_conversation",
        "open_admin_payments",
        "update_booking_status",
        "update_inventory_stock",
        "send_admin_message",
    ]
    label: str
    parameters: dict[str, str] = Field(default_factory=dict)


class AgentHandoffDto(BaseModel):
    model_config = ConfigDict(extra="forbid")

    recommended: bool
    reason: str | None = None
    booking_id: str | None = None


class AgentResponseDto(BaseModel):
    model_config = ConfigDict(extra="forbid")

    answer: str
    summary: str
    evidence: list[str] = Field(default_factory=list)
    sources: list[AgentSourceDto] = Field(default_factory=list)
    evidence_status: EvidenceStatus
    suggested_questions: list[str] = Field(default_factory=list, max_length=4)
    suggested_actions: list[AgentActionDto] = Field(default_factory=list)
    handoff: AgentHandoffDto | None = None
    model: str
    response_id: str | None = None


class AgentGeneratedAnswerDto(BaseModel):
    model_config = ConfigDict(extra="forbid")

    answer: str
    summary: str
    evidence: list[str] = Field(default_factory=list)
    evidence_status: EvidenceStatus
    suggested_questions: list[str] = Field(default_factory=list, max_length=4)
    suggested_actions: list[AgentActionDto] = Field(default_factory=list)
    handoff: AgentHandoffDto | None = None


@dataclass(frozen=True)
class AgentToolResult:
    data: dict[str, Any]
    sources: list[dict[str, str | None]]
