from __future__ import annotations

import json
from types import SimpleNamespace
from typing import Any
from typing import cast
from unittest.mock import patch
from urllib.request import Request as UrlRequest

import pytest
from fastapi.testclient import TestClient

from app.adapters.services.agent.admin_tools import ADMIN_AGENT_TOOL_SPECS
from app.adapters.services.agent.admin_tools import AdminAgentToolbox
from app.adapters.services.agent.deepseek import DeepSeekAgentClient
from app.domain.profile.entities import PlayerProfile
from app.domain.recommendation.entities import RecommendationResponseModel
from app.domain.recommendation.entities import RecommendationResultModel
from app.domain.recommendation.entities import RecommendationRunItemRecord
from app.domain.recommendation.entities import RecommendationRunRecord
from app.domain.recommendation.scoring import ALGORITHM_VERSION
from app.dto.agent import AgentQueryDto
from app.dto.agent import AgentToolResult
from app.entrypoints.api.routes.agent_routes import get_deepseek_agent_client
from app.main import app
from app.ports.repositories.booking_repository import BookingRepository
from app.ports.repositories.catalog_repository import CatalogRepository
from app.ports.repositories.recommendation_run_repository import (
    RecommendationRunRepository,
)
from app.ports.repositories.profile_repository import ProfileRepository
from app.ports.repositories.recommendation_repository import RecommendationRepository
from app.ports.repositories.store_repository import StoreRepository
from app.shared.errors import NotFoundError
from app.shared.errors import ServiceUnavailableError
from app.shared.pagination import Page
from app.use_cases.agent.query_agent import ACTIVE_AGENT_ACTIONS
from app.use_cases.agent.query_agent import QueryAgentUseCase
from app.use_cases.agent.tools import AGENT_TOOL_SPECS
from app.use_cases.agent.tools import AgentToolbox
from app.use_cases.recommendation.generate_recommendation import (
    GenerateRecommendationUseCase,
)


class FakeModelClient:
    model = "deepseek-v4-flash"

    def __init__(self, responses: list[dict[str, Any]]) -> None:
        self.responses = responses
        self.calls: list[dict[str, Any]] = []

    def complete(self, **kwargs: Any) -> dict[str, Any]:
        self.calls.append({**kwargs, "messages": list(kwargs["messages"])})
        return self.responses.pop(0)


class FakeToolbox:
    def execute(
        self,
        *,
        name: str,
        arguments: dict[str, object],
        user_id: str,
    ) -> AgentToolResult:
        assert name == "get_string_details"
        assert arguments == {"catalog_id": "yonex-bg80"}
        assert user_id == "user-1"
        return AgentToolResult(
            data={"string": {"id": "yonex-bg80", "display_name": "Yonex BG80"}},
            sources=[
                {
                    "source_type": "catalog",
                    "source_id": "yonex-bg80",
                    "label": "Yonex BG80",
                    "version": "2026-08-13",
                }
            ],
        )

    def get_recommendation_run_context(self, **_: Any) -> AgentToolResult:
        raise AssertionError("not expected")

    def get_string_details(self, _: str) -> AgentToolResult:
        raise AssertionError("not expected")

    def get_my_bookings(self, **_: Any) -> AgentToolResult:
        raise AssertionError("not expected")


def _completion(message: dict[str, object], finish_reason: str) -> dict[str, Any]:
    return {
        "id": "response-1",
        "model": "deepseek-v4-flash",
        "choices": [{"finish_reason": finish_reason, "message": message}],
    }


def _answer_content(*, suggested_actions: list[dict[str, object]] | None = None) -> str:
    return json.dumps(
        {
            "answer": "The store information is available from the live settings.",
            "summary": "Live store information",
            "evidence": ["The current store name is StringSence."],
            "evidence_status": "complete",
            "suggested_questions": ["What are the business hours?"],
            "suggested_actions": suggested_actions or [],
            "handoff": None,
        }
    )


def _login_admin(client: TestClient) -> str:
    response = client.post(
        "/api/auth/login",
        json={"phone_number": "+60190000000", "password": "admin1234"},
    )
    assert response.status_code == 200
    return cast(str, response.json()["access_token"])


def test_fyp_agent_scope_exposes_only_active_tools_and_string_action() -> None:
    assert {spec["name"] for spec in AGENT_TOOL_SPECS} == {
        "get_string_details",
        "compare_strings",
        "get_store_information",
        "preview_recommendation_what_if",
        "find_in_stock_alternatives",
    }
    assert {spec["name"] for spec in ADMIN_AGENT_TOOL_SPECS} == {
        "get_admin_operations_summary",
        "find_admin_bookings",
        "find_admin_inventory",
    }
    assert ACTIVE_AGENT_ACTIONS == {"open_string"}
    what_if = next(
        spec
        for spec in AGENT_TOOL_SPECS
        if spec["name"] == "preview_recommendation_what_if"
    )
    parameters = cast(dict[str, Any], what_if["parameters"])
    assert parameters["required"] == ["changes"]
    assert set(cast(dict[str, Any], parameters["properties"])) == {"changes"}
    changes = cast(dict[str, Any], parameters["properties"]["changes"])
    assert changes["type"] == "object"
    assert set(cast(dict[str, Any], changes["properties"])) >= {
        "playing_style",
        "preferred_feel",
        "durability",
        "budget_rm",
    }


