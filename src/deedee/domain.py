"""CRM entities and reference errors; no HTTP or database dependencies."""
from dataclasses import dataclass, field
from typing import Protocol


@dataclass(frozen=True)
class Company:
    name: str
    website: str | None = None
    industry: str | None = None
    notes: str | None = None

    def __post_init__(self):
        if not self.name.strip() or len(self.name) > 200:
            raise ValueError("Company name must contain 1–200 characters.")


@dataclass(frozen=True)
class Contact:
    name: str
    email: str | None = None
    phone: str | None = None
    title: str | None = None
    company_id: str | None = None
    tags: list[str] = field(default_factory=list)

    def __post_init__(self):
        if not self.name.strip() or len(self.name) > 200:
            raise ValueError("Contact name must contain 1–200 characters.")


class NotFound(Exception):
    pass


class Conflict(Exception):
    pass


class Repository(Protocol):
    def create(self, kind: str, values: dict) -> dict: ...
    def get(self, kind: str, record_id: str) -> dict: ...
    def update(self, kind: str, record_id: str, values: dict) -> dict: ...
    def delete(self, kind: str, record_id: str) -> None: ...
    def list(self, kind: str, *, q: str, limit: int, offset: int,
             company_id: str | None = None) -> dict: ...
