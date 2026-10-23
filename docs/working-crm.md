# Working CRM guide — 0.2.0

## Application structure

```text
src/deedee/
  api.py                 App, contact/company endpoints, static interface
  work_api.py            Deal, task, activity, dashboard, backup endpoints
  domain.py              Foundation domain entities and repository contract
  schemas.py             Customer and mock-AI request/response contracts
  work_schemas.py        Opportunity and work validation
  services.py            Foundation use cases and mock provider boundary
  persistence.py         Parameterized SQLite queries and transactions
  migrations/            Ordered schema migrations
  static/                Browser HTML, CSS, and JavaScript
```

The browser calls the same versioned API documented at `/docs`. Customer text
is inserted with DOM text nodes, rather than interpreted as HTML. No external
scripts, fonts, or styles are loaded. No frontend build is required.
The browser fetches the small local workspace in API pages and performs list
search/pagination locally. This is intended for a small CRM, not large datasets.

## Storage and upgrading

`DEEDEE_DB_PATH` sets a file-backed SQLite location; the default is
`data/deedee.db` relative to the launch directory. Do not use `:memory:`.
Startup applies missing SQL migrations and records them in `schema_migrations`.
Migration 002 adds workflow tables without replacing company/contact records.
Back up an existing database file before changing application versions.
Run a single server worker; simultaneous migration runners are not supported.

Record relationships are independent, optional references. A deal can link a
company and a contact even if that contact belongs to another company, such as
an external adviser. Each reference must exist in the local workspace.
Deletes are restricted while other records refer to a record. Deal history
is removed when its deal is explicitly deleted.

## Work API

Resource families under `/api/v1`: `companies`, `contacts`, `deals`,
`tasks`, and `activities`. Each supports POST, GET list, GET by ID, PUT full
replacement, and DELETE. PUT resets omitted optional fields; it is not PATCH.

| Resource | Additional behavior |
| --- | --- |
| Deals | `stage`, `company_id`, `contact_id` filters; GET /deals/{id}/history |
| Tasks | `status`, `company_id`, `contact_id`, `deal_id` filters |
| Activities | `company_id`, `contact_id`, `deal_id` filters; newest event first |
| Dashboard | GET /dashboard returns counts and exact decimal totals grouped by currency/stage |
| Backup | GET /backup returns a consistent read snapshot including deal history |

Common list arguments: `q`, `limit` 1–100, `offset` zero or higher.
The UI's overdue filter uses the device's current calendar date. The dashboard
API's `as_of` uses the server's calendar date. Neither uses a stored workspace
timezone in this version.

Deal stages: lead, qualified, proposal, won, lost. Values are non-negative
decimals with at most two decimal places and 14 total digits. Currency is a
three-letter uppercase label; no exchange-rate conversion is implemented.
History records the initial stage and each subsequent change transactionally.

Task status: open, in_progress, done. Due dates are optional ISO calendar dates.
Activities require a timezone-aware `occurred_at`, a note, and at least one
customer/deal reference. Timestamps normalize to UTC. Email-type activities
only log an event; they do not send a message.

Errors: 404 unknown record, 409 missing/referenced relationship, 422 invalid
input. Application errors use the foundation's JSON error envelope.

## Backups

The footer exports JSON containing companies, contacts, deals, tasks, activities,
and deal history. No model keys exist in the application. Backups contain
customer information; store them accordingly. Automated JSON restore and CSV
import are not implemented. A full SQLite file copy while the server is stopped
can preserve the complete local database for recovery.

## AI behavior

The UI requires a preview before enabling the summary action. Only explicitly
selected contacts and companies are included; their email, phone, notes, and
tags are excluded. Changing the selection invalidates the preview.
The provider is `mock` with model `deterministic-v1`: simple deterministic
formatting, with no external inference. Outputs identify source IDs and are
suggestions only. The confirmation flag is a UI control, not authentication.
Real BYOK providers and saved suggestion review remain future work.

## Verification

```sh
python -m pip install -e ".[test]"
python -m unittest discover -s tests -v
```

16 backend tests pass, including existing database upgrade, full workflow CRUD,
decimal totals, reference failures and rollback, stage history, backup export,
timezone normalization, and the mock no-network/no-write boundary.

Optional Node.js UI checks (Node 20.19+):

```sh
npm install --no-save jsdom
node tests/run_ui_smoke.cjs dom
```

The runner starts an isolated API and disposable database. It creates all five
record types through UI event handlers, moves a deal, verifies literal rendering
of script-like input, previews and confirms a mock summary, completes a task,
and checks saved state through the API.

For Chromium visual/layout checks:

```sh
npm install --no-save playwright
npx playwright install chromium
node tests/run_ui_smoke.cjs browser
```

Set `DEEDEE_TEST_PYTHON` when the Python executable is not named `python`.
Tests were run on 23 October 2026: all 16 backend tests, DOM-to-live-API
integration, and a full Chromium browser workflow passed. Desktop and mobile
screenshots were inspected, and the mobile page passed a horizontal-overflow
check. Browser checks cover creation, stage history, task completion, reload
persistence, literal text rendering, AI preview/confirmation, and backup download.

The standard Playwright browser CDN download failed in the test environment.
An alternative packaged Chromium completed verification:

```sh
npm install --no-save playwright @sparticuz/chromium
DEEDEE_PACKAGED_CHROMIUM=1 node tests/run_ui_smoke.cjs browser
```

The alternative command uses POSIX environment syntax and a Linux-compatible
Chromium package; standard Playwright installation is the portable default.

## Next modules

External BYOK adapter and provider/model settings; authentication and roles
before shared hosting; import/restore with validation; saved suggestion review
and audit metadata. Keep each module independently testable.