def test_admin_inventory_tool_returns_every_matching_string() -> None:
    class Catalogs:
        def list_inventory(self, **kwargs: object) -> Page[SimpleNamespace]:
            assert kwargs["limit"] is None
            items = [
                SimpleNamespace(
                    id=f"string-{index}",
                    display_name=f"String {index}",
                    current_stock=8,
                    reserved_stock=0,
                    available_stock=8,
                    reorder_level=2,
                    inventory=SimpleNamespace(availability_status="in_stock"),
                    selling_price=35.0,
                    updated_at=None,
                )
                for index in range(12)
            ]
            return Page(items=items, total=len(items), limit=None, offset=0)

    toolbox = cast(
        AdminAgentToolbox,
        SimpleNamespace(catalog_repository=Catalogs()),
    )

    result = AdminAgentToolbox.find_admin_inventory(
        toolbox,
        availability=None,
        search=None,
    )

    assert result.data["total"] == 12
    assert len(cast(list[object], result.data["inventory"])) == 12


def test_admin_booking_tool_discloses_truncated_result_count() -> None:
    class Bookings:
        def list_admin(self, **kwargs: object) -> Page[SimpleNamespace]:
            assert kwargs["limit"] == 10
            items = [
                SimpleNamespace(
                    id=f"booking-{index}",
                    order_code=f"ORD-{index}",
                    status="awaiting_dropoff",
                    string_name="Yonex BG80",
                    customer_username="Player",
                    customer_phone_number="+60123456789",
                    racket_brand="Yonex",
                    racket_model="Astrox",
                    requested_tension=26,
                    drop_off_datetime=None,
                    updated_at=None,
                )
                for index in range(10)
            ]
            return Page(items=items, total=12, limit=10, offset=0)

    toolbox = cast(
        AdminAgentToolbox,
        SimpleNamespace(booking_repository=Bookings()),
    )

    result = AdminAgentToolbox.find_admin_bookings(
        toolbox,
        status=None,
        search=None,
    )

    assert result.data["returned_count"] == 10
    assert result.data["total"] == 12
    assert result.data["is_truncated"] is True


def test_agent_executes_bounded_tool_and_returns_server_sources() -> None:
    client = FakeModelClient(
        [
            _completion(
                {
                    "role": "assistant",
                    "content": None,
                    "tool_calls": [
                        {
                            "id": "call-1",
                            "type": "function",
                            "function": {
                                "name": "get_string_details",
                                "arguments": json.dumps({"catalog_id": "yonex-bg80"}),
                            },
                        }
                    ],
                },
                "tool_calls",
            ),
            _completion(
                {"role": "assistant", "content": _answer_content()},
                "stop",
            ),
        ]
    )
    payload = AgentQueryDto.model_validate(
        {
            "message": "Tell me about Yonex BG80.",
            "context": {"surface": "chatbot"},
        }
    )

    response = QueryAgentUseCase(
        toolbox=cast(AgentToolbox, FakeToolbox()),
        model_client=cast(DeepSeekAgentClient, client),
    ).execute(payload=payload, user_id="user-1")

    assert response.model == "deepseek-v4-flash"
    assert response.sources[0].source_type == "catalog"
    assert client.calls[0]["tool_choice"] == "auto"
    assert client.calls[1]["tool_choice"] == "auto"
    assert client.calls[0]["user_id"].startswith("stringsense-")
    assert "user-1" not in client.calls[0]["user_id"]
    assert "Never use Markdown" in client.calls[0]["messages"][0]["content"]
    assert "Example JSON output" in client.calls[0]["messages"][0]["content"]
    surface_instruction = client.calls[0]["messages"][1]
    assert surface_instruction["role"] == "system"
    assert (
        "Route the latest player request in this priority order"
        in surface_instruction["content"]
    )
    assert "call compare_strings" in surface_instruction["content"]
    assert "call get_store_information" in surface_instruction["content"]
    assert "exactly this shape" in surface_instruction["content"]
    assert "Always ask all four questions" not in surface_instruction["content"]
    assert client.calls[0]["messages"][-1] == {
        "role": "user",
        "content": "Tell me about Yonex BG80.",
    }


@pytest.mark.parametrize(
    ("user_message", "tool_name", "arguments"),
    [
        ("What time does the shop open?", "get_store_information", {}),
        (
            "Compare Yonex BG80 and Yonex BG65.",
            "compare_strings",
            {"catalog_ids": ["Yonex BG80", "Yonex BG65"]},
        ),
        (
            "Tell me about Yonex BG80.",
            "get_string_details",
            {"catalog_id": "yonex-bg80"},
        ),
    ],
)
def test_chatbot_priority_routes_keep_non_selection_requests_out_of_guided_flow(
    user_message: str,
    tool_name: str,
    arguments: dict[str, object],
) -> None:
    class RoutingToolbox:
        def __init__(self) -> None:
            self.calls: list[tuple[str, dict[str, object]]] = []

        def execute(
            self,
            *,
            name: str,
            arguments: dict[str, object],
            user_id: str,
        ) -> AgentToolResult:
            assert user_id == "user-1"
            self.calls.append((name, arguments))
            return AgentToolResult(data={"verified": True}, sources=[])

    client = FakeModelClient(
        [
            _completion(
                {
                    "role": "assistant",
                    "content": None,
                    "tool_calls": [
                        {
                            "id": "call-route",
                            "type": "function",
                            "function": {
                                "name": tool_name,
                                "arguments": json.dumps(arguments),
                            },
                        }
                    ],
                },
                "tool_calls",
            ),
            _completion({"role": "assistant", "content": _answer_content()}, "stop"),
        ]
    )
    toolbox = RoutingToolbox()

    QueryAgentUseCase(
        toolbox=cast(AgentToolbox, toolbox),
        model_client=client,
    ).execute(
        payload=AgentQueryDto.model_validate(
            {"message": user_message, "context": {"surface": "chatbot"}}
        ),
        user_id="user-1",
    )

    assert toolbox.calls == [(tool_name, arguments)]
    assert not any(
        message.get("role") == "system"
        and "Conversation-derived guided-selection state" in message.get("content", "")
        for message in client.calls[0]["messages"]
    )
    assert client.calls[0]["messages"][-1] == {
        "role": "user",
        "content": user_message,
    }


