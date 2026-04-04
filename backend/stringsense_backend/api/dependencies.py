from __future__ import annotations

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials
from fastapi.security import HTTPBearer
from pydantic import BaseModel

from stringsense_backend.core.domain import UserRole
from stringsense_backend.core.errors import ForbiddenError
from stringsense_backend.core.errors import UnauthorizedError
from stringsense_backend.core.security import verify_access_token


class CurrentUser(BaseModel):
    sub: str
    user_id: str
    phone_number: str
    role: str


security = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
) -> CurrentUser:
    if credentials is None:
        raise UnauthorizedError("Missing bearer token")

    payload = verify_access_token(credentials.credentials)
    if payload is None:
        raise UnauthorizedError("Invalid access token")

    return CurrentUser(**payload)


def require_roles(user: CurrentUser, *roles: UserRole) -> CurrentUser:
    allowed = {role.value for role in roles}
    if user.role not in allowed:
        raise ForbiddenError("Insufficient permissions for this resource")
    return user


def get_current_customer(user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
    return require_roles(user, UserRole.CUSTOMER, UserRole.ADMIN)


def get_current_admin(user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
    return require_roles(user, UserRole.ADMIN)
