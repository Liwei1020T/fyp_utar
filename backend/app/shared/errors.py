from __future__ import annotations

from typing import Any


class AppError(Exception):
    def __init__(
        self,
        message: str,
        *,
        status_code: int,
        code: str,
        details: Any | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.code = code
        self.details = details


class BadRequestError(AppError):
    def __init__(self, message: str, *, details: Any | None = None) -> None:
        super().__init__(
            message,
            status_code=400,
            code="bad_request",
            details=details,
        )


class UnauthorizedError(AppError):
    def __init__(self, message: str = "Authentication required") -> None:
        super().__init__(message, status_code=401, code="unauthorized")


class ForbiddenError(AppError):
    def __init__(self, message: str = "Forbidden") -> None:
        super().__init__(message, status_code=403, code="forbidden")


class NotFoundError(AppError):
    def __init__(self, message: str, *, details: Any | None = None) -> None:
        super().__init__(
            message,
            status_code=404,
            code="not_found",
            details=details,
        )


class ConflictError(AppError):
    def __init__(self, message: str, *, details: Any | None = None) -> None:
        super().__init__(
            message,
            status_code=409,
            code="conflict",
            details=details,
        )


class TooManyRequestsError(AppError):
    def __init__(self, message: str = "Too many attempts; try again later") -> None:
        super().__init__(message, status_code=429, code="rate_limited")


class ServiceUnavailableError(AppError):
    def __init__(self, message: str = "Service temporarily unavailable") -> None:
        super().__init__(message, status_code=503, code="service_unavailable")
