import secrets
from datetime import datetime
from datetime import timedelta
from datetime import timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.constants import PASSWORD_RESET_CODE_LENGTH
from app.core.constants import UserRole
from app.core.exceptions import BadRequestError
from app.core.exceptions import ConflictError
from app.core.security import create_access_token
from app.core.security import get_password_hash
from app.core.security import verify_password
from app.db.models import AppUser
from app.db.models import PasswordResetCode
from app.db.session import create_all_tables
from app.db.session import drop_all_tables
from app.db.session import SessionLocal


class AuthService:
    def reset(self) -> None:
        drop_all_tables()
        create_all_tables()
        with self._session() as db:
            self.ensure_seed_admin(db)
            db.commit()

    @staticmethod
    def _session() -> Session:
        return SessionLocal()

    def register_customer(
        self,
        db: Session,
        *,
        full_name: str,
        phone_number: str,
        password: str,
    ) -> dict:
        existing_user = db.execute(
            select(AppUser).where(AppUser.phone_number == phone_number)
        ).scalar_one_or_none()
        if existing_user is not None:
            raise ConflictError("Phone number already registered")

        user = AppUser(
            full_name=full_name,
            phone_number=phone_number,
            password_hash=get_password_hash(password),
            role=UserRole.CUSTOMER.value,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return self._serialize_user(user)

    def login(
        self,
        db: Session,
        *,
        phone_number: str,
        password: str,
    ) -> dict | None:
        user = db.execute(
            select(AppUser).where(AppUser.phone_number == phone_number)
        ).scalar_one_or_none()
        if user is None:
            return None
        if not verify_password(password, user.password_hash):
            return None
        return self._serialize_user(user)

    def get_by_id(self, db: Session, user_id: str) -> dict | None:
        user = db.execute(
            select(AppUser).where(AppUser.id == user_id)
        ).scalar_one_or_none()
        if user is None:
            return None
        return self._serialize_user(user)

    @staticmethod
    def _serialize_user(user: AppUser) -> dict:
        return {
            "id": user.id,
            "auth_user_id": user.auth_user_id,
            "full_name": user.full_name,
            "phone_number": user.phone_number,
            "role": user.role,
        }

    @staticmethod
    def token_for(user: dict) -> str:
        return create_access_token(
            subject=user["id"],
            auth_user_id=user["auth_user_id"],
            role=user["role"],
            phone_number=user["phone_number"],
        )

    def dev_login(self, db: Session, *, role: UserRole) -> dict:
        if role == UserRole.ADMIN:
            user = self.ensure_seed_admin(db)
        else:
            user = db.execute(
                select(AppUser).where(
                    AppUser.phone_number == settings.dev_customer_phone_number
                )
            ).scalar_one_or_none()
            if user is None:
                user = AppUser(
                    full_name=settings.dev_customer_full_name,
                    phone_number=settings.dev_customer_phone_number,
                    password_hash=get_password_hash(secrets.token_urlsafe(16)),
                    role=UserRole.CUSTOMER.value,
                )
                db.add(user)
                db.commit()
                db.refresh(user)

        return self._serialize_user(user)

    def issue_password_reset_code(
        self,
        db: Session,
        *,
        phone_number: str,
    ) -> dict:
        user = db.execute(
            select(AppUser).where(AppUser.phone_number == phone_number)
        ).scalar_one_or_none()
        if user is None:
            return {}

        existing_codes = (
            db.execute(
                select(PasswordResetCode).where(
                    PasswordResetCode.phone_number == phone_number,
                    PasswordResetCode.used_at.is_(None),
                )
            )
            .scalars()
            .all()
        )
        now = datetime.now(timezone.utc)
        for existing in existing_codes:
            existing.used_at = now

        code = f"{secrets.randbelow(10**PASSWORD_RESET_CODE_LENGTH):0{PASSWORD_RESET_CODE_LENGTH}d}"
        reset_code = PasswordResetCode(
            user_id=user.id,
            phone_number=phone_number,
            code_hash=get_password_hash(code),
            expires_at=now
            + timedelta(minutes=settings.password_reset_code_expire_minutes),
        )
        db.add(reset_code)
        db.commit()

        if settings.password_reset_dev_preview_enabled and settings.is_dev_like:
            return {"dev_code_preview": code}
        return {}

    def reset_password_with_code(
        self,
        db: Session,
        *,
        phone_number: str,
        verification_code: str,
        new_password: str,
    ) -> None:
        reset_code = db.execute(
            select(PasswordResetCode)
            .where(
                PasswordResetCode.phone_number == phone_number,
                PasswordResetCode.used_at.is_(None),
            )
            .order_by(PasswordResetCode.created_at.desc())
        ).scalar_one_or_none()
        if reset_code is None:
            raise BadRequestError("Invalid or expired verification code")

        now = datetime.now(timezone.utc)
        expires_at = reset_code.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        if expires_at <= now:
            raise BadRequestError("Invalid or expired verification code")
        if reset_code.attempt_count >= settings.password_reset_code_max_attempts:
            raise BadRequestError("Verification code attempt limit exceeded")
        if not verify_password(verification_code, reset_code.code_hash):
            reset_code.attempt_count += 1
            db.commit()
            raise BadRequestError("Invalid or expired verification code")

        user = db.execute(
            select(AppUser).where(AppUser.id == reset_code.user_id)
        ).scalar_one_or_none()
        if user is None:
            raise BadRequestError("Invalid or expired verification code")

        user.password_hash = get_password_hash(new_password)
        reset_code.used_at = now
        db.commit()

    @staticmethod
    def ensure_seed_admin(db: Session) -> AppUser:
        admin = db.execute(
            select(AppUser).where(
                AppUser.phone_number == settings.seed_admin_phone_number
            )
        ).scalar_one_or_none()
        if admin is None:
            admin = AppUser(
                full_name=settings.seed_admin_full_name,
                phone_number=settings.seed_admin_phone_number,
                password_hash=get_password_hash(settings.seed_admin_password),
                role=UserRole.ADMIN.value,
            )
            db.add(admin)
            db.flush()
            return admin

        if admin.role != UserRole.ADMIN.value:
            raise ConflictError(
                "Seed admin phone number is already assigned to a non-admin user",
            )

        if not admin.full_name:
            admin.full_name = settings.seed_admin_full_name
        return admin


auth_service = AuthService()
