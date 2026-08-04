from typing import Literal

from pydantic import AnyHttpUrl, BaseModel, Field


class AuditRequest(BaseModel):
    url: AnyHttpUrl


class AgentRule(BaseModel):
    agent: str
    status: Literal["allowed", "blocked", "unknown"]


class RobotsReport(BaseModel):
    url: str
    found: bool
    passed: bool
    agents: list[AgentRule]
    error: str | None = None


class LLMsFileReport(BaseModel):
    url: str
    found: bool
    valid_markdown: bool
    has_h1: bool
    error: str | None = None


class LLMsReport(BaseModel):
    passed: bool
    files: list[LLMsFileReport]


class JavaScriptReport(BaseModel):
    raw_word_count: int
    rendered_word_count: int | None
    raw_to_rendered_ratio: float | None
    js_reliant: bool | None
    rendering_available: bool = True
    error: str | None = None


class SchemaReport(BaseModel):
    script_count: int
    types: list[str]
    key_entities: dict[str, bool]
    invalid_script_count: int


class AuditResponse(BaseModel):
    requested_url: str
    final_url: str
    robots: RobotsReport
    llms: LLMsReport
    javascript: JavaScriptReport
    schema_org: SchemaReport = Field(alias="schema")

    model_config = {"populate_by_name": True}
