from __future__ import annotations

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field


class RagDocument(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    text: str = Field(min_length=1)
    source: str | None = None


class RagQueryRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    query: str = Field(min_length=1)
    documents: list[RagDocument] = Field(default_factory=list)
    top_k: int = Field(default=3, ge=1, le=10)


class RagMatch(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    source: str | None = None
    score: float
    excerpt: str


class RagQueryResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    query: str
    answer: str
    matches: list[RagMatch]
    mode: str
