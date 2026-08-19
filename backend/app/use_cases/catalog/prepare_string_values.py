from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import cast

from app.shared.errors import BadRequestError


@dataclass
class PrepareStringValuesUseCase:
    approved_strings_path: Path
    approved_catalog_ids: frozenset[str]
    merge_defaults: Callable[..., dict[str, object]]

    def execute(
        self,
        *,
        brand: str,
        model_name: str,
        overrides: dict[str, object],
    ) -> dict[str, object]:
        try:
            values = self.merge_defaults(
                self.approved_strings_path,
                brand=brand,
                model_name=model_name,
                overrides=overrides,
            )
        except ValueError as error:
            raise BadRequestError(str(error)) from error
        catalog = cast(dict[str, object], values["catalog"])
        if str(catalog["catalog_id"]) not in self.approved_catalog_ids:
            raise BadRequestError("Only the 12 approved system strings may be used")
        return values
