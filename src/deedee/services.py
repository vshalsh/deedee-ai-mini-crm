"""Use cases keep transport, persistence, and provider details separate."""
from dataclasses import asdict
from typing import Protocol
from .domain import Company, Contact, Repository


class CRMService:
    def __init__(self, repository: Repository):
        self.repository = repository

    def save(self, kind, data, record_id=None):
        entity = Company(**data) if kind == "companies" else Contact(**data)
        values = asdict(entity)
        if record_id is None:
            return self.repository.create(kind, values)
        return self.repository.update(kind, record_id, values)


class SummaryProvider(Protocol):
    def summarize(self, records: list[dict]) -> str: ...


class MockProvider:
    """Deterministic string formatting, with no network or model dependency."""
    def summarize(self, records):
        return "Local mock summary: " + "; ".join(
            f"{record['kind']}: {record['name']}" for record in records
        ) + ". Review these selected records before planning a follow-up."


class AIService:
    def __init__(self, repository: Repository, provider: SummaryProvider):
        self.repository = repository
        self.provider = provider

    def context(self, selection):
        if len(selection.contact_ids) + len(selection.company_ids) > 20:
            raise ValueError("Select at most 20 records.")
        records = []
        for kind, ids in (("contacts", selection.contact_ids), ("companies", selection.company_ids)):
            for record_id in dict.fromkeys(ids):
                record = self.repository.get(kind, record_id)
                fields = ("id", "name", "title") if kind == "contacts" else ("id", "name", "industry")
                records.append(dict({key: record[key] for key in fields}, kind=kind))
        if not records:
            raise ValueError("Select at least one contact or company.")
        return records

    def summarize(self, records):
        return {
            "records": records,
            "summary": self.provider.summarize(records),
            "source_ids": [record["id"] for record in records],
        }
