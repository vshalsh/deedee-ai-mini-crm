# Foundation lesson: companies, contacts, and a local AI boundary

## What is implemented

| Module | Source | Behavior |
| --- | --- | --- |
| Domain | `src/deedee/domain.py` | Company/contact dataclasses, name rules, repository protocol, errors |
| Persistence | `src/deedee/persistence.py` | Parameterized queries, single local workspace, foreign keys, rollback |
| Migrations | `src/deedee/migrations/001_foundation.sql` | Schema plus migration history, applied on startup |
| HTTP schemas | `src/deedee/schemas.py` | Input validation, unknown-field rejection, response contracts |
| Services | `src/deedee/services.py` | CRM use cases, selected-record context, provider protocol and mock |
| API | `src/deedee/api.py` | FastAPI routes, status codes, consistent application errors |
| Demo | `examples/foundation_demo.py` | Real API with temporary SQLite and fictional data |

This is a compact Python package rather than a monorepo of separately deployable
packages. Preserve dependency direction when adding modules.

## Setup and exercise

Follow the README, start the API, and open `http://127.0.0.1:8000/docs`.

1. POST a company with `{"name":"Northstar Analytics","industry":"Business software"}`.
2. Copy its returned UUID into a contact's `company_id`.
3. POST a contact with name, email, title, company_id, and optional tags.
4. GET contacts with `q=Northstar` or the company's ID as a filter.
5. POST selected IDs to the context route and inspect the returned fields.
6. POST the same IDs with `confirm=true` to request a mock summary.

## API contract

All resource routes are below `/api/v1`.

| Method | Path | Purpose |
| --- | --- | --- |
| POST | /companies, /contacts | Create; 201 with saved record |
| GET | /companies, /contacts | Search/list with total, limit, offset |
| GET | /companies/{id}, /contacts/{id} | Read; 404 if missing |
| PUT | /companies/{id}, /contacts/{id} | Full replacement of editable fields |
| DELETE | /companies/{id}, /contacts/{id} | Delete; 204; linked company deletion returns 409 |
| POST | /ai/context | Preview selected records |
| POST | /ai/summarize | Generate a suggestion after explicit confirmation |

PUT requires a name; omitted optional fields reset to null or an empty list.
Server-owned ID, workspace, and timestamps cannot be supplied in write bodies.
Timestamps are UTC; IDs are UUIDs. Duplicate contact emails are allowed; future
imports will need explicit duplicate review rules.

List parameters: `q` (up to 200 characters), `limit` (1–100; default 50),
`offset` (zero or greater). Contacts additionally accept `company_id`.
Contact search matches name, email, tags, or linked company name; company search
matches name or industry. SQLite LIKE provides basic case-insensitive matching
for ASCII, not full international text search. Results order by name then ID.
The database enforces company references. Remove/reassign contacts before deleting
a linked company.

Application errors have `{"error":{"code":"...","message":"..."}}`.
Validation errors add field locations and messages without echoing full payloads.
Relationship conflicts return 409; invalid inputs return 422.
Website validation permits HTTP(S) URLs without embedded credentials.
Email validation is a simple format check, not deliverability verification.

## Local mock contract

Context request:

```json
{"contact_ids":["CONTACT_ID"],"company_ids":["COMPANY_ID"]}
```

Only explicit records are included, with ID, kind, name, contact title or company
industry. No automatic traversal brings in the linked company's details.
No email, phone, notes, tags, or database export is passed to the provider.
A maximum of 20 selected IDs bounds context; field lengths are validated.

The summary request adds `"confirm":true`. The response identifies
`provider=mock`, `model=deterministic-v1`, `external_request=false`,
source IDs, and `suggestion_only=true`. Token usage is null because no model
was called. The service only reads records and returns text.
A later UI must present the preview and collect confirmation; this API flag
does not establish authenticated user consent.

## Verification and scope

Tests exercise CRUD, restart persistence, migration idempotency, references,
delete restrictions, failed-write rollback, search/pagination, invalid payloads,
missing records, minimal context, deterministic suggestions, no socket connections,
and unchanged database bytes after AI requests.

Run `python -m unittest discover -s tests -v`.
Run `python examples/foundation_demo.py` to exercise the complete foundation.

Verified on 21 October 2026 with Python 3.12: editable installation succeeded,
all 10 foundation tests passed, and the in-process API demo exited successfully.

This chapter describes the earlier foundation slice. Version 0.2.0 adds the
dashboard UI, deals, activities, tasks, deal-stage history, and JSON export.
Authentication, tenant membership, saved suggestion review, general audit history,
CSV import/restore, and external BYOK remain future work. See the [working CRM guide](working-crm.md). Bind the server to loopback for local use. Before shared hosting,
add authentication, authorization, deployment controls, and a reviewed secret
lifecycle. No provider credentials are accepted or stored by this implementation.
