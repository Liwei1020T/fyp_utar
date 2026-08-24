from __future__ import annotations

from dataclasses import dataclass
from typing import cast

from pydantic import ValidationError

from app.domain.catalog.entities import StringItem
from app.domain.recommendation.entities import RecommendationRequestModel
from app.domain.recommendation.scoring import CORE_RECOMMENDATION_FEATURES
from app.dto.agent import AgentWhatIfChangesDto
from app.dto.agent import AgentToolResult
from app.dto.catalog import official_performance_to_dto
from app.dto.store import business_hours_to_dto
from app.dto.store import settings_to_dto
from app.dto.recommendation import recommendation_response_to_dto
from app.ports.repositories.booking_repository import BookingRepository
from app.ports.repositories.catalog_repository import CatalogRepository
from app.ports.repositories.profile_repository import ProfileRepository
from app.ports.repositories.recommendation_log_repository import (
    RecommendationLogRepository,
)
from app.ports.repositories.store_repository import StoreRepository
from app.ports.repositories.recommendation_repository import RecommendationRepository
from app.shared.errors import BadRequestError
from app.shared.errors import NotFoundError
from app.use_cases.store.get_business_hours import GetBusinessHoursUseCase
from app.use_cases.store.get_store_settings import GetStoreSettingsUseCase
from app.use_cases.recommendation.generate_recommendation import (
    GenerateRecommendationUseCase,
)


ALL_AGENT_TOOL_SPECS: tuple[dict[str, object], ...] = (
    {
        "name": "get_string_details",
        "description": "Get approved catalog, performance, price, and stock facts for one string.",
        "parameters": {
            "type": "object",
            "properties": {"catalog_id": {"type": "string"}},
            "required": ["catalog_id"],
            "additionalProperties": False,
        },
    },
    {
        "name": "compare_strings",
        "description": "Compare two or three approved strings by catalog ID or exact display name using the same catalog fields.",
        "parameters": {
            "type": "object",
            "properties": {
                "catalog_ids": {
                    "type": "array",
                    "items": {"type": "string"},
                    "minItems": 2,
                    "maxItems": 3,
                }
            },
            "required": ["catalog_ids"],
            "additionalProperties": False,
        },
    },
    {
        "name": "get_review_evidence",
        "description": "Get promoted NLP review evidence for one approved string.",
        "parameters": {
            "type": "object",
            "properties": {
                "catalog_id": {"type": "string"},
                "aspects": {
                    "type": "array",
                    "items": {"type": "string"},
                    "maxItems": 9,
                },
            },
            "required": ["catalog_id"],
            "additionalProperties": False,
        },
    },
    {
        "name": "get_recommendation_run_context",
        "description": "Get the current player's exact saved recommendation run and rationale.",
        "parameters": {
            "type": "object",
            "properties": {
                "run_id": {"type": "string"},
                "catalog_id": {"type": "string"},
            },
            "required": ["run_id"],
            "additionalProperties": False,
        },
    },
    {
        "name": "get_store_information",
        "description": "Get live customer-facing store settings and business hours.",
        "parameters": {
            "type": "object",
            "properties": {},
            "additionalProperties": False,
        },
    },
    {
        "name": "get_my_bookings",
        "description": "Get the current player's booking status, optionally for one booking.",
        "parameters": {
            "type": "object",
            "properties": {"booking_id": {"type": "string"}},
            "additionalProperties": False,
        },
    },
    {
        "name": "get_my_string_preferences",
        "description": "Get the current player's saved string preferences for guided selection.",
        "parameters": {
            "type": "object",
            "properties": {},
            "additionalProperties": False,
        },
    },
    {
        "name": "get_my_recommendations",
        "description": "Get the current player's latest current cached V11 recommendations.",
        "parameters": {
            "type": "object",
            "properties": {},
            "additionalProperties": False,
        },
    },
    {
        "name": "preview_recommendation_what_if",
        "description": "Run a V11 simulation with explicit profile changes without updating the saved profile or recommendation cache.",
        "parameters": {
            "type": "object",
            "properties": {
                "changes": {
                    "type": "object",
                    "properties": {
                        "skill_level": {
                            "type": "string",
                            "enum": ["beginner", "intermediate", "advanced"],
                        },
                        "playing_style": {
                            "type": "string",
                            "enum": ["attacking", "balanced", "control_defensive"],
                        },
                        "preferred_tension": {
                            "type": "number",
                            "minimum": 16,
                            "maximum": 35,
                        },
                        "frequency_per_week": {
                            "type": "integer",
                            "minimum": 0,
                            "maximum": 14,
                        },
                        "preferred_feel": {
                            "type": "string",
                            "enum": ["soft", "medium", "hard"],
                        },
                        "preferred_gauge": {
                            "type": "string",
                            "enum": ["no_preference", "thin", "medium", "thick"],
                        },
                        "recent_goal": {
                            "type": "string",
                            "enum": [
                                "balanced",
                                "power",
                                "control",
                                "durability",
                                "comfort",
                                "tension_retention",
                                "value_for_money",
                            ],
                        },
                        "attack": {"type": "integer", "minimum": 1, "maximum": 10},
                        "comfort": {"type": "integer", "minimum": 1, "maximum": 10},
                        "control": {"type": "integer", "minimum": 1, "maximum": 10},
                        "durability": {"type": "integer", "minimum": 1, "maximum": 10},
                        "elasticity": {"type": "integer", "minimum": 1, "maximum": 10},
                        "sound": {"type": "integer", "minimum": 1, "maximum": 10},
                        "string_movement": {
                            "type": "integer",
                            "minimum": 1,
                            "maximum": 10,
                        },
                        "tension_retention": {
                            "type": "integer",
                            "minimum": 1,
                            "maximum": 10,
                        },
                        "value_for_money": {
                            "type": "integer",
                            "minimum": 1,
                            "maximum": 10,
                        },
                        "budget_rm": {
                            "type": "number",
                            "minimum": 0,
                            "maximum": 1000,
                        },
                        "racket_id": {"type": "string"},
                    },
                    "additionalProperties": False,
                }
            },
            "required": ["changes"],
            "additionalProperties": False,
        },
    },
    {
        "name": "find_in_stock_alternatives",
        "description": "Find up to three similar approved strings that are currently in stock.",
        "parameters": {
            "type": "object",
            "properties": {
                "catalog_id": {"type": "string"},
                "budget_rm": {
                    "type": "number",
                    "minimum": 0,
                    "maximum": 1000,
                },
            },
            "required": ["catalog_id"],
            "additionalProperties": False,
        },
    },
)


