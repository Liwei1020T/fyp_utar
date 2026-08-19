from __future__ import annotations

import hashlib
import hmac
from datetime import UTC
from datetime import datetime
from datetime import timedelta
from pathlib import Path
from urllib.parse import quote
from uuid import uuid4

from app.config.settings import get_settings
from app.shared.errors import BadRequestError


ALLOWED_IMAGE_CONTENT_TYPES = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}
MAX_UPLOAD_BYTES = 5 * 1024 * 1024
BOOKING_UPDATES_DIR = "booking-updates"
STRING_IMAGES_DIR = "string-images"
PAYMENT_QR_DIR = "payment-qr"
PAYMENT_PROOFS_DIR = "payment-proofs"
SIGNED_MEDIA_URL_TTL = timedelta(hours=12)
PAYMENT_PROOF_SIGNED_MEDIA_URL_TTL = timedelta(minutes=15)


def _detect_image_extension(content: bytes) -> str | None:
    if content.startswith(b"\xff\xd8\xff"):
        return ".jpg"
    if content.startswith(b"\x89PNG\r\n\x1a\n"):
        return ".png"
    if len(content) >= 12 and content[:4] == b"RIFF" and content[8:12] == b"WEBP":
        return ".webp"
    return None


def _validate_image_payload(
    *,
    content: bytes,
    content_type: str | None,
    empty_message: str,
    oversize_message: str,
    invalid_type_message: str,
) -> str:
    if not content:
        raise BadRequestError(empty_message)
    if len(content) > MAX_UPLOAD_BYTES:
        raise BadRequestError(oversize_message)

    declared_extension = ALLOWED_IMAGE_CONTENT_TYPES.get(content_type or "")
    detected_extension = _detect_image_extension(content)
    if (
        declared_extension is None
        or detected_extension is None
        or declared_extension != detected_extension
    ):
        raise BadRequestError(invalid_type_message)
    return detected_extension


def _resolve_upload_destination(
    relative_path: str,
    *,
    expected_directory: str,
) -> Path | None:
    if "://" in relative_path:
        return None

    candidate = Path(relative_path)
    if candidate.is_absolute():
        return None

    root = get_settings().upload_root_path.resolve()
    destination = (root / candidate).resolve()
    try:
        relative_to_root = destination.relative_to(root)
    except ValueError:
        return None

    if not relative_to_root.parts or relative_to_root.parts[0] != expected_directory:
        return None
    return destination


def resolve_upload_media_path(relative_path: str) -> Path | None:
    if "://" in relative_path:
        return None

    candidate = Path(relative_path)
    if candidate.is_absolute():
        return None

    root = get_settings().upload_root_path.resolve()
    destination = (root / candidate).resolve()
    try:
        relative_to_root = destination.relative_to(root)
    except ValueError:
        return None

    if not relative_to_root.parts:
        return None

    top_level = relative_to_root.parts[0]
    if top_level not in {
        BOOKING_UPDATES_DIR,
        STRING_IMAGES_DIR,
        PAYMENT_QR_DIR,
        PAYMENT_PROOFS_DIR,
    }:
        return None

    return destination


def build_signed_media_url(
    relative_path: str,
    *,
    ttl: timedelta = SIGNED_MEDIA_URL_TTL,
) -> str:
    if "://" in relative_path or relative_path.startswith("/"):
        return relative_path
    if resolve_upload_media_path(relative_path) is None:
        return relative_path

    expires_at = int((datetime.now(UTC) + ttl).timestamp())
    payload = f"{relative_path}:{expires_at}".encode("utf-8")
    secret = get_settings().jwt_secret_key or ""
    signature = hmac.new(
        secret.encode("utf-8"),
        payload,
        hashlib.sha256,
    ).hexdigest()
    encoded_path = quote(relative_path, safe="/")
    return f"/api/media/{encoded_path}?exp={expires_at}&sig={signature}"