def test_guided_selection_uses_the_next_unanswered_question() -> None:
    client = FakeModelClient(
        [_completion({"role": "assistant", "content": _answer_content()}, "stop")]
    )
    payload = AgentQueryDto.model_validate(
        {
            "message": "control",
            "context": {"surface": "chatbot"},
            "conversation_history": [
                {"role": "user", "content": "Help me choose a string."},
                {
                    "role": "assistant",
                    "content": "What is your playing style: attacking, balanced, or control?",
                },
            ],
        }
    )

    response = QueryAgentUseCase(
        toolbox=cast(AgentToolbox, FakeToolbox()),
        model_client=client,
    ).execute(payload=payload, user_id="user-1")

    assert client.calls == []
    assert "what feel do you prefer" in response.answer.casefold()
    assert "durability" not in response.answer.casefold()
    assert "budget" not in response.answer.casefold()
    assert response.evidence_status == "insufficient_evidence"


def test_recommendation_explanation_requests_short_non_technical_copy() -> None:
    class RecommendationToolbox(FakeToolbox):
        def get_recommendation_run_context(self, **_: Any) -> AgentToolResult:
            return AgentToolResult(
                data={"run_id": "run-1", "catalog_id": "kumpoo-js-63"},
                sources=[
                    {
                        "source_type": "recommendation_run",
                        "source_id": "run-1",
                        "label": "Recommendation run run-1",
                        "version": None,
                    }
                ],
            )

        def get_string_details(self, _: str) -> AgentToolResult:
            return AgentToolResult(
                data={
                    "string": {
                        "id": "kumpoo-js-63",
                        "inventory": {
                            "available_stock": 8,
                            "availability_status": "in_stock",
                        },
                    }
                },
                sources=[
                    {
                        "source_type": "catalog",
                        "source_id": "kumpoo-js-63",
                        "label": "Kumpoo JS-63",
                        "version": None,
                    }
                ],
            )

    client = FakeModelClient(
        [_completion({"role": "assistant", "content": _answer_content()}, "stop")]
    )
    payload = AgentQueryDto.model_validate(
        {
            "message": "Why does this suit me?",
            "context": {
                "surface": "recommendation_explanation",
                "run_id": "run-1",
                "catalog_id": "kumpoo-js-63",
            },
        }
    )

    QueryAgentUseCase(
        toolbox=cast(AgentToolbox, RecommendationToolbox()),
        model_client=client,
    ).execute(payload=payload, user_id="user-1")

    messages = client.calls[0]["messages"]
    instruction_message = next(
        message
        for message in messages
        if message.get("content", "").startswith("For this recommendation explanation")
    )
    assert instruction_message["role"] == "system"
    instruction = instruction_message["content"]
    assert "answer under 70 words" in instruction
    assert "Do not repeat the same fact" in instruction
    assert "Do not mention algorithms" in instruction
    assert "personal experience" in instruction
    assert "similar-player evidence" in instruction
    assert "fixed sentence template" in instruction
    assert "find_in_stock_alternatives" in instruction


def test_catalog_context_requests_grounded_string_introduction() -> None:
    class CatalogContextToolbox(FakeToolbox):
        def get_string_details(self, catalog_id: str) -> AgentToolResult:
            assert catalog_id == "yonex-bg66-ultimax"
            return AgentToolResult(
                data={
                    "string": {
                        "id": catalog_id,
                        "display_name": "Yonex BG66 ULTIMAX",
                        "short_description": "Thin-gauge repulsion string.",
                    }
                },
                sources=[
                    {
                        "source_type": "catalog",
                        "source_id": catalog_id,
                        "label": "Yonex BG66 ULTIMAX",
                        "version": None,
                    }
                ],
            )

    client = FakeModelClient(
        [_completion({"role": "assistant", "content": _answer_content()}, "stop")]
    )
    payload = AgentQueryDto.model_validate(
        {
            "message": "Introduce this string.",
            "context": {
                "surface": "chatbot",
                "catalog_id": "yonex-bg66-ultimax",
            },
        }
    )

    response = QueryAgentUseCase(
        toolbox=cast(AgentToolbox, CatalogContextToolbox()),
        model_client=client,
    ).execute(payload=payload, user_id="user-1")

    assert response.sources[0].source_id == "yonex-bg66-ultimax"
    instruction_message = next(
        message
        for message in client.calls[0]["messages"]
        if message.get("content", "").startswith("This player surface")
    )
    assert instruction_message["role"] == "system"
    instruction = instruction_message["content"]
    assert "exact catalog-string explanations" in instruction
    assert "one practical consideration" in instruction
    assert "do not ask guided questions" in instruction
    assert "This is not a personalized recommendation" in instruction
    assert "yonex-bg66-ultimax" in client.calls[0]["messages"][-2]["content"]


