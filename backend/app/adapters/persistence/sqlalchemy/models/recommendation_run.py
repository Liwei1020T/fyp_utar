from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import JSON
from sqlalchemy import Numeric
from sqlalchemy import String as SAString
from sqlalchemy import func
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship

from app.adapters.persistence.sqlalchemy.base import Base
from app.adapters.persistence.sqlalchemy.models.common import generate_uuid

if TYPE_CHECKING:
    from app.adapters.persistence.sqlalchemy.models.user import User


class RecommendationRun(Base):
    __tablename__ = "recommendation_runs"

    id: Mapped[str] = mapped_column(
        SAString(36), primary_key=True, default=generate_uuid
    )
    user_id: Mapped[str | None] = mapped_column(
        SAString(36),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    algorithm_version: Mapped[str] = mapped_column(SAString(80), index=True)
    request_snapshot: Mapped[dict[str, object]] = mapped_column(JSON, default=dict)
    profile_snapshot: Mapped[dict[str, object]] = mapped_column(JSON, default=dict)
    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        index=True,
    )

    user: Mapped["User | None"] = relationship()
    items: Mapped[list["RecommendationRunItem"]] = relationship(
        back_populates="run",
        cascade="all, delete-orphan",
        order_by="RecommendationRunItem.rank_position.asc()",
    )


class RecommendationRunItem(Base):
    __tablename__ = "recommendation_run_items"

    id: Mapped[str] = mapped_column(
        SAString(36), primary_key=True, default=generate_uuid
    )
    run_id: Mapped[str] = mapped_column(
        SAString(36),
        ForeignKey("recommendation_runs.id", ondelete="CASCADE"),
        index=True,
    )
    catalog_id: Mapped[str] = mapped_column(SAString(120), index=True)
    rank_position: Mapped[int] = mapped_column(Integer)
    final_score: Mapped[float] = mapped_column(Numeric(6, 4))
    preference_match_score: Mapped[float | None] = mapped_column(
        Numeric(6, 4),
        nullable=True,
    )
    rule_fit_score: Mapped[float | None] = mapped_column(Numeric(6, 4), nullable=True)
    budget_fit_score: Mapped[float | None] = mapped_column(Numeric(6, 4), nullable=True)
    value_for_money_score: Mapped[float | None] = mapped_column(
        Numeric(6, 4), nullable=True
    )
    nlp_review_score: Mapped[float | None] = mapped_column(
        Numeric(6, 4),
        nullable=True,
    )
    score_breakdown: Mapped[dict[str, object]] = mapped_column(JSON, default=dict)
    rationale: Mapped[dict[str, object]] = mapped_column(JSON, default=dict)

    run: Mapped["RecommendationRun"] = relationship(back_populates="items")
