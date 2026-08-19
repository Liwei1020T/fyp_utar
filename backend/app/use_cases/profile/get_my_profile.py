from __future__ import annotations

from dataclasses import dataclass

from app.domain.profile.entities import PlayerProfile
from app.ports.repositories.profile_repository import ProfileRepository


@dataclass
class GetMyProfileUseCase:
    profile_repository: ProfileRepository

    def execute(self, user_id: str) -> PlayerProfile | None:
        return self.profile_repository.get_by_user_id(user_id)
