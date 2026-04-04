from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import Depends
from fastapi import FastAPI
from fastapi import HTTPException
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.requests import Request
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from stringsense_backend.api.router import router as api_router
from stringsense_backend.core.config import get_settings
from stringsense_backend.core.errors import AppError
from stringsense_backend.core.http import error_payload
from stringsense_backend.db.seed import ensure_catalog_seeded
from stringsense_backend.db.seed import ensure_seed_users
from stringsense_backend.db.session import SessionLocal
from stringsense_backend.db.session import create_all_tables
from stringsense_backend.db.session import get_db
from stringsense_backend.modules.health import health_payload


@asynccontextmanager
async def lifespan(_: FastAPI):
    settings = get_settings()
    if settings.auto_create_schema:
        create_all_tables()

    with SessionLocal() as db:
        ensure_seed_users(db)
        ensure_catalog_seeded(db)
        db.commit()
    yield


settings = get_settings()
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
            code=exc.code,
            message=exc.message,
            details=exc.details,
        ),
    )


@app.exception_handler(RequestValidationError)
async def handle_validation_error(
    _: Request, exc: RequestValidationError
) -> JSONResponse:
    return JSONResponse(
        status_code=422,
        content=error_payload(
            code="validation_error",
            message="Validation error",
            details=jsonable_encoder(exc.errors(), custom_encoder={Exception: str}),
        ),
    )


@app.exception_handler(HTTPException)
async def handle_http_exception(_: Request, exc: HTTPException) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content=error_payload(
            code="http_error",
            message=str(exc.detail),
            details={"detail": exc.detail},
        ),
    )


@app.exception_handler(IntegrityError)
async def handle_integrity_error(_: Request, exc: IntegrityError) -> JSONResponse:
    return JSONResponse(
        status_code=409,
        content=error_payload(
            code="integrity_error",
            message="Database integrity error",
            details={"detail": str(exc.orig)},
        ),
    )


@app.get("/health")
def root_health(db: Session = Depends(get_db)) -> dict[str, object]:
    return health_payload(db)


app.include_router(api_router, prefix=settings.api_v1_prefix)
