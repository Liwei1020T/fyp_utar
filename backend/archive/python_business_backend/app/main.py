from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi import Depends
from fastapi.encoders import jsonable_encoder
from fastapi import HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.requests import Request
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.health import health_payload
from app.api.responses import error_payload
from app.api.v1.router import router as api_v1_router
from app.core.config import settings
from app.core.exceptions import AppError
from app.db.session import get_db
from app.db.session import SessionLocal
from app.services.auth_service import auth_service


@asynccontextmanager
async def lifespan(_: FastAPI):
    with SessionLocal() as db:
        health_payload(db)
        auth_service.ensure_seed_admin(db)
        db.commit()
    yield


app = FastAPI(title=settings.app_name, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(AppError)
async def handle_app_error(_: Request, exc: AppError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content=error_payload(
            message=exc.message,
            code=exc.code,
            details=exc.details,
        ),
    )


@app.exception_handler(HTTPException)
async def handle_http_exception(_: Request, exc: HTTPException) -> JSONResponse:
    message = str(exc.detail)
    return JSONResponse(
        status_code=exc.status_code,
        content=error_payload(
            message=message,
            code="http_error",
            details={"detail": exc.detail},
        ),
    )


@app.exception_handler(RequestValidationError)
async def handle_validation_error(
    _: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    encoded_errors = jsonable_encoder(
        exc.errors(),
        custom_encoder={
            ValueError: str,
            Exception: str,
        },
    )
    return JSONResponse(
        status_code=422,
        content=error_payload(
            message="Validation error",
            code="validation_error",
            details=encoded_errors,
        ),
    )


@app.exception_handler(IntegrityError)
async def handle_integrity_error(_: Request, exc: IntegrityError) -> JSONResponse:
    return JSONResponse(
        status_code=409,
        content=error_payload(
            message="Database integrity error",
            code="integrity_error",
            details={"detail": str(exc.orig)},
        ),
    )


@app.get("/health")
def health_check(db: Session = Depends(get_db)) -> dict[str, str]:
    return health_payload(db)


app.include_router(api_v1_router, prefix=settings.api_v1_prefix)