# FYP scope: uncomment a deferred name here to expose its preserved tool again.
ACTIVE_AGENT_TOOL_NAMES = {
    "get_string_details",
    "compare_strings",
    # "get_review_evidence",
    # "get_recommendation_run_context",  # Still used as trusted page preload.
    "get_store_information",
    # "get_my_bookings",
    # "get_my_string_preferences",
    # "get_my_recommendations",
    "preview_recommendation_what_if",
    "find_in_stock_alternatives",
}
AGENT_TOOL_SPECS = tuple(
    spec for spec in ALL_AGENT_TOOL_SPECS if spec["name"] in ACTIVE_AGENT_TOOL_NAMES
)


@dataclass
class AgentToolbox:
    catalog_repository: CatalogRepository
    recommendation_log_repository: RecommendationLogRepository
    store_repository: StoreRepository
    booking_repository: BookingRepository
    profile_repository: ProfileRepository
    recommendation_repository: RecommendationRepository

    def execute(
        self,
        *,
        name: str,
        arguments: dict[str, object],
        user_id: str,
    ) -> AgentToolResult:
        if name == "get_string_details":
            return self.get_string_details(_required_string(arguments, "catalog_id"))
        if name == "compare_strings":
            return self.compare_strings(_string_list(arguments, "catalog_ids", 2, 3))
        if name == "get_review_evidence":
            return self.get_review_evidence(
                _required_string(arguments, "catalog_id"),
                _string_list(arguments, "aspects", 0, 9),
            )
        if name == "get_recommendation_run_context":
            return self.get_recommendation_run_context(
                user_id=user_id,
                run_id=_required_string(arguments, "run_id"),
                catalog_id=_optional_string(arguments, "catalog_id"),
            )
        if name == "get_store_information":
            return self.get_store_information()
        if name == "get_my_bookings":
            return self.get_my_bookings(
                user_id=user_id,
                booking_id=_optional_string(arguments, "booking_id"),
            )
        if name == "get_my_string_preferences":
            return self.get_my_string_preferences(user_id=user_id)
        if name == "get_my_recommendations":
            return self.get_my_recommendations(user_id=user_id)
        if name == "preview_recommendation_what_if":
            return self.preview_recommendation_what_if(
                user_id=user_id,
                raw_changes=arguments.get("changes"),
            )
        if name == "find_in_stock_alternatives":
            return self.find_in_stock_alternatives(
                catalog_id=_required_string(arguments, "catalog_id"),
                budget_rm=_optional_number(arguments, "budget_rm"),
            )
        raise BadRequestError("Unknown Agent tool")

    def get_string_details(self, catalog_id: str) -> AgentToolResult:
        item = self.catalog_repository.get_by_id(catalog_id)
        if item is None or not item.is_active:
            raise NotFoundError("String not found")
        catalog = {
            "id": item.id,
            "brand": item.brand,
            "display_name": item.display_name,
            "model_name": item.model_name,
            "series_label": item.series_label,
            "is_hybrid": item.is_hybrid,
            "gauge_main_mm": item.gauge_main_mm,
            "gauge_cross_mm": item.gauge_cross_mm,
            "gauge_label": item.gauge_label,
            "category": item.category,
            "main_trait": item.main_trait,
            "tension_min_lbs": item.tension_min_lbs,
            "tension_max_lbs": item.tension_max_lbs,
            "material_summary_en": item.material_summary_en,
            "color_options_en": item.color_options_en,
            "short_description": item.short_description,
            "full_description": item.full_description,
            "aspect_scores": item.aspect_scores,
            "price_rm": item.price_rm,
            "inventory": {
                "available_stock": item.available_stock,
                "availability_status": item.inventory.availability_status
                if item.inventory
                else "out_of_stock",
                "pricing_mode": item.inventory.pricing_mode
                if item.inventory
                else "price_pending",
            },
            "official_performance": (
                official_performance_to_dto(item.official_performance).model_dump()
                if item.official_performance
                else None
            ),
        }
        return AgentToolResult(
            data={"string": catalog},
            sources=[_source("catalog", item.id, item.display_name, item.updated_at)],
        )

    def compare_strings(self, catalog_ids: list[str]) -> AgentToolResult:
        catalog_lookup = {
            key.casefold(): item.id
            for item in self.catalog_repository.list_active_catalog()
            for key in (item.id, item.display_name)
        }
        resolved_ids = [
            catalog_lookup.get(catalog_id.casefold(), catalog_id)
            for catalog_id in catalog_ids
        ]
        if len(set(resolved_ids)) != len(resolved_ids):
            raise BadRequestError("String comparison requires distinct catalog IDs")
        results = [self.get_string_details(catalog_id) for catalog_id in resolved_ids]
        return AgentToolResult(
            data={"strings": [result.data["string"] for result in results]},
            sources=[source for result in results for source in result.sources],
        )

    def get_review_evidence(
        self,
        catalog_id: str,
        aspects: list[str],
    ) -> AgentToolResult:
        item = self.catalog_repository.get_by_id(catalog_id)
        if item is None or not item.is_active:
            raise NotFoundError("String not found")
        matrix = self.catalog_repository.get_recommendation_matrix(catalog_id)
        if matrix is None:
            return AgentToolResult(
                data={"catalog_id": catalog_id, "evidence": []},
                sources=[
                    _source("catalog", item.id, item.display_name, item.updated_at)
                ],
            )
        aspect_filter = set(aspects)
        evidence = [
            {
                "feature_key": entry.feature_key,
                "feature_label": entry.feature_label,
                "normalized_score": entry.normalized_score,
                "evidence_note": entry.evidence_note,
                "updated_at": _version(entry.updated_at),
            }
            for entry in matrix.matrix_entries
            if entry.source_layer == "nlp_review"
            and (not aspect_filter or entry.feature_key in aspect_filter)
        ]
        return AgentToolResult(
            data={"catalog_id": catalog_id, "evidence": evidence},
            sources=[
                _source(
                    "nlp_review", catalog_id, f"{item.display_name} review evidence"
                )
            ],
        )

    def get_recommendation_run_context(
        self,
        *,
        user_id: str,
        run_id: str,
        catalog_id: str | None,
    ) -> AgentToolResult:
        run = self.recommendation_log_repository.get_run(run_id)
        if run is None or run.user_id != user_id:
            raise NotFoundError("Recommendation run not found")
        items = [
            {
                "catalog_id": item.catalog_id,
                "rank": item.rank_position,
                "final_score": item.final_score,
                "score_breakdown": item.score_breakdown,
                "rationale": item.rationale,
            }
            for item in run.items
            if catalog_id is None or item.catalog_id == catalog_id
        ]
        if catalog_id is not None and not items:
            raise NotFoundError("Recommendation item not found")
        return AgentToolResult(
            data={
                "run_id": run.id,
                "algorithm_version": run.algorithm_version,
                "generated_at": _version(run.generated_at),
                "request_snapshot": _without_keys(run.request_snapshot, "user_id"),
                "profile_snapshot": _without_keys(run.profile_snapshot, "user_id"),
                "items": items,
            },
            sources=[
                _source(
                    "recommendation_run",
                    run.id,
                    f"Recommendation run {run.id}",
                    run.generated_at,
                )
            ],
        )

    def get_store_information(self) -> AgentToolResult:
        settings = GetStoreSettingsUseCase(self.store_repository).execute()
        hours = GetBusinessHoursUseCase(self.store_repository).execute()
        settings_data = settings_to_dto(settings).model_dump()
        settings_data.pop("notification_settings", None)
        return AgentToolResult(
            data={
                "settings": settings_data,
                "business_hours": business_hours_to_dto(hours).model_dump(),
            },
            sources=[
                _source(
                    "store_settings",
                    settings.id,
                    settings.store_name,
                    settings.updated_at,
                ),
                _source(
                    "business_hours", hours.id, "Store business hours", hours.updated_at
                ),
            ],
        )

    def get_my_bookings(
        self,
        *,
        user_id: str,
        booking_id: str | None,
    ) -> AgentToolResult:
        if booking_id is not None:
            booking = self.booking_repository.get_by_id(booking_id)
            if booking is None or booking.user_id != user_id:
                raise NotFoundError("Booking not found")
            bookings = [booking]
        else:
            bookings = self.booking_repository.list_by_user(user_id).items
        return AgentToolResult(
            data={
                "bookings": [
                    {
                        "id": booking.id,
                        "order_code": booking.order_code,
                        "string_id": booking.string_id,
                        "string_name": booking.string_name,
                        "racket_brand": booking.racket_brand,
                        "racket_model": booking.racket_model,
                        "requested_tension": booking.requested_tension,
                        "drop_off_datetime": _version(booking.drop_off_datetime),
                        "expected_completion_datetime": _version(
                            booking.expected_completion_datetime
                        ),
                        "collection_datetime": _version(booking.collection_datetime),
                        "service_method": booking.service_method,
                        "status": booking.status,
                        "completion_summary": booking.completion_summary,
                        "latest_admin_note": booking.latest_admin_note,
                        "updated_at": _version(booking.updated_at),
                    }
                    for booking in bookings
                ]
            },
            sources=[
                _source("booking", booking.id, booking.order_code, booking.updated_at)
                for booking in bookings
            ],
        )

    def get_my_recommendations(self, *, user_id: str) -> AgentToolResult:
        response = GenerateRecommendationUseCase(
            profile_repository=self.profile_repository,
            recommendation_repository=self.recommendation_repository,
            recommendation_log_repository=self.recommendation_log_repository,
        ).execute_cached(user_id=user_id)
        run_id = response.run_id or "current"
        return AgentToolResult(
            data={
                "recommendation": recommendation_response_to_dto(response).model_dump()
            },
            sources=[
                _source(
                    "recommendation_run" if response.run_id else "recommendation_cache",
                    run_id,
                    "Latest recommendation",
                    response.generated_at,
                )
            ],
        )

    def get_my_string_preferences(self, *, user_id: str) -> AgentToolResult:
        profile = self.profile_repository.get_by_user_id(user_id)
        if profile is None:
            raise NotFoundError("Profile not found")
        return AgentToolResult(
            data={
                "profile": {
                    "skill_level": profile.skill_level,
                    "playing_style": profile.playing_style,
                    "preferred_feel": profile.preferred_feel,
                    "durability_priority": profile.pref_durability,
                }
            },
            sources=[
                _source(
                    "player_profile",
                    "current-player-profile",
                    "Saved string preferences",
                    profile.updated_at,
                )
            ],
        )

    def preview_recommendation_what_if(
        self,
        *,
        user_id: str,
        raw_changes: object,
    ) -> AgentToolResult:
        try:
            changes = AgentWhatIfChangesDto.model_validate(raw_changes)
        except ValidationError as error:
            raise BadRequestError("Invalid What-if changes") from error
        profile = self.profile_repository.get_by_user_id(user_id)
        if profile is None:
            raise NotFoundError("Profile not found")
        values = {
            "skill_level": profile.skill_level,
            "playing_style": profile.playing_style,
            "preferred_tension": profile.preferred_tension,
            "frequency_per_week": profile.frequency_per_week,
            "preferred_feel": profile.preferred_feel,
            "preferred_gauge": profile.preferred_gauge,
            "recent_goal": profile.recent_goal,
            "pref_attack": profile.pref_attack,
            "pref_comfort": profile.pref_comfort,
            "pref_control": profile.pref_control,
            "pref_durability": profile.pref_durability,
            "pref_elasticity": profile.pref_elasticity,
            "pref_sound": profile.pref_sound,
            "pref_string_movement": profile.pref_string_movement,
            "pref_tension_retention": profile.pref_tension_retention,
            "pref_value_for_money": profile.pref_value_for_money,
        }
        change_values = changes.model_dump(
            exclude_none=True,
            exclude={"budget_rm", "racket_id"},
        )
        for friendly_name, preference_name in {
            "attack": "pref_attack",
            "comfort": "pref_comfort",
            "control": "pref_control",
            "durability": "pref_durability",
            "elasticity": "pref_elasticity",
            "sound": "pref_sound",
            "string_movement": "pref_string_movement",
            "tension_retention": "pref_tension_retention",
            "value_for_money": "pref_value_for_money",
        }.items():
            if friendly_name in change_values:
                change_values[preference_name] = change_values.pop(friendly_name)
        values.update(change_values)
        missing = [key for key, value in values.items() if value is None]
        if missing:
            raise BadRequestError("Profile is incomplete for What-if preview")
        complete_values = cast(dict[str, str | float | int], values)
        request = RecommendationRequestModel(
            user_id=user_id,
            skill_level=str(complete_values["skill_level"]),
            playing_style=str(complete_values["playing_style"]),
            preferred_tension=float(complete_values["preferred_tension"]),
            frequency_per_week=int(complete_values["frequency_per_week"]),
            preferred_feel=str(complete_values["preferred_feel"]),
            preferred_gauge=str(complete_values["preferred_gauge"]),
            recent_goal=str(complete_values["recent_goal"]),
            pref_attack=int(complete_values["pref_attack"]),
            pref_comfort=int(complete_values["pref_comfort"]),
            pref_control=int(complete_values["pref_control"]),
            pref_durability=int(complete_values["pref_durability"]),
            pref_elasticity=int(complete_values["pref_elasticity"]),
            pref_sound=int(complete_values["pref_sound"]),
            pref_string_movement=int(complete_values["pref_string_movement"]),
            pref_tension_retention=int(complete_values["pref_tension_retention"]),
            pref_value_for_money=int(complete_values["pref_value_for_money"]),
            top_n=10 if changes.budget_rm is not None else 3,
        )
        response = GenerateRecommendationUseCase(
            profile_repository=self.profile_repository,
            recommendation_repository=self.recommendation_repository,
            recommendation_log_repository=self.recommendation_log_repository,
        ).execute_preview(
            user_id=user_id,
            request=request,
            racket_id=changes.racket_id,
        )
        recommendation = recommendation_response_to_dto(response).model_dump()
        if changes.budget_rm is not None:
            within_budget = [
                result
                for result in recommendation["results"]
                if result["price_rm"] is not None
                and result["price_rm"] <= changes.budget_rm
            ][:3]
            for rank, result in enumerate(within_budget, start=1):
                result["rank"] = rank
            recommendation["results"] = within_budget
        return AgentToolResult(
            data={
                "simulation": True,
                "applied_changes": changes.model_dump(exclude_none=True),
                "recommendation": recommendation,
            },
            sources=[
                _source(
                    "recommendation_run",
                    response.run_id or "preview",
                    "Recommendation preview",
                    response.generated_at,
                )
            ],
        )

    def find_in_stock_alternatives(
        self,
        *,
        catalog_id: str,
        budget_rm: float | None,
    ) -> AgentToolResult:
        target = self.catalog_repository.get_by_id(catalog_id)
        if target is None or not target.is_active:
            raise NotFoundError("String not found")
        target_available = bool(
            target.inventory
            and target.available_stock > 0
            and target.inventory.availability_status in {"in_stock", "low_stock"}
        )
        alternatives: list[tuple[float, StringItem]] = []
        if not target_available:
            for candidate in self.recommendation_repository.list_active_candidates():
                item = candidate.item
                if item.id == target.id:
                    continue
                if budget_rm is not None and (
                    item.price_rm is None or item.price_rm > budget_rm
                ):
                    continue
                distance = sum(
                    abs(
                        target.aspect_score(feature_key)
                        - item.aspect_score(feature_key)
                    )
                    for feature_key in CORE_RECOMMENDATION_FEATURES
                )
                alternatives.append((distance, item))
        alternatives.sort(
            key=lambda pair: (
                pair[0],
                pair[1].price_rm if pair[1].price_rm is not None else float("inf"),
                pair[1].display_name,
            )
        )
        selected = [item for _, item in alternatives[:3]]
        return AgentToolResult(
            data={
                "requested_string": {
                    "catalog_id": target.id,
                    "display_name": target.display_name,
                    "available_stock": target.available_stock,
                    "availability_status": (
                        target.inventory.availability_status
                        if target.inventory
                        else "out_of_stock"
                    ),
                },
                "target_available": target_available,
                "budget_rm": budget_rm,
                "alternatives": [
                    {
                        "catalog_id": item.id,
                        "display_name": item.display_name,
                        "brand": item.brand,
                        "price_rm": item.price_rm,
                        "available_stock": item.available_stock,
                        "availability_status": (
                            item.inventory.availability_status
                            if item.inventory
                            else "out_of_stock"
                        ),
                        "matched_strengths": [
                            feature_key.replace("_", " ")
                            for feature_key in sorted(
                                CORE_RECOMMENDATION_FEATURES,
                                key=lambda key: abs(
                                    target.aspect_score(key) - item.aspect_score(key)
                                ),
                            )[:3]
                        ],
                    }
                    for item in selected
                ],
            },
            sources=[
                _source("catalog", target.id, target.display_name, target.updated_at),
                *[
                    _source("catalog", item.id, item.display_name, item.updated_at)
                    for item in selected
                ],
            ],
        )