def test_agent_drops_action_with_unverified_resource_id() -> None:
    client = FakeModelClient(
        [
            _completion(
                {
                    "role": "assistant",
                    "content": None,
                    "tool_calls": [
                        {
                            "id": "call-1",
                            "type": "function",
                            "function": {
                                "name": "get_string_details",
                                "arguments": json.dumps({"catalog_id": "yonex-bg80"}),
                            },
                        }
                    ],
                },
                "tool_calls",
            ),
            _completion(
                {
                    "role": "assistant",
                    "content": _answer_content(
                        suggested_actions=[
                            {
                                "action": "open_booking",
                                "label": "Open booking",
                                "parameters": {"booking_id": "invented-booking"},
                            }
                        ]
                    ),
                },
                "stop",
            ),
        ]
    )

    response = QueryAgentUseCase(
        toolbox=cast(AgentToolbox, FakeToolbox()),
        model_client=client,
    ).execute(
        payload=AgentQueryDto.model_validate(
            {"message": "Open my booking", "context": {"surface": "chatbot"}}
        ),
        user_id="user-1",
    )

    assert response.suggested_actions == []


def test_agent_rejects_a_still_deferred_tool_call() -> None:
    client = FakeModelClient(
        [
            _completion(
                {
                    "role": "assistant",
                    "content": None,
                    "tool_calls": [
                        {
                            "id": "call-deferred",
                            "type": "function",
                            "function": {
                                "name": "get_review_evidence",
                                "arguments": json.dumps({"catalog_id": "yonex-bg80"}),
                            },
                        }
                    ],
                },
                "tool_calls",
            ),
            _completion(
                {"role": "assistant", "content": _answer_content()},
                "stop",
            ),
        ]
    )

    QueryAgentUseCase(
        toolbox=cast(AgentToolbox, FakeToolbox()),
        model_client=client,
    ).execute(
        payload=AgentQueryDto.model_validate(
            {
                "message": "Summarize the BG80 reviews.",
                "context": {"surface": "chatbot"},
            }
        ),
        user_id="user-1",
    )

    tool_message = client.calls[1]["messages"][-1]
    assert json.loads(tool_message["content"]) == {"error": "Agent tool is not enabled"}


def test_compare_strings_combines_distinct_backend_items() -> None:
    class Catalogs:
        def list_active_catalog(self):
            return [
                SimpleNamespace(id="yonex-bg80", display_name="Yonex BG80"),
                SimpleNamespace(id="yonex-bg65", display_name="Yonex BG65"),
            ]

    toolbox = AgentToolbox(
        catalog_repository=cast(CatalogRepository, Catalogs()),
        recommendation_run_repository=cast(RecommendationRunRepository, object()),
        store_repository=cast(StoreRepository, object()),
        booking_repository=cast(BookingRepository, object()),
        profile_repository=cast(ProfileRepository, object()),
        recommendation_repository=cast(RecommendationRepository, object()),
    )
    details = [
        AgentToolResult(
            data={"string": {"id": "yonex-bg80", "display_name": "Yonex BG80"}},
            sources=[
                {
                    "source_type": "catalog",
                    "source_id": "yonex-bg80",
                    "label": "Yonex BG80",
                    "version": None,
                }
            ],
        ),
        AgentToolResult(
            data={"string": {"id": "yonex-bg65", "display_name": "Yonex BG65"}},
            sources=[
                {
                    "source_type": "catalog",
                    "source_id": "yonex-bg65",
                    "label": "Yonex BG65",
                    "version": None,
                }
            ],
        ),
    ]

    resolved_ids: list[str] = []

    def get_details(catalog_id: str) -> AgentToolResult:
        resolved_ids.append(catalog_id)
        return details.pop(0)

    with patch.object(toolbox, "get_string_details", side_effect=get_details):
        result = toolbox.execute(
            name="compare_strings",
            arguments={"catalog_ids": ["Yonex BG80", "Yonex BG65"]},
            user_id="user-1",
        )

    assert resolved_ids == ["yonex-bg80", "yonex-bg65"]
    assert [item["id"] for item in result.data["strings"]] == [
        "yonex-bg80",
        "yonex-bg65",
    ]
    assert [source["source_id"] for source in result.sources] == [
        "yonex-bg80",
        "yonex-bg65",
    ]


def test_string_details_resolves_exact_display_name() -> None:
    item = SimpleNamespace(
        id="yonex-bg80",
        brand="Yonex",
        display_name="Yonex BG80",
        model_name="BG80",
        series_label="High Repulsion",
        is_hybrid=False,
        gauge_main_mm=0.68,
        gauge_cross_mm=None,
        gauge_label="0.68 mm",
        category="repulsion",
        main_trait="Repulsion",
        tension_min_lbs=20,
        tension_max_lbs=35,
        material_summary_en="Nylon and Vectran.",
        color_options_en=["White"],
        short_description="A firm offensive string.",
        full_description="A firm offensive string with crisp response.",
        aspect_scores={},
        price_rm=48.0,
        available_stock=8,
        inventory=SimpleNamespace(
            available_stock=8,
            availability_status="in_stock",
            pricing_mode="fixed",
        ),
        official_performance=None,
        is_active=True,
        updated_at=None,
    )

    class Catalogs:
        def get_by_id(self, catalog_id: str):
            assert catalog_id == "Yonex BG80"
            return None

        def list_active_catalog(self):
            return [item]

    toolbox = AgentToolbox(
        catalog_repository=cast(CatalogRepository, Catalogs()),
        recommendation_run_repository=cast(RecommendationRunRepository, object()),
        store_repository=cast(StoreRepository, object()),
        booking_repository=cast(BookingRepository, object()),
        profile_repository=cast(ProfileRepository, object()),
        recommendation_repository=cast(RecommendationRepository, object()),
    )

    result = toolbox.get_string_details("Yonex BG80")

    assert result.data["string"]["id"] == "yonex-bg80"
    assert result.sources[0]["source_id"] == "yonex-bg80"


