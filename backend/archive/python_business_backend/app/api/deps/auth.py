from fastapi import Depends
from fastapi import HTTPException
from fastapi import status
from fastapi.security import HTTPAuthorizationCredentials
from fastapi.security import HTTPBearer

from app.core.constants import UserRole
from app.integrations.token_auth import verify_access_token


security = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
) -> dict:
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing bearer token",
        )

    payload = verify_access_token(credentials.credentials)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid access token",
        )

    return payload


def require_role(user: dict, *roles: UserRole) -> dict:
    allowed_roles = {role.value for role in roles}
    if user.get("role") not in allowed_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions for this resource",
        )
    return user


def get_current_customer(user: dict = Depends(get_current_user)) -> dict:
    return require_role(user, UserRole.CUSTOMER)


def get_current_admin(user: dict = Depends(get_current_user)) -> dict:
    return require_role(user, UserRole.ADMIN)
