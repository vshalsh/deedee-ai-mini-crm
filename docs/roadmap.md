# DeeDee roadmap

A practical, learning-first build sequence. Complete one milestone with tests and documentation before starting the next.

| Milestone | Deliverable | Exit check |
|---|---|---|
| 0. Foundation | Scope, domain vocabulary, sample data, repo structure | Contributor can explain entities and boundaries |
| 1. Domain + persistence | Python domain models, SQLite schema, migrations, seeded demo workspace | Domain tests pass; fresh database can be created |
| 2. CRM API + core UI | Contacts and companies CRUD/search; basic dashboard | API tests pass; a user can add and find records |
| 3. Deals + work history | Deal pipeline, activities timeline, follow-up tasks | Relationship and stage rules are tested |
| 4. Import/export | CSV preview/import/export and JSON backup/restore | Invalid rows are reported; keys never appear in exports |
| 5. AI foundation | Provider interface, deterministic mock, BYOK settings, context preview | Mock works without network; keys are redacted |
| 6. AI suggestions | Timeline summary, note-to-task extraction, follow-up draft, review queue | Output is validated and human-approved before writes |
| 7. Hardening + learning docs | Security checks, tests, local setup, module lessons, contribution guide | A new contributor can fork and complete a module |

## Suggested first slice

Build one narrow end-to-end path:

1. Create a company.
2. Create a contact linked to it.
3. Create a deal linked to both.
4. Add a meeting note.
5. Display the note in the deal timeline.

This proves the domain, persistence, API, and UI boundaries before introducing AI.

## AI acceptance criteria

- No key is required for startup, tests, or the demo dataset.
- AI actions use only explicitly selected context.
- The user can inspect the context before the provider request.
- Model output includes source IDs and is schema-validated.
- Suggestions do not modify records until a user approves them.
- The app can handle provider timeout, invalid output, and quota errors without losing CRM data.

## Deferred ideas

Multi-tenant SaaS, roles beyond a local owner, email/calendar sync, autonomous agents, auto-sending, embeddings/vector search, billing, and enterprise reporting are out of the first learning build.