def verify_signed_media_request(relative_path: str, *, exp: int, sig: str) -> bool:
    if exp < int(datetime.now(UTC).timestamp()):
        return False

    payload = f"{relative_path}:{exp}".encode("utf-8")
    secret = get_settings().jwt_secret_key or ""
    expected_signature = hmac.new(
        secret.encode("utf-8"),
        payload,
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(expected_signature, sig)


def save_booking_update_photo(
    *,
    content: bytes,
    content_type: str | None,
    original_name: str | None,
) -> str:
    extension = _validate_image_payload(
        content=content,
        content_type=content_type,
        empty_message="Uploaded photo is empty",
        oversize_message="Uploaded photo must be 5 MB or smaller",
        invalid_type_message="Uploaded photo must be a valid JPG, PNG, or WEBP image",
    )

    safe_stem = Path(original_name or "booking-photo").stem[:60] or "booking-photo"
    file_name = f"{uuid4().hex}-{safe_stem}{extension}"
    relative_path = Path(BOOKING_UPDATES_DIR) / file_name
    destination = get_settings().upload_root_path / relative_path
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(content)
    return relative_path.as_posix()


def delete_booking_update_photo(relative_path: str | None) -> None:
    if not relative_path:
        return

    destination = _resolve_upload_destination(
        relative_path,
        expected_directory=BOOKING_UPDATES_DIR,
    )
    if destination is None:
        return

    try:
        destination.unlink(missing_ok=True)
    except OSError:
        # Upload cleanup is best-effort; the original request error should still win.
        return


def save_string_catalog_image(
    *,
    content: bytes,
    content_type: str | None,
    original_name: str | None,
) -> str:
    extension = _validate_image_payload(
        content=content,
        content_type=content_type,
        empty_message="Uploaded image is empty",
        oversize_message="Uploaded image must be 5 MB or smaller",
        invalid_type_message="Uploaded image must be a valid JPG, PNG, or WEBP image",
    )

    safe_stem = Path(original_name or "string-image").stem[:60] or "string-image"
    file_name = f"{uuid4().hex}-{safe_stem}{extension}"
    relative_path = Path(STRING_IMAGES_DIR) / file_name
    destination = get_settings().upload_root_path / relative_path
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(content)
    return relative_path.as_posix()


def delete_string_catalog_image(relative_path: str | None) -> None:
    if not relative_path:
        return

    destination = _resolve_upload_destination(
        relative_path,
        expected_directory=STRING_IMAGES_DIR,
    )
    if destination is None:
        return

    try:
        destination.unlink(missing_ok=True)
    except OSError:
        return


def _save_payment_image(
    *,
    content: bytes,
    content_type: str | None,
    original_name: str | None,
    directory: str,
    empty_message: str,
    invalid_type_message: str,
) -> str:
    extension = _validate_image_payload(
        content=content,
        content_type=content_type,
        empty_message=empty_message,
        oversize_message="Payment image must be 5 MB or smaller",
        invalid_type_message=invalid_type_message,
    )
    safe_stem = Path(original_name or "payment-image").stem[:60] or "payment-image"
    relative_path = Path(directory) / f"{uuid4().hex}-{safe_stem}{extension}"
    destination = get_settings().upload_root_path / relative_path
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(content)
    return relative_path.as_posix()


def save_payment_qr(
    *,
    content: bytes,
    content_type: str | None,
    original_name: str | None,
) -> str:
    return _save_payment_image(
        content=content,
        content_type=content_type,
        original_name=original_name,
        directory=PAYMENT_QR_DIR,
        empty_message="Payment QR image is empty",
        invalid_type_message="Payment QR must be a valid JPG, PNG, or WEBP image",
    )


def delete_payment_qr(relative_path: str | None) -> None:
    if not relative_path:
        return
    destination = _resolve_upload_destination(
        relative_path,
        expected_directory=PAYMENT_QR_DIR,
    )
    if destination is None:
        return
    try:
        destination.unlink(missing_ok=True)
    except OSError:
        return


def save_payment_proof(
    *,
    content: bytes,
    content_type: str | None,
    original_name: str | None,
) -> str:
    return _save_payment_image(
        content=content,
        content_type=content_type,
        original_name=original_name,
        directory=PAYMENT_PROOFS_DIR,
        empty_message="Payment proof image is empty",
        invalid_type_message="Payment proof must be a valid JPG, PNG, or WEBP image",
    )


def delete_payment_proof(relative_path: str | None) -> None:
    if not relative_path:
        return
    destination = _resolve_upload_destination(
        relative_path,
        expected_directory=PAYMENT_PROOFS_DIR,
    )
    if destination is None:
        return
    try:
        destination.unlink(missing_ok=True)
    except OSError:
        return
