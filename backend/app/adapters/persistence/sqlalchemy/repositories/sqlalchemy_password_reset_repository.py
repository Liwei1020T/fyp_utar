from __future__ import annotations

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.adapters.persistence.sqlalchemy.models import PasswordResetCode
from app.adapters.persistence.sqlalchemy.repositories.mappers import (
    to_password_reset_code,
)
from app.domain.auth.entities import PasswordResetCodeRecord


class SqlAlchemyPasswordResetRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def mark_active_codes_used(self, phone_number: str, used_at: datetime) -> None:
        active_codes = self.db.execute(
            select(PasswordResetCode).where(
                PasswordResetCode.phone_number == phone_number,
                PasswordResetCode.used_at.is_(None),
            )
        ).scalars()
        for code in active_codes:
            code.used_at = used_at

    def create_code(
        self,
        *,
        user_id: str,
        phone_number: str,
        code_hash: str,
        expires_at: datetime,
    ) -> PasswordResetCodeRecord:
        record = PasswordResetCode(
            user_id=user_id,
            phone_number=phone_number,
            code_hash=code_hash,
            expires_at=expires_at,
        )
        self.db.add(record)
        self.db.flush()
        self.db.refresh(record)
        return to_password_reset_code(record)

    def get_latest_active_code(
        self,
        phone_number: str,
    ) -> PasswordResetCodeRecord | None:
        record = self.db.execute(
            select(PasswordResetCode)
            .where(
                PasswordResetCode.phone_number == phone_number,
                PasswordResetCode.used_at.is_(None),
            )
            .order_by(PasswordResetCode.created_at.desc())
            .limit(1)
            .with_for_update()
        ).scalar_one_or_none()
        return to_password_reset_code(record) if record else None

    def update_attempts(self, code_id: str, attempt_count: int) -> None:
        record = self.db.get(PasswordResetCode, code_id)
        if record is None:
            return
        record.attempt_count = attempt_count
        self.db.flush()

    def mark_used(
        self,
        code_id: str,
        used_at: datetime,
    ) -> None:
        record = self.db.get(PasswordResetCode, code_id)
        if record is None:
            return
        record.used_at = used_at
        self.db.flush()
