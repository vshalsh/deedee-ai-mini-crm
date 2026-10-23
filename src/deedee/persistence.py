"""SQLite implementation; SQL stays behind the repository boundary."""
from contextlib import contextmanager
from datetime import datetime, timezone
from datetime import date
from decimal import Decimal
from importlib.resources import files
from pathlib import Path
import json
import sqlite3
from uuid import uuid4
from .domain import Conflict, NotFound

KINDS = {
    "companies": ("name", "website", "industry", "notes"),
    "contacts": ("name", "email", "phone", "title", "company_id", "tags"),
    "deals": ("title", "company_id", "contact_id", "amount", "currency", "stage", "expected_close_date", "notes"),
    "tasks": ("title", "due_date", "status", "company_id", "contact_id", "deal_id", "notes"),
    "activities": ("type", "occurred_at", "note", "company_id", "contact_id", "deal_id"),
}


class SQLiteRepository:
    def __init__(self, path: str):
        self.path = str(Path(path).expanduser().resolve())
        Path(self.path).parent.mkdir(parents=True, exist_ok=True)

    @contextmanager
    def connection(self):
        db = sqlite3.connect(self.path, timeout=5)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA foreign_keys = ON")
        try:
            with db:
                yield db
        except sqlite3.IntegrityError as exc:
            raise Conflict("A linked record is missing, or this record is still referenced. Remove or reassign linked work first.") from exc
        finally:
            db.close()

    def initialize(self):
        with self.connection() as db:
            db.execute("CREATE TABLE IF NOT EXISTS schema_migrations (version TEXT PRIMARY KEY)")
            for migration in sorted(files("deedee").joinpath("migrations").iterdir(), key=lambda p: p.name):
                if migration.name.endswith(".sql") and not db.execute(
                    "SELECT 1 FROM schema_migrations WHERE version = ?", (migration.name,)
                ).fetchone():
                    # Schema and migration record are committed together.
                    script = migration.read_text(encoding="utf-8")
                    version = migration.name.replace("'", "''")
                    db.executescript("BEGIN IMMEDIATE;\n" + script +
                                     "\nINSERT INTO schema_migrations VALUES ('" + version + "');\nCOMMIT;")

    @staticmethod
    def decode(row):
        result = dict(row)
        if "tags" in result:
            result["tags"] = json.loads(result["tags"])
        return result

    @staticmethod
    def columns(kind):
        return KINDS[kind]  # Only application-owned resource constants are accepted.

    def get(self, kind, record_id):
        self.columns(kind)
        with self.connection() as db:
            row = db.execute(
                f"SELECT * FROM {kind} WHERE id = ? AND workspace_id = 'local'", (record_id,)
            ).fetchone()
            if row is None:
                raise NotFound("Record not found.")
            return self.decode(row)

    def create(self, kind, values):
        columns = self.columns(kind)
        record_id = str(uuid4())
        now = datetime.now(timezone.utc).isoformat()
        values = dict(values)
        if kind == "contacts":
            values["tags"] = json.dumps(values["tags"])
        fields = ("id", "workspace_id") + columns + ("created_at", "updated_at")
        args = (record_id, "local") + tuple(values[c] for c in columns) + (now, now)
        with self.connection() as db:
            db.execute(f"INSERT INTO {kind} ({','.join(fields)}) VALUES ({','.join('?' for _ in fields)})", args)
            if kind == 'deals':
                db.execute('INSERT INTO deal_history(deal_id,from_stage,to_stage,changed_at) VALUES (?,NULL,?,?)',
                           (record_id, values['stage'], now))
            row = db.execute(f"SELECT * FROM {kind} WHERE id = ?", (record_id,)).fetchone()
            return self.decode(row)

    def update(self, kind, record_id, values):
        columns = self.columns(kind)
        values = dict(values)
        if kind == "contacts":
            values["tags"] = json.dumps(values["tags"])
        now = datetime.now(timezone.utc).isoformat()
        with self.connection() as db:
            previous = db.execute(f"SELECT * FROM {kind} WHERE id = ? AND workspace_id = 'local'", (record_id,)).fetchone()
            result = db.execute(
                f"UPDATE {kind} SET " + ",".join(c + " = ?" for c in columns) +
                ", updated_at = ? WHERE id = ? AND workspace_id = 'local'",
                tuple(values[c] for c in columns) + (now, record_id),
            )
            if result.rowcount == 0:
                raise NotFound("Record not found.")
            if kind == 'deals' and previous['stage'] != values['stage']:
                db.execute('INSERT INTO deal_history(deal_id,from_stage,to_stage,changed_at) VALUES (?,?,?,?)',
                           (record_id, previous['stage'], values['stage'], now))
            return self.decode(db.execute(f"SELECT * FROM {kind} WHERE id = ?", (record_id,)).fetchone())

    def delete(self, kind, record_id):
        self.columns(kind)
        with self.connection() as db:
            result = db.execute(f"DELETE FROM {kind} WHERE id = ? AND workspace_id = 'local'", (record_id,))
            if result.rowcount == 0:
                raise NotFound("Record not found.")

    def list(self, kind, *, q="", limit=50, offset=0, company_id=None,
             contact_id=None, deal_id=None, stage=None, status=None):
        self.columns(kind)
        where = "r.workspace_id = 'local'"
        args = []
        if q:
            escaped = q.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
            pattern = "%" + escaped + "%"
            fields = {'companies': ['r.name','r.industry'],
                      'contacts': ['r.name','r.email','r.tags','c.name'],
                      'deals': ['r.title','r.notes'], 'tasks': ['r.title','r.notes'],
                      'activities': ['r.note']}[kind]
            where += " AND (" + " OR ".join(f"{f} LIKE ? ESCAPE '\\'" for f in fields) + ")"
            args.extend([pattern] * len(fields))
        for field, value in [('company_id',company_id), ('contact_id',contact_id),
                             ('deal_id',deal_id), ('stage',stage), ('status',status)]:
            if value is not None and field in KINDS[kind]:
                where += f' AND r.{field} = ?'
                args.append(value)
        join = " LEFT JOIN companies c ON c.id = r.company_id AND c.workspace_id = r.workspace_id" if kind == "contacts" else ""
        with self.connection() as db:
            order = 'r.occurred_at DESC, r.id' if kind == 'activities' else (
                'r.due_date IS NULL, r.due_date, r.id' if kind == 'tasks' else
                ('r.name COLLATE NOCASE, r.id' if kind in {'contacts','companies'} else 'r.created_at DESC, r.id'))
            total = db.execute(f"SELECT COUNT(*) FROM {kind} r{join} WHERE {where}", args).fetchone()[0]
            rows = db.execute(
                f"SELECT r.* FROM {kind} r{join} WHERE {where} ORDER BY {order} LIMIT ? OFFSET ?",
                args + [limit, offset],
            ).fetchall()
            return {"items": [self.decode(row) for row in rows], "total": total, "limit": limit, "offset": offset}

    def history(self, record_id):
        self.get('deals', record_id)
        with self.connection() as db:
            return {'items': [dict(row) for row in db.execute(
                'SELECT from_stage,to_stage,changed_at FROM deal_history WHERE deal_id=? ORDER BY id', (record_id,))]}

    def dashboard(self):
        today = date.today().isoformat()
        with self.connection() as db:
            db.execute('BEGIN')
            counts = {kind: db.execute(f"SELECT COUNT(*) FROM {kind} WHERE workspace_id='local'").fetchone()[0]
                      for kind in KINDS}
            counts['open_tasks'] = db.execute("SELECT COUNT(*) FROM tasks WHERE workspace_id='local' AND status!='done'").fetchone()[0]
            counts['overdue_tasks'] = db.execute("SELECT COUNT(*) FROM tasks WHERE workspace_id='local' AND status!='done' AND due_date<?", (today,)).fetchone()[0]
            totals = {}
            for row in db.execute("SELECT amount,currency,stage FROM deals WHERE workspace_id='local'"):
                currency = totals.setdefault(row['currency'], {})
                currency[row['stage']] = currency.get(row['stage'], Decimal('0')) + Decimal(row['amount'])
            return {'counts': counts, 'as_of': today,
                    'pipeline_totals': {currency: {stage: str(amount) for stage,amount in stages.items()}
                                        for currency,stages in totals.items()}}

    def backup(self):
        with self.connection() as db:
            db.execute('BEGIN')
            data = {kind: [self.decode(row) for row in db.execute(
                f"SELECT * FROM {kind} WHERE workspace_id='local' ORDER BY id")] for kind in KINDS}
            data['deal_history'] = [dict(row) for row in db.execute(
                "SELECT h.* FROM deal_history h JOIN deals d ON d.id=h.deal_id WHERE d.workspace_id='local' ORDER BY h.id")]
            return {'format_version': 1, 'workspace': 'local', **data}