def test_recommendation_run_tool_hides_another_users_run() -> None:
    run = RecommendationRunRecord(
        id="run-1",
        user_id="user-2",
        phone_number=None,
        username=None,
        algorithm_version="v11",
        request_snapshot={},
        profile_snapshot={},
        generated_at=None,
        items=[
            RecommendationRunItemRecord(
                id="item-1",
                catalog_id="yonex-bg80",
                rank_position=1,
                final_score=0.9,
                preference_match_score=0.9,
                rule_fit_score=0.8,
                value_for_money_score=0.7,
                nlp_review_score=0.8,
                score_breakdown={},
                rationale={},
            )
        ],
    )

    class RunRepository:
        def get_run(self, run_id: str) -> RecommendationRunRecord | None:
            assert run_id == "run-1"
            return run

    toolbox = AgentToolbox(
        catalog_repository=cast(CatalogRepository, object()),
        recommendation_run_repository=cast(
            RecommendationRunRepository,
            RunRepository(),
        ),
        store_repository=cast(StoreRepository, object()),
        booking_repository=cast(BookingRepository, object()),
        profile_repository=cast(ProfileRepository, object()),
        recommendation_repository=cast(RecommendationRepository, object()),
    )

    with pytest.raises(NotFoundError, match="Recommendation run not found"):
        toolbox.get_recommendation_run_context(
            user_id="user-1",
            run_id="run-1",
            catalog_id=None,
        )


def test_what_if_tool_maps_changes_without_mutating_saved_profile() -> None:
    profile = PlayerProfile(
        user_id="user-1",
        skill_level="intermediate",
        playing_style="balanced",
        preferred_tension=25,
        frequency_per_week=3,
        preferred_feel="medium",
        preferred_gauge="no_preference",
        recent_goal="balanced",
        pref_attack=5,
        pref_comfort=5,
        pref_control=5,
        pref_durability=5,
        pref_elasticity=5,
        pref_sound=5,
        pref_string_movement=5,
        pref_tension_retention=5,
        pref_value_for_money=5,
        created_at=None,
        updated_at=None,
    )

    class Profiles:
        def get_by_user_id(self, user_id: str) -> PlayerProfile:
            assert user_id == "user-1"
            return profile

    toolbox = AgentToolbox(
        catalog_repository=cast(CatalogRepository, object()),
        recommendation_run_repository=cast(RecommendationRunRepository, object()),
        store_repository=cast(StoreRepository, object()),
        booking_repository=cast(BookingRepository, object()),
        profile_repository=cast(ProfileRepository, Profiles()),
        recommendation_repository=cast(RecommendationRepository, object()),
    )
    preview_response = RecommendationResponseModel(
        algorithm_version=ALGORITHM_VERSION,
        results=[
            RecommendationResultModel(
                rank=1,
                string_name="Within budget",
                brand="Test",
                score=0.9,
                price_rm=35,
                aspect_scores={},
                reasons=[],
                catalog_id="within-budget",
            ),
            RecommendationResultModel(
                rank=2,
                string_name="Over budget",
                brand="Test",
                score=0.8,
                price_rm=55,
                aspect_scores={},
                reasons=[],
                catalog_id="over-budget",
            ),
        ],
        run_id="run-preview",
    )

    with patch.object(
        GenerateRecommendationUseCase,
        "execute_preview",
        return_value=preview_response,
    ) as execute_preview:
        result = toolbox.execute(
            name="preview_recommendation_what_if",
            arguments={
                "changes": {
                    "attack": 9,
                    "preferred_tension": 28,
                    "playing_style": "control",
                    "budget_rm": 40,
                }
            },
            user_id="user-1",
        )

    request = execute_preview.call_args.kwargs["request"]
    assert request.pref_attack == 9
    assert request.preferred_tension == 28
    assert request.playing_style == "control_defensive"
    assert request.pref_comfort == 5
    assert request.top_n == 10
    assert profile.pref_attack == 5
    assert result.data["simulation"] is True
    assert result.data["applied_changes"]["playing_style"] == "control_defensive"
    assert result.data["recommendation"]["run_id"] == "run-preview"
    assert [
        item["catalog_id"] for item in result.data["recommendation"]["results"]
    ] == ["within-budget"]


def test_out_of_stock_tool_returns_only_similar_in_budget_candidates() -> None:
    target_scores = {
        feature: 0.8
        for feature in (
            "repulsion",
            "control",
            "durability",
            "comfort",
            "sound",
            "elasticity",
            "tension_retention",
            "string_movement",
            "value_for_money",
        )
    }

    def item(
        catalog_id: str,
        *,
        price: float,
        stock: int,
        score: float,
        availability_status: str | None = None,
    ) -> SimpleNamespace:
        scores = {feature: score for feature in target_scores}
        return SimpleNamespace(
            id=catalog_id,
            brand="Test",
            display_name=catalog_id,
            price_rm=price,
            available_stock=stock,
            inventory=SimpleNamespace(
                availability_status=availability_status
                or ("in_stock" if stock else "out_of_stock")
            ),
            aspect_score=lambda feature, default=0.5: scores.get(feature, default),
            is_active=True,
            updated_at=None,
        )

    target = item("target", price=40, stock=0, score=0.8)
    close = item("close", price=45, stock=4, score=0.78)
    far = item("far", price=30, stock=6, score=0.2)
    expensive = item("expensive", price=80, stock=8, score=0.8)
    stale = item(
        "stale",
        price=35,
        stock=7,
        score=0.79,
        availability_status="out_of_stock",
    )

    class Catalogs:
        def get_by_id(self, catalog_id: str):
            assert catalog_id == "target"
            return target

    class Recommendations:
        def list_active_candidates(self):
            return [
                SimpleNamespace(item=far),
                SimpleNamespace(item=expensive),
                SimpleNamespace(item=close),
                SimpleNamespace(item=stale),
            ]

    toolbox = AgentToolbox(
        catalog_repository=cast(CatalogRepository, Catalogs()),
        recommendation_run_repository=cast(RecommendationRunRepository, object()),
        store_repository=cast(StoreRepository, object()),
        booking_repository=cast(BookingRepository, object()),
        profile_repository=cast(ProfileRepository, object()),
        recommendation_repository=cast(
            RecommendationRepository,
            Recommendations(),
        ),
    )

    result = toolbox.execute(
        name="find_in_stock_alternatives",
        arguments={"catalog_id": "target", "budget_rm": 50},
        user_id="user-1",
    )

    assert result.data["target_available"] is False
    assert [item["catalog_id"] for item in result.data["alternatives"]] == [
        "close",
        "far",
    ]
    assert all(item["available_stock"] > 0 for item in result.data["alternatives"])


