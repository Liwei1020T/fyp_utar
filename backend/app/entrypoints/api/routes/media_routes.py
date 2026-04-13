from __future__ import annotations

from fastapi import APIRouter
from fastapi import Query
from fastapi.responses import FileResponse

from app.shared.errors import NotFoundError
from app.shared.upload_storage import resolve_upload_media_path
from app.shared.upload_storage import verify_signed_media_request


router = APIRouter(tags=["media"])


@router.get("/media/{media_path:path}")
def get_media_file(
    media_path: str,
    exp: int = Query(..., ge=0),
    sig: str = Query(..., min_length=64, max_length=128),
) -> FileResponse:
    if not verify_signed_media_request(media_path, exp=exp, sig=sig):
        raise NotFoundError("Media not found")

    destination = resolve_upload_media_path(media_path)
    if destination is None or not destination.is_file():
        raise NotFoundError("Media not found")

    return FileResponse(destination)
