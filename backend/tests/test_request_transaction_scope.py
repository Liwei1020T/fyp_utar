from __future__ import annotations

import asyncio
from collections.abc import Iterable

import pytest
from fastapi.dependencies.models import Dependant
from fastapi.routing import APIRoute
from sqlalchemy.orm import Session
from starlette.types import Message
from starlette.types import Scope

from app.adapters.persistence.sqlalchemy.session import get_db
from app.main import app


def _iter_api_routes(routes: Iterable[object]) -> Iterable[APIRoute]:
    for route in routes:
        if isinstance(route, APIRoute):
            yield route
        original_router = getattr(route, "original_router", None)
        if original_router is not None:
            yield from _iter_api_routes(original_router.routes)


def _iter_dependants(dependant: Dependant) -> Iterable[Dependant]:
    yield dependant
    for child in dependant.dependencies:
        yield from _iter_dependants(child)


def _get_db_dependants() -> list[Dependant]:
    return [
        dependant
        for route in _iter_api_routes(app.routes)
        for dependant in _iter_dependants(route.dependant)
        if dependant.call is get_db
    ]


def test_all_get_db_dependencies_are_function_scoped_and_cached() -> None:
    db_dependants = _get_db_dependants()

    assert db_dependants
    assert {dependant.scope for dependant in db_dependants} == {"function"}
    assert {dependant.use_cache for dependant in db_dependants} == {True}


def test_commit_failure_happens_before_asgi_response_start(
    monkeypatch,
) -> None:
    events: list[str] = []
    responses: list[Message] = []

    def fail_commit(_: Session) -> None:
        events.append("db.commit")
        raise RuntimeError("forced ASGI commit failure")

    monkeypatch.setattr(Session, "commit", fail_commit)

    async def receive() -> Message:
        return {"type": "http.request", "body": b"", "more_body": False}

    async def send(message: Message) -> None:
        events.append(str(message["type"]))
        responses.append(message)

    async def probe() -> None:
        scope: Scope = {
            "type": "http",
            "asgi": {"version": "3.0", "spec_version": "2.0"},
            "http_version": "1.1",
            "method": "GET",
            "scheme": "http",
            "path": "/health",
            "raw_path": b"/health",
            "query_string": b"",
            "headers": [],
            "client": ("test", 1),
            "server": ("test", 80),
            "root_path": "",
        }
        await app(
            scope,
            receive,
            send,
        )

    with pytest.raises(RuntimeError, match="forced ASGI commit failure"):
        asyncio.run(probe())

    assert events.index("db.commit") < events.index("http.response.start")
    assert responses[0]["status"] == 500
