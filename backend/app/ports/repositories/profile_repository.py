from __future__ import annotations

from typing import Protocol

from app.domain.profile.entities import PlayerProfile


class ProfileRepository(Protocol):
    def get_by_user_id(self, user_id: str) -> PlayerProfile | None: ...

    def upsert(
        self,
        profile: PlayerProfile,
        *,
        username: str | None = None,
    ) -> PlayerProfile: ...