def test_out_of_stock_explanation_fetches_verified_alternatives_before_offering_one() -> (
    None
):
    class OutOfStockToolbox(FakeToolbox):
        def __init__(self) -> None:
            self.calls: list[tuple[str, dict[str, object]]] = []

        def get_recommendation_run_context(self, **_: Any) -> AgentToolResult:
            return AgentToolResult(
                data={"run_id": "run-1", "catalog_id": "target"},
                sources=[
                    {
                        "source_type": "recommendation_run",
                        "source_id": "run-1",
                        "label": "Recommendation run",
                        "version": None,
                    }
                ],
            )

        def get_string_details(self, catalog_id: str) -> AgentToolResult:
            assert catalog_id == "target"
            return AgentToolResult(
                data={
                    "string": {
                        "id": "target",
                        "inventory": {
                            "available_stock": 0,
                            "availability_status": "out_of_stock",
                        },
                    }
                },
                sources=[
                    {
                        "source_type": "catalog",
                        "source_id": "target",
                        "label": "Target string",
                        "version": None,
                    }
                ],
            )

        def execute(
            self,
            *,
            name: str,
            arguments: dict[str, object],
            user_id: str,
        ) -> AgentToolResult:
            assert user_id == "user-1"
            self.calls.append((name, arguments))
            assert name == "find_in_stock_alternatives"
            return AgentToolResult(
                data={"alternatives": [{"catalog_id": "alternative"}]},
                sources=[
                    {
                        "source_type": "catalog",
                        "source_id": "alternative",
                        "label": "Alternative string",
                        "version": None,
                    }
                ],
            )

    client = FakeModelClient(
        [
            _completion(
                {
                    "role": "assistant",
                    "content": None,
                    "tool_calls": [
                        {
                            "id": "call-alternatives",
                            "type": "function",
                            "function": {
                                "name": "find_in_stock_alternatives",
                                "arguments": json.dumps(
                                    {"catalog_id": "target", "budget_rm": 50}
                                ),
                            },
                        }
                    ],
                },
                "tool_calls",
            ),
            _completion(
                {
                    "role": "assistant",
                    "content": _answer_content(
                        suggested_actions=[
                            {
                                "action": "open_string",
                                "label": "Open alternative",
                                "parameters": {"catalog_id": "alternative"},
                            }
                        ]
                    ),
                },
                "stop",
            ),
        ]
    )
    toolbox = OutOfStockToolbox()

    response = QueryAgentUseCase(
        toolbox=cast(AgentToolbox, toolbox),
        model_client=client,
    ).execute(
        payload=AgentQueryDto.model_validate(
            {
                "message": "This recommendation is out of stock. What else can I buy?",
                "context": {
                    "surface": "recommendation_explanation",
                    "run_id": "run-1",
                    "catalog_id": "target",
                },
            }
        ),
        user_id="user-1",
    )

    assert toolbox.calls == [
        (
            "find_in_stock_alternatives",
            {"catalog_id": "target", "budget_rm": 50},
        )
    ]
    assert response.suggested_actions[0].parameters == {"catalog_id": "alternative"}
    assert {source.source_id for source in response.sources} >= {
        "target",
        "alternative",
    }


def test_latest_recommendation_tool_returns_backend_run_source() -> None:
    toolbox = AgentToolbox(
        catalog_repository=cast(CatalogRepository, object()),
        recommendation_run_repository=cast(RecommendationRunRepository, object()),
        store_repository=cast(StoreRepository, object()),
        booking_repository=cast(BookingRepository, object()),
        profile_repository=cast(ProfileRepository, object()),
        recommendation_repository=cast(RecommendationRepository, object()),
    )
    cached_response = RecommendationResponseModel(
        algorithm_version=ALGORITHM_VERSION,
        results=[],
        run_id="run-latest",
    )

    with patch.object(
        GenerateRecommendationUseCase,
        "execute_cached",
        return_value=cached_response,
    ):
        result = toolbox.execute(
            name="get_my_recommendations",
            arguments={},
            user_id="user-1",
        )

    assert result.data["recommendation"]["run_id"] == "run-latest"
    assert result.sources[0]["source_id"] == "run-latest"


