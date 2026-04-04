from fastapi import APIRouter
from fastapi import Depends
from sqlalchemy.orm import Session

from app.api.deps.auth import get_current_user
from app.api.responses import success_response
from app.core.config import settings
from app.core.exceptions import NotFoundError
from app.core.exceptions import UnauthorizedError
from app.db.session import get_db
from app.schemas.auth import DevLoginPayload
from app.schemas.auth import ForgotPasswordRequestPayload
from app.schemas.auth import ForgotPasswordResetPayload
from app.schemas.auth import LoginPayload
from app.schemas.auth import RegisterPayload
from app.services.auth_service import auth_service


router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/me")
def auth_me(
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    current_user = auth_service.get_by_id(db, user["sub"])
    data = current_user or {
        "id": user.get("sub"),
        "auth_user_id": user.get("auth_user_id"),
        "phone_number": user.get("phone_number"),
        "role": user.get("role"),
    }
    return success_response(
        message="Current user fetched successfully",
        data=data,
    )


@router.post("/register")
def register(
    payload: RegisterPayload,
    db: Session = Depends(get_db),
) -> dict:
    user = auth_service.register_customer(
        db,
        full_name=payload.full_name,
        phone_number=payload.phone_number,
        password=payload.password,
    )
    return success_response(
        message="Registration successful",
        data={
            "access_token": auth_service.token_for(user),
            "token_type": "bearer",
            "role": user["role"],
            "phone_number": user["phone_number"],
            "user_id": user["id"],
        },
    )


@router.post("/login")
def login(
    payload: LoginPayload,
    db: Session = Depends(get_db),
) -> dict:
    user = auth_service.login(
        db,
        phone_number=payload.phone_number,
        password=payload.password,
    )
    if user is None:
        raise UnauthorizedError("Invalid credentials")

    return success_response(
        message="Login successful",
        data={
            "access_token": auth_service.token_for(user),
            "token_type": "bearer",
            "role": user["role"],
            "phone_number": user["phone_number"],
            "user_id": user["id"],
        },
    )


@router.post("/dev-login", include_in_schema=False)
def dev_login(
    payload: DevLoginPayload,
    db: Session = Depends(get_db),
) -> dict:
    if not settings.enable_dev_auth:
        raise NotFoundError("Route not found")

    user = auth_service.dev_login(db, role=payload.role)
    return success_response(
        message="Dev login successful",
        data={
            "access_token": auth_service.token_for(user),
            "token_type": "bearer",
            "role": user["role"],
            "phone_number": user["phone_number"],
            "user_id": user["id"],
        },
    )


@router.post("/forgot-password/request-code")
def request_forgot_password_code(
    payload: ForgotPasswordRequestPayload,
    db: Session = Depends(get_db),
) -> dict:
    data = auth_service.issue_password_reset_code(
        db,
        phone_number=payload.phone_number,
    )
    return success_response(
        message="Verification code sent if the account exists",
        data=data,
    )


@router.post("/forgot-password/reset")
def reset_forgot_password(
    payload: ForgotPasswordResetPayload,
    db: Session = Depends(get_db),
) -> dict:
    auth_service.reset_password_with_code(
        db,
        phone_number=payload.phone_number,
        verification_code=payload.verification_code,
        new_password=payload.new_password,
    )
    return success_response(
        message="Password reset successful",
        data={},
    )
