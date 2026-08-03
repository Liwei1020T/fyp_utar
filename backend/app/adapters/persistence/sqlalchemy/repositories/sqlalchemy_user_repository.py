from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.adapters.persistence.sqlalchemy.models import User
from app.adapters.persistence.sqlalchemy.repositories.mappers import to_user_account
from app.domain.auth.entities import UserAccount


class SqlAlchemyUserRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_id(self, user_id: str) -> UserAccount | None:
        user = self.db.execute(
            select(User).where(User.id == user_id)
        ).scalar_one_or_none()
        return to_user_account(user) if user else None

    def get_by_id_for_update(self, user_id: str) -> UserAccount | None:
        user = self.db.execute(
            select(User)
            .where(User.id == user_id)
            .with_for_update()
            .execution_options(populate_existing=True)
        ).scalar_one_or_none()
        return to_user_account(user) if user else None

    def get_by_phone_number(self, phone_number: str) -> UserAccount | None:
        user = self.db.execute(
            select(User).where(User.phone_number == phone_number)
        ).scalar_one_or_none()
        return to_user_account(user) if user else None

    def get_by_phone_number_for_update(
        self,
        phone_number: str,
    ) -> UserAccount | None:
        user = self.db.execute(
            select(User)
            .where(User.phone_number == phone_number)
            .with_for_update()
            .execution_options(populate_existing=True)
        ).scalar_one_or_none()
        return to_user_account(user) if user else None

    def create_user(
        self,
        *,
        username: str,
        phone_number: str,
        password_hash: str,
        role: str,
        auth_provider: str,
    ) -> UserAccount:
        user = User(
            username=username,
            phone_number=phone_number,
            password_hash=password_hash,
            role=role,
            auth_provider=auth_provider,
        )
        self.db.add(user)
        self.db.flush()
        self.db.refresh(user)
        return to_user_account(user)

    def update_password(
        self,
        user_id: str,
        password_hash: str,
    ) -> UserAccount | None:
        user = self.db.execute(
            select(User)
            .where(User.id == user_id)
            .with_for_update()
            .execution_options(populate_existing=True)
        ).scalar_one_or_none()
        if user is None:
            return None
        user.password_hash = password_hash
        user.auth_version += 1
        self.db.flush()
        self.db.refresh(user)
        return to_user_account(user)