def test_deepseek_client_uses_official_model_and_chat_completion_endpoint() -> None:
    captured: dict[str, object] = {}

    class Response:
        def __enter__(self) -> "Response":
            return self

        def __exit__(self, *_: object) -> None:
            return None

        def read(self) -> bytes:
            return json.dumps(_completion({"content": "{}"}, "stop")).encode()

    def fake_urlopen(request: object, timeout: float) -> Response:
        captured["request"] = request
        captured["timeout"] = timeout
        return Response()

    client = DeepSeekAgentClient(
        api_key="test-key",
        model="deepseek-v4-flash",
        base_url="https://api.deepseek.com",
        timeout_seconds=12,
    )
    with patch(
        "app.adapters.services.agent.deepseek.urlopen",
        fake_urlopen,
    ):
        client.complete(
            messages=[{"role": "user", "content": "hello"}],
            tools=[],
            tool_choice="none",
            user_id="stringsense-test",
        )

    request = captured["request"]
    assert isinstance(request, UrlRequest)
    assert isinstance(request.data, bytes)
    payload = json.loads(request.data.decode())
    assert request.full_url == "https://api.deepseek.com/chat/completions"
    assert request.get_header("Authorization") == "Bearer test-key"
    assert payload["model"] == "deepseek-v4-flash"
    assert payload["thinking"] == {"type": "disabled"}
    assert payload["response_format"] == {"type": "json_object"}
    assert captured["timeout"] == 12


def test_deepseek_client_retries_empty_json_content_once() -> None:
    payloads: list[dict[str, object]] = []
    responses = iter(
        [
            _completion({"role": "assistant", "content": " " * 20}, "stop"),
            _completion({"role": "assistant", "content": "{}"}, "stop"),
        ]
    )

    class Response:
        def __init__(self, body: dict[str, Any]) -> None:
            self.body = body

        def __enter__(self) -> "Response":
            return self

        def __exit__(self, *_: object) -> None:
            return None

        def read(self) -> bytes:
            return json.dumps(self.body).encode()

    def fake_urlopen(request: object, timeout: float) -> Response:
        assert isinstance(request, UrlRequest)
        assert isinstance(request.data, bytes)
        payloads.append(json.loads(request.data.decode()))
        return Response(next(responses))

    client = DeepSeekAgentClient(
        api_key="test-key",
        model="deepseek-v4-flash",
        base_url="https://api.deepseek.com",
        timeout_seconds=12,
    )
    with patch("app.adapters.services.agent.deepseek.urlopen", fake_urlopen):
        result = client.complete(
            messages=[{"role": "user", "content": "hello"}],
            tools=[],
            tool_choice="none",
            user_id="stringsense-test",
        )

    assert result["choices"][0]["message"]["content"] == "{}"
    assert len(payloads) == 2
    retry_messages = cast(list[dict[str, object]], payloads[1]["messages"])
    assert retry_messages[-2] == {
        "role": "system",
        "content": (
            "Return one non-empty JSON object matching the requested schema. Use this "
            "only as a format example: "
            '{"answer":"Plain response.","summary":"Short summary.",'
            '"evidence":[],"evidence_status":"insufficient_evidence",'
            '"suggested_questions":[],"suggested_actions":[],"handoff":null}'
        ),
    }
    assert retry_messages[-1] == {"role": "user", "content": "hello"}


def test_agent_endpoint_requires_auth_and_reports_unconfigured_provider() -> None:
    client = TestClient(app)
    unauthenticated = client.post(
        "/api/agent/query",
        json={"message": "hello", "context": {"surface": "chatbot"}},
    )
    assert unauthenticated.status_code == 401

    register = client.post(
        "/api/auth/register",
        json={
            "username": "agent-user",
            "phone_number": "+60128887777",
            "password": "secret123",
        },
    )
    token = register.json()["access_token"]

    def unavailable_provider() -> DeepSeekAgentClient:
        raise ServiceUnavailableError("Agent is not configured")

    app.dependency_overrides[get_deepseek_agent_client] = unavailable_provider
    try:
        unavailable = client.post(
            "/api/agent/query",
            headers={"Authorization": f"Bearer {token}"},
            json={"message": "hello", "context": {"surface": "chatbot"}},
        )
    finally:
        app.dependency_overrides.pop(get_deepseek_agent_client, None)
    assert unavailable.status_code == 503
    assert unavailable.json()["error"]["message"] == "Agent is not configured"


def test_agent_retries_an_invalid_final_answer_before_failing() -> None:
    fake_client = FakeModelClient(
        [
            _completion(
                {"role": "assistant", "content": "The answer is 3."},
                "stop",
            ),
            _completion(
                {"role": "assistant", "content": _answer_content()},
                "stop",
            ),
        ]
    )

    response = QueryAgentUseCase(
        toolbox=cast(AgentToolbox, FakeToolbox()),
        model_client=fake_client,
    ).execute(
        payload=AgentQueryDto.model_validate(
            {
                "message": "How many bookings are there?",
                "context": {"surface": "admin_assistant"},
            }
        ),
        user_id="admin-1",
    )

    assert (
        response.answer == "The store information is available from the live settings."
    )
    assert len(fake_client.calls) == 2
    assert fake_client.calls[1]["tools"] == []
    assert fake_client.calls[1]["tool_choice"] == "none"
    assert fake_client.calls[1]["messages"][-2]["role"] == "system"
    assert fake_client.calls[1]["messages"][-1] == {
        "role": "user",
        "content": "How many bookings are there?",
    }
    assert (
        "Return exactly one JSON object"
        in fake_client.calls[1]["messages"][-2]["content"]
    )


