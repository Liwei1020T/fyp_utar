from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path


@dataclass
class PrepareStringValuesUseCase:
    approved_strings_path: Path
    merge_defaults: Callable[..., dict[str, object]]

    def execute(
        self,
        *,
        brand: str,
        model_name: str,
        overrides: dict[str, object],
    ) -> dict[str, object]:
        return self.merge_defaults(
            self.approved_strings_path,
            brand=brand,
            model_name=model_name,
            overrides=overrides,
        )