def _required_string(arguments: dict[str, object], key: str) -> str:
    value = arguments.get(key)
    if not isinstance(value, str) or not value.strip():
        raise BadRequestError(f"{key} is required")
    return value.strip()


def _optional_string(arguments: dict[str, object], key: str) -> str | None:
    value = arguments.get(key)
    if value is None:
        return None
    if not isinstance(value, str) or not value.strip():
        raise BadRequestError(f"{key} must be a non-empty string")
    return value.strip()


def _optional_number(arguments: dict[str, object], key: str) -> float | None:
    value = arguments.get(key)
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int | float):
        raise BadRequestError(f"{key} must be a number")
    number = float(value)
    if not 0 <= number <= 1000:
        raise BadRequestError(f"{key} must be between 0 and 1000")
    return number


def _string_list(
    arguments: dict[str, object],
    key: str,
    minimum: int,
    maximum: int,
) -> list[str]:
    value = arguments.get(key, [])
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise BadRequestError(f"{key} must be a list of strings")
    normalized = [item.strip() for item in value if item.strip()]
    if not minimum <= len(normalized) <= maximum:
        raise BadRequestError(
            f"{key} must contain between {minimum} and {maximum} values"
        )
    return normalized


def _source(
    source_type: str,
    source_id: str,
    label: str,
    updated_at: object | None = None,
) -> dict[str, str | None]:
    return {
        "source_type": source_type,
        "source_id": source_id,
        "label": label,
        "version": _version(updated_at),
    }


def _version(value: object | None) -> str | None:
    if value is None:
        return None
    isoformat = getattr(value, "isoformat", None)
    return str(isoformat()) if callable(isoformat) else str(value)


def _without_keys(
    value: dict[str, object],
    *keys: str,
) -> dict[str, object]:
    return {key: item for key, item in value.items() if key not in keys}
