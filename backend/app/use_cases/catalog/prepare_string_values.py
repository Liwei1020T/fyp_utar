from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from stringsense_backend.db.catalog_seed import merge_with_approved_defaults


@dataclass
class PrepareStringValuesUseCase:
    approved_strings_path: Path

    def execute(
        self,
        *,
        brand: str,
        model_name: str,
        overrides: dict[str, object],
    ) -> dict[str, object]:
        return merge_with_approved_defaults(
            self.approved_strings_path,
            brand=brand,
            model_name=model_name,
            overrides=overrides,
        )
