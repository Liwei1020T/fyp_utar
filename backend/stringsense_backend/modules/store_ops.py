from __future__ import annotations

from app.entrypoints.api.routes.admin_routes import router as admin_router
from app.entrypoints.api.routes.store_routes import router as public_router

__all__ = ["admin_router", "public_router"]
