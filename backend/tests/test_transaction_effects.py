from __future__ import annotations

import asyncio
from collections.abc import Generator
from pathlib import Path
from typing import cast

import pytest
from sqlalchemy.orm import Session

from app.adapters.persistence.sqlalchemy.session import get_db
from app.shared.transaction_effects import register_created_file
from app.shared.transaction_effects import register_removed_file


def _delete_file(path: str) -> None:
    Path(path).unlink(missing_ok=True)


def test_filesystem_effects_commit_after_database_commit(tmp_path) -> None:
    created = tmp_path / "new.jpg"
    replaced = tmp_path / "old.jpg"
    created.write_bytes(b"new")
    replaced.write_bytes(b"old")

    db_generator = get_db()
    db = next(db_generator)
    register_created_file(db, str(created), _delete_file)
    register_removed_file(db, str(replaced), _delete_file)

    with pytest.raises(StopIteration):
        next(db_generator)

    assert created.exists()
    assert not replaced.exists()


def test_filesystem_effects_rollback_on_commit_failure(monkeypatch, tmp_path) -> None:
    created = tmp_path / "new.jpg"
    replaced = tmp_path / "old.jpg"
    created.write_bytes(b"new")
    replaced.write_bytes(b"old")

    def fail_commit(_: Session) -> None:
        raise RuntimeError("forced commit failure")

    monkeypatch.setattr(Session, "commit", fail_commit)
    db_generator = get_db()
    db = next(db_generator)
    register_created_file(db, str(created), _delete_file)
    register_removed_file(db, str(replaced), _delete_file)

    with pytest.raises(RuntimeError, match="forced commit failure"):
        next(db_generator)

    assert not created.exists()
    assert replaced.exists()


def test_filesystem_effects_rollback_on_cancellation(tmp_path) -> None:
    created = tmp_path / "cancelled.jpg"
    created.write_bytes(b"new")

    db_generator = cast(Generator[Session, None, None], get_db())
    db = next(db_generator)
    register_created_file(db, str(created), _delete_file)

    with pytest.raises(asyncio.CancelledError):
        db_generator.throw(asyncio.CancelledError())

    assert not created.exists()
