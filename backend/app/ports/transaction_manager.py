from __future__ import annotations

from typing import Protocol


class TransactionManager(Protocol):
    def commit(self) -> None: ...

    def rollback(self) -> None: ...
