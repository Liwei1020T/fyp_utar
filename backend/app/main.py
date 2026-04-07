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
from fastapi.staticfiles import StaticFiles
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.adapters.persistence.sqlalchemy.seed import ensure_catalog_seeded
from app.adapters.persistence.sqlalchemy.seed import ensure_seed_users
from app.adapters.persistence.sqlalchemy.seed import ensure_store_defaults
from app.adapters.persistence.sqlalchemy.session import SessionLocal
from app.adapters.persistence.sqlalchemy.session import check_database_connection
from app.adapters.persistence.sqlalchemy.session import create_all_tables
from app.adapters.persistence.sqlalchemy.session import get_db
from app.config.settings import get_settings
from app.entrypoints.api.router import router as api_router
from app.shared.errors import AppError
from app.shared.http import error_payload


@asynccontextmanager
async def lifespan(_: FastAPI):
    settings = get_settings()
    if settings.auto_create_schema:
        create_all_tables()

    with SessionLocal() as db:
        ensure_seed_users(db)
        ensure_catalog_seeded(db)
        ensure_store_defaults(db)
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

settings.upload_root_path.mkdir(parents=True, exist_ok=True)
app.mount(
    "/media",
    StaticFiles(directory=str(settings.upload_root_path)),
    name="media",
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
    _: Request,
    exc: RequestValidationError,
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
    check_database_connection(db)
    return {"status": "ok", "service": "backend"}


app.include_router(api_router, prefix=settings.api_prefix)
