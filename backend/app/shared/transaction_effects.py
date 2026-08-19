from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass
from dataclasses import field
from typing import cast

from sqlalchemy.orm import Session


logger = logging.getLogger(__name__)
_EFFECTS_KEY = "stringsense.transaction_effects"
FileCleanup = Callable[[str], None]


@dataclass
class TransactionEffects:
    created_files: list[tuple[str, FileCleanup]] = field(default_factory=list)
    removed_files: list[tuple[str, FileCleanup]] = field(default_factory=list)

    def rollback(self) -> None:
        for relative_path, cleanup in self.created_files:
            self._cleanup(relative_path, cleanup)
        self._clear()

    def commit(self) -> None:
        for relative_path, cleanup in self.removed_files:
            self._cleanup(relative_path, cleanup)
        self._clear()

    @staticmethod
    def _cleanup(relative_path: str, cleanup: FileCleanup) -> None:
        try:
            cleanup(relative_path)
        except Exception:
            logger.exception("Transaction file cleanup failed for %s", relative_path)

    def _clear(self) -> None:
        self.created_files.clear()
        self.removed_files.clear()


def _get_effects(db: Session) -> TransactionEffects:
    effects = db.info.get(_EFFECTS_KEY)
    if effects is None:
        effects = TransactionEffects()
        db.info[_EFFECTS_KEY] = effects
    return cast(TransactionEffects, effects)


def register_created_file(
    db: Session,
    relative_path: str,
    cleanup: FileCleanup,
) -> None:
    _get_effects(db).created_files.append((relative_path, cleanup))


def register_removed_file(
    db: Session,
    relative_path: str,
    cleanup: FileCleanup,
) -> None:
    _get_effects(db).removed_files.append((relative_path, cleanup))


def commit_transaction_effects(db: Session) -> None:
    effects = cast(TransactionEffects | None, db.info.pop(_EFFECTS_KEY, None))
    if effects is not None:
        effects.commit()


def rollback_transaction_effects(db: Session) -> None:
    effects = cast(TransactionEffects | None, db.info.pop(_EFFECTS_KEY, None))
    if effects is not None:
        effects.rollback()
