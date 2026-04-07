from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from app.config.settings import get_settings
from app.shared.errors import BadRequestError


ALLOWED_IMAGE_CONTENT_TYPES = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}
MAX_UPLOAD_BYTES = 5 * 1024 * 1024


def save_booking_update_photo(
    *,
    content: bytes,
    content_type: str | None,
    original_name: str | None,
) -> str:
    if not content:
        raise BadRequestError("Uploaded photo is empty")
    if len(content) > MAX_UPLOAD_BYTES:
        raise BadRequestError("Uploaded photo must be 5 MB or smaller")

    extension = ALLOWED_IMAGE_CONTENT_TYPES.get(content_type or "")
    if extension is None:
        raise BadRequestError("Uploaded photo must be a JPG, PNG, or WEBP image")

    safe_stem = Path(original_name or "booking-photo").stem[:60] or "booking-photo"
    file_name = f"{uuid4().hex}-{safe_stem}{extension}"
    relative_path = Path("booking-updates") / file_name
    destination = get_settings().upload_root_path / relative_path
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(content)
    return relative_path.as_posix()