def test_agent_endpoint_accepts_validated_fake_model_response() -> None:
    fake_client = FakeModelClient(
        [_completion({"role": "assistant", "content": _answer_content()}, "stop")]
    )
    app.dependency_overrides[get_deepseek_agent_client] = lambda: cast(
        DeepSeekAgentClient,
        fake_client,
    )
    try:
        client = TestClient(app)
        register = client.post(
            "/api/auth/register",
            json={
                "username": "agent-user",
                "phone_number": "+60128887777",
                "password": "secret123",
            },
        )
        token = register.json()["access_token"]
        response = client.post(
            "/api/agent/query",
            headers={"Authorization": f"Bearer {token}"},
            json={"message": "hello", "context": {"surface": "chatbot"}},
        )
    finally:
        app.dependency_overrides.pop(get_deepseek_agent_client, None)

    assert response.status_code == 200
    assert response.json()["model"] == "deepseek-v4-flash"
    assert response.json()["evidence_status"] == "insufficient_evidence"


def test_agent_uses_configured_model_when_provider_omits_model_name() -> None:
    fake_client = FakeModelClient(
        [
            {
                "id": "response-without-model",
                "choices": [
                    {
                        "finish_reason": "stop",
                        "message": {
                            "role": "assistant",
                            "content": _answer_content(),
                        },
                    }
                ],
            }
        ]
    )
    fake_client.model = "configured-agent-model"

    response = QueryAgentUseCase(
        toolbox=cast(AgentToolbox, FakeToolbox()),
        model_client=fake_client,
    ).execute(
        payload=AgentQueryDto.model_validate(
            {"message": "hello", "context": {"surface": "chatbot"}}
        ),
        user_id="user-1",
    )

    assert response.model == "configured-agent-model"


def test_admin_agent_uses_enabled_read_tools_and_filters_all_actions() -> None:
    fake_client = FakeModelClient(
        [
            _completion(
                {
                    "role": "assistant",
                    "content": None,
                    "tool_calls": [
                        {
                            "id": "call-admin-summary",
                            "type": "function",
                            "function": {
                                "name": "get_admin_operations_summary",
                                "arguments": "{}",
                            },
                        }
                    ],
                },
                "tool_calls",
            ),
            _completion(
                {
                    "role": "assistant",
                    "content": _answer_content(
                        suggested_actions=[
                            {
                                "action": "open_admin_payments",
                                "label": "Open payments",
                                "parameters": {},
                            },
                            {
                                "action": "update_inventory_stock",
                                "label": "Set JS-63 stock to 12",
                                "parameters": {
                                    "catalog_id": "kumpoo-js-63",
                                    "current_stock": "12",
                                },
                            },
                        ]
                    ),
                },
                "stop",
            ),
        ]
    )
    app.dependency_overrides[get_deepseek_agent_client] = lambda: cast(
        DeepSeekAgentClient,
        fake_client,
    )
    try:
        client = TestClient(app)
        response = client.post(
            "/api/agent/query",
            headers={"Authorization": f"Bearer {_login_admin(client)}"},
            json={
                "message": "Summarize today's operations.",
                "context": {"surface": "admin_assistant"},
            },
        )
    finally:
        app.dependency_overrides.pop(get_deepseek_agent_client, None)

    assert response.status_code == 200
    assert response.json()["sources"][0]["source_type"] == "admin_operations"
    assert response.json()["suggested_actions"] == []
    offered_tools = {tool["function"]["name"] for tool in fake_client.calls[0]["tools"]}
    assert offered_tools == {
        "get_admin_operations_summary",
        "find_admin_bookings",
        "find_admin_inventory",
    }
    assert fake_client.calls[0]["tool_choice"] == "auto"
    admin_instruction = next(
        message
        for message in fake_client.calls[0]["messages"]
        if message.get("content", "").startswith(
            "You are assisting an authenticated StringSense administrator"
        )
    )
    assert admin_instruction["role"] == "system"
    instruction = admin_instruction["content"]
    assert "Match the response shape to the administrator's question" in instruction
    assert "Do not force a fixed list template" in instruction
    assert "one record per line" not in instruction
    assert "Name: value" not in instruction
    assert (
        "If the answer already contains the requested facts, use an empty evidence list"
        in instruction
    )
    assert "Answer in the language of the latest administrator question" in instruction
    assert "check that the summary, answer, and evidence agree" in instruction
    assert "Do not retrieve or append unrelated operations data" in instruction
    assert "state how many records were returned" in instruction
    assert "Never expose secrets" in instruction
    assert "booking search" in instruction
    assert "inventory search" in instruction
    assert "no suggested questions or actions" in instruction
    assert "aggregate payment and unread-support workload counts" in instruction
    assert "individual payment or support records" in instruction


def test_agent_surface_rejects_the_wrong_role() -> None:
    fake_client = FakeModelClient(
        [_completion({"role": "assistant", "content": _answer_content()}, "stop")]
    )
    app.dependency_overrides[get_deepseek_agent_client] = lambda: cast(
        DeepSeekAgentClient,
        fake_client,
    )
    try:
        client = TestClient(app)
        register = client.post(
            "/api/auth/register",
            json={
                "username": "agent-player",
                "phone_number": "+60128887778",
                "password": "secret123",
            },
        )
        player_token = register.json()["access_token"]
        player_to_admin = client.post(
            "/api/agent/query",
            headers={"Authorization": f"Bearer {player_token}"},
            json={
                "message": "Show admin work",
                "context": {"surface": "admin_assistant"},
            },
        )
        admin_to_player = client.post(
            "/api/agent/query",
            headers={"Authorization": f"Bearer {_login_admin(client)}"},
            json={"message": "hello", "context": {"surface": "chatbot"}},
        )
    finally:
        app.dependency_overrides.pop(get_deepseek_agent_client, None)

    assert player_to_admin.status_code == 403
    assert admin_to_player.status_code == 403
    assert fake_client.calls == []
