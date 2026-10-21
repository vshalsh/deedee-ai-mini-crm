# DeeDee — AI Mini CRM

DeeDee is a **modular, forkable learning project** for building a small CRM with careful, user-controlled AI features and Bring Your Own Key (BYOK) support.

> **Project status:** runnable foundation. FastAPI + SQLite, company/contact CRUD,
> search and pagination, versioned schema migration, and a deterministic local
> mock summary are implemented. Deals, tasks, activities, frontend UI, and
> external BYOK adapters remain planned.

## Run locally

Requires Python 3.10+.

```sh
python -m venv .venv
. .venv/bin/activate
python -m pip install -e ".[test]"
uvicorn deedee.api:create_app --factory --host 127.0.0.1 --port 8000
```

On Windows PowerShell activate with `.venv\Scripts\Activate.ps1`.
Open http://127.0.0.1:8000/docs for the interactive API.
SQLite is initialized automatically at `data/deedee.db`; override with
`DEEDEE_DB_PATH`. Use a file-backed database path, not `:memory:`.
This foundation is a local, single-user learning API without authentication.

```sh
python -m unittest discover -s tests -v
python examples/foundation_demo.py
```

The demo uses temporary SQLite storage and fictional records, creates a company
and linked contact, previews selected context, and generates a mock suggestion.
The mock is deterministic text formatting, not an LLM. No API key is required.
See [foundation lesson and API guide](docs/foundation.md).

## What you will learn

- Model CRM records and relationships with a Python backend.
- Build contacts, companies, deals, activities, and follow-up tasks as separate modules.
- Add AI through a provider interface instead of coupling the CRM to one model vendor.
- Use a local mock provider for a no-key, no-network demo.
- Let a user bring an API key for optional AI actions.
- Give an AI only the CRM context needed for a task, validate its output, and require a human to approve changes.

## Product scope

The planned full version is a single-user, local-first CRM that can:

- Store contacts and companies.
- Track deals in a simple sales pipeline.
- Record notes, meetings, and calls in an activity timeline.
- Create and manage follow-up tasks.
- Ask AI to summarize selected records, extract suggested tasks from notes, and draft follow-up messages.

The goal is a teaching-sized CRM. Multi-tenant hosting, email/calendar sync, autonomous outbound messages, billing, and enterprise CRM features are later extensions.

## Module map

| Module | Responsibility | Build |
|---|---|---:|
| CRM domain | Contact, Company, Deal, Activity, Task entities and validation | 1 |
| Persistence | SQLite schema, migrations, repository interfaces, seed data | 1 |
| API | FastAPI endpoints, filtering, pagination, consistent errors | 2 |
| Contacts & companies | Customer records, search, relationship views | 2 |
| Deals pipeline | Deal stages, value, owner, close date, linked company/contact | 3 |
| Activities & tasks | Timeline, meeting/call notes, due dates, follow-ups | 3 |
| Web interface | Dashboard, lists, detail pages, pipeline, settings | 4 |
| AI provider gateway | Mock provider plus optional BYOK provider adapter | 5 |
| Context & prompt builder | Select and minimize CRM data for each AI request | 5 |
| AI workflows | Summaries, note extraction, and message drafts | 6 |
| Review & audit | Human approval, output validation, usage metadata, safe logs | 6 |
| Import/export | CSV import/export and JSON backup/restore | 7 |

Detailed responsibilities and interfaces: [Module guide](docs/modules.md).  
System boundaries and data flow: [Architecture](docs/architecture.md).  
BYOK and privacy rules: [Security guide](docs/security-byok.md).  
Milestones: [Roadmap](docs/roadmap.md).

## Recommended learning stack

- **Backend:** Python with FastAPI.
- **Local data:** SQLite for the first version; keep persistence behind repositories so another database can be added later.
- **Frontend:** intentionally flexible; choose a small web UI that can call the API.
- **Tests:** pytest for domain rules, API behavior, provider adapters, and safety checks.
- **AI:** local mock provider by default; optional provider adapter when a user configures their own key.

The no-key demo must remain useful. AI must be optional so contributors can run and learn the CRM without paying for an external API.

## AI safety contract

1. AI requests are opt-in and show which CRM records will be used.
2. Only selected, necessary context is sent to the configured provider.
3. AI output is a **suggestion**. It never silently edits CRM data or sends a message.
4. Validate structured output before showing it; show the source records behind summaries and extracted facts.
5. Never log API keys. Avoid logging raw CRM prompts or record contents.
6. Provide clear provider, model, and usage information where available.

See [Security and BYOK](docs/security-byok.md) before implementing an AI feature.

## Example workflow

1. Add a contact and link them to a company.
2. Open a deal and add a meeting note to its timeline.
3. Select **Summarize activity** and review the exact records DeeDee will use.
4. DeeDee returns a summary plus suggested follow-up tasks.
5. Review, edit, and approve each suggestion before saving it.

## Fork and build

1. Fork this repository.
2. Read the [roadmap](docs/roadmap.md) and pick one module.
3. Implement the domain/API contract before adding UI or AI behavior.
4. Add tests and update the relevant module guide.
5. Keep the mock provider working so others can learn without an API key.

The repository now includes the runnable foundation described above. No API keys or real customer data belong in commits. DeeDee is licensed under GNU Affero General Public License v3.0 or later (AGPL-3.0-or-later); see [LICENSE](LICENSE). Any future commercial edition or alternative license will require separate terms and review.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). Please use fictional records in examples and tests.

## License

GNU Affero General Public License v3.0 or later (AGPL-3.0-or-later). See [LICENSE](LICENSE).
