# DeeDee — AI Mini CRM

DeeDee is a working local CRM with a browser interface, Python/FastAPI backend,
and SQLite persistence. It is a modular learning project under AGPL-3.0-or-later.

## Start DeeDee

Requires Python 3.10+.

```sh
git clone https://github.com/vshalsh/deedee-ai-mini-crm.git
cd deedee-ai-mini-crm
python -m venv .venv
. .venv/bin/activate
python -m pip install -e ".[test]"
python -m deedee
```

On Windows PowerShell, activate with `.venv\Scripts\Activate.ps1`.
Then open **http://127.0.0.1:8000/**. The interactive API is at
http://127.0.0.1:8000/docs.

All screens and assets are served by Python. No frontend build, Node.js runtime,
external CDN, model key, or paid AI service is needed to run the CRM.

## What works

| Module | Available behavior |
| --- | --- |
| Dashboard | Contact/company counts, active opportunities, open/overdue tasks, pipeline value by currency, recent activity |
| Companies | Create, view, edit, delete, search, notes and relationship details |
| Contacts | Create, view, edit, delete, search, tags and company links |
| Deals | Five-stage pipeline, values, currencies, expected close dates, record links and stage history |
| Follow-ups | Due dates, open/in-progress/done states, linked records and one-click completion |
| Timeline | Notes, calls, meetings and email records with timezone-aware event times |
| AI assistant | Select contacts/companies, preview minimal context, confirm a local mock summary |
| Backup | Download a JSON snapshot of CRM records and deal-stage history |

Lists include search, filters where applicable, and pagination. The pipeline
provides a stage selector on every deal. Record details show linked work.
Linked-record constraints prevent accidental deletion of referenced customers
or deals; reassign or remove their linked records first.

## First workflow

1. Open **Companies** and add a company.
2. Add a **Contact** linked to that company.
3. Add a **Deal**, choose a value/currency, and link the customer.
4. Log a meeting under **Activity timeline**, linked to the deal.
5. Add a **Follow-up**, set a due date, and complete it from the dashboard.
6. Move the deal to **Proposal** using its stage selector; open its details to
   inspect stage history.
7. Open **AI assistant**, select records, preview context, and confirm the mock
   summary. Suggestions do not save changes or send messages.
8. Use **Download JSON backup** in the footer to export your data.

The interface starts with an empty workspace. All data you enter persists in
`data/deedee.db` across restarts. Override the path with `DEEDEE_DB_PATH`.
Existing foundation databases upgrade automatically without deleting records.
Use one server worker for this local edition.

## Learn the modules

- [Working CRM guide](docs/working-crm.md): screens, API, storage, tests, and limits
- [Foundation lesson](docs/foundation.md): domain, repository, schemas, mock boundary
- [Module guide](docs/modules.md) and [architecture](docs/architecture.md)
- [Security and BYOK](docs/security-byok.md) and [roadmap](docs/roadmap.md)
- [Change log](CHANGELOG.md) and [contribution guide](CONTRIBUTING.md)

```sh
python -m unittest discover -s tests -v
python examples/foundation_demo.py
```

The demo uses fictional contacts and temporary storage. See the working CRM guide
for optional UI integration and visual-browser test commands.

## Current scope

Version 0.2.0 is a **local single-user CRM**. Bind it to loopback as the startup
command does. Authentication, shared hosting, tenant roles, CSV import, backup
restore, and external provider adapters remain future modules.

AI is currently a deterministic mock, clearly labeled in the interface; it does
not invoke an LLM. No provider keys are accepted or stored. BYOK remains planned.
There is no autonomous outbound messaging. Deal amounts are stored as decimals
and dashboard totals remain grouped by currency; currencies are never silently
converted. Email activity records are manual logs, not sent emails.

## License

GNU Affero General Public License v3.0 or later (AGPL-3.0-or-later).
See [LICENSE](LICENSE). Future commercial editions require separate terms.
