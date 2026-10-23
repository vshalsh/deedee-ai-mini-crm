# DeeDee module guide

## Current implementation — 0.2.0

The local CRM now includes browser screens for contacts, companies, deals,
follow-up tasks, activities, and mock summaries. Deal stage history, dashboard
totals, relationship constraints, and JSON backup export are implemented.
External BYOK, authentication, saved suggestion review, and CSV import/restore
remain future work. See [working CRM guide](working-crm.md) for current behavior.
The remaining sections describe the full module design and future extensions.

This document defines module boundaries so contributors can build DeeDee one piece at a time. Each module should have a small public interface and tests. Avoid importing database or model-provider details into CRM domain logic.

## 1. CRM domain

**Owns:** core record types, identifiers, validation, and business rules.

- `Contact`: name, email, phone, title, company reference, tags.
- `Company`: name, website, industry, notes.
- `Deal`: title, company/contact references, amount, currency, stage, expected close date.
- `Activity`: type, timestamp, note, linked contact/company/deal.
- `Task`: title, due date, status, owner, linked CRM records.

**Rules:** use stable IDs; validate references; represent deal stages explicitly; keep timestamps timezone-aware. Domain rules must work without a database or AI package.

## 2. Persistence

**Owns:** database schema, migrations, and repositories.

- Start with SQLite and seed data.
- Expose repository interfaces to the API and application services.
- Enforce foreign keys and useful indexes.
- Keep migration history in source control.

No API route or AI workflow should issue ad-hoc SQL directly.

## 3. API

**Owns:** versioned HTTP endpoints and request/response schemas.

Initial resource families:

- `/api/v1/contacts`
- `/api/v1/companies`
- `/api/v1/deals`
- `/api/v1/activities`
- `/api/v1/tasks`
- `/api/v1/ai/*` for explicit, reviewable suggestions

Add pagination, filtering, validation errors, and API tests. Keep the AI routes separate from ordinary CRUD routes.

## 4. Contacts and companies

**Owns:** contact/company CRUD, search, and relationship views.

- Search by name, email, company, or tag.
- Display the company and recent activity on a contact detail page.
- Prevent duplicate records from CSV import where a reliable match can be made; report ambiguous matches for review.

## 5. Deal pipeline

**Owns:** opportunity lifecycle.

- Use a configurable but finite set of stages (initial default: `lead`, `qualified`, `proposal`, `won`, `lost`).
- Record stage changes and timestamps.
- Show amount totals by stage.
- Do not allow AI to change a stage without explicit human approval.

## 6. Activities and tasks

**Owns:** the customer timeline and follow-up work.

- Activities are dated events or notes, not mutable status fields.
- Tasks have a title, due date, status, and links to related records.
- AI-extracted tasks enter a review queue before becoming saved tasks.

## 7. Web interface

**Owns:** user-facing CRM screens and settings.

Suggested screens:

- Dashboard: open deals, tasks due, recent activity.
- Contacts and companies: searchable lists and detail pages.
- Deals: pipeline board and deal detail.
- Timeline: notes, calls, and meetings.
- AI settings: provider selection, key entry, model, usage information.
- Suggestion review: source context, proposed changes, approve/edit/reject.

The frontend stack is intentionally open. Keep API contracts independent of the chosen UI framework.

## 8. AI provider gateway

**Owns:** the interface between DeeDee and model providers.

Define a small provider contract, for example:

- `summarize(context, options) -> SummaryResult`
- `extract_tasks(note, options) -> list[TaskSuggestion]`
- `draft_follow_up(context, goal, options) -> DraftResult`

Implement a deterministic mock first. Add a BYOK adapter only after the mock tests pass. Keep provider-specific request formatting, retry behavior, and error translation inside the adapter.

## 9. Context and prompt builder

**Owns:** selecting, minimizing, and formatting CRM context.

- Accept explicit record IDs and an action type.
- Fetch only those records and the minimum linked context needed.
- Remove fields not needed for the task.
- Apply a maximum context size.
- Label record content as untrusted data so instructions embedded in notes cannot override system behavior.
- Return a previewable context object for the UI and tests.

## 10. AI workflows

**Owns:** product-level AI actions built on domain services and the provider gateway.

First three actions:

1. Summarize a selected contact, company, or deal timeline.
2. Extract proposed follow-up tasks from a meeting note.
3. Draft a follow-up message for a user-selected goal and recipient.

AI workflow services return suggestions with source record IDs. They do not directly mutate CRM records or send outbound messages.

## 11. Review, audit, and usage

**Owns:** approval boundaries and operational traceability.

- Record who requested an AI action, provider/model label, action type, timestamp, and token/usage metadata if provided.
- Do not store API keys, raw prompts, or full customer records in the audit log.
- Validate model output against a strict schema.
- Require explicit approval before applying a suggestion.
- Support per-action limits and clear provider errors.

## 12. Import and export

**Owns:** portable sample data and user-controlled backup.

- CSV import for contacts and companies with a preview and validation report.
- CSV export for core CRM lists.
- JSON backup and restore for the full local workspace.
- Never include provider keys in exports.

## Dependency direction

```text
Web UI -> API -> Application services -> Domain
                         |              |
                         v              v
                    Repositories   AI gateway
                         |              |
                       SQLite     Mock / BYOK adapter
```

Domain logic should not depend on FastAPI, SQLite, a frontend framework, or a model provider.
