from __future__ import annotations

from dataclasses import dataclass

from app.domain.profile.entities import PlayerProfile
from app.ports.repositories.profile_repository import ProfileRepository


@dataclass
class UpsertMyProfileUseCase:
    profile_repository: ProfileRepository

    def execute(self, profile: PlayerProfile) -> PlayerProfile:
        return self.profile_repository.upsert(profile)

