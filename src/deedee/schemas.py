"""Strict HTTP contracts."""
import re
from urllib.parse import urlsplit
from pydantic import BaseModel, ConfigDict, Field, field_validator


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class CompanyInput(StrictModel):
    name: str = Field(min_length=1, max_length=200)
    website: str | None = Field(default=None, max_length=500)
    industry: str | None = Field(default=None, max_length=200)
    notes: str | None = Field(default=None, max_length=5000)

    @field_validator("website")
    @classmethod
    def valid_website(cls, value):
        if value is not None:
            parsed = urlsplit(value)
            if parsed.scheme not in {"http", "https"} or not parsed.hostname or parsed.username or parsed.password:
                raise ValueError("Website must be an HTTP(S) URL without credentials.")
        return value


class ContactInput(StrictModel):
    name: str = Field(min_length=1, max_length=200)
    email: str | None = Field(default=None, max_length=254)
    phone: str | None = Field(default=None, max_length=60)
    title: str | None = Field(default=None, max_length=200)
    company_id: str | None = Field(default=None, min_length=1, max_length=100)
    tags: list[str] = Field(default_factory=list, max_length=20)

    @field_validator("email")
    @classmethod
    def valid_email(cls, value):
        if value is not None and not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", value):
            raise ValueError("Email must have a local part and domain.")
        return value

    @field_validator("tags")
    @classmethod
    def valid_tags(cls, values):
        if any(not tag.strip() or len(tag) > 40 for tag in values):
            raise ValueError("Tags must contain 1–40 characters.")
        return sorted(set(tag.strip() for tag in values))


class Record(StrictModel):
    id: str
    workspace_id: str
    created_at: str
    updated_at: str


class CompanyOutput(CompanyInput, Record):
    pass


class ContactOutput(ContactInput, Record):
    pass


class CompanyPage(StrictModel):
    items: list[CompanyOutput]
    total: int
    limit: int
    offset: int


class ContactPage(StrictModel):
    items: list[ContactOutput]
    total: int
    limit: int
    offset: int


class Selection(StrictModel):
    contact_ids: list[str] = Field(default_factory=list, max_length=20)
    company_ids: list[str] = Field(default_factory=list, max_length=20)


class SummaryRequest(Selection):
    confirm: bool = False


class ContextRecord(StrictModel):
    id: str
    kind: str
    name: str
    title: str | None = None
    industry: str | None = None


class ContextPreview(StrictModel):
    provider: str = "mock"
    model: str = "deterministic-v1"
    external_request: bool = False
    records: list[ContextRecord]


class SummaryResult(ContextPreview):
    summary: str = Field(max_length=8000)
    source_ids: list[str]
    suggestion_only: bool = True
    usage: None = None
