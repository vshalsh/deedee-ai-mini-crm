"""SQLite implementation; SQL stays behind the repository boundary."""
from contextlib import contextmanager
from datetime import datetime, timezone
from importlib.resources import files
from pathlib import Path
import json
import sqlite3
from uuid import uuid4
from .domain import Conflict, NotFound

KINDS = {
    "companies": ("name", "website", "industry", "notes"),
    "contacts": ("name", "email", "phone", "title", "company_id", "tags"),
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
            raise Conflict("A linked company is missing or still has contacts.") from exc
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
            row = db.execute(f"SELECT * FROM {kind} WHERE id = ?", (record_id,)).fetchone()
            return self.decode(row)

    def update(self, kind, record_id, values):
        columns = self.columns(kind)
        values = dict(values)
        if kind == "contacts":
            values["tags"] = json.dumps(values["tags"])
        now = datetime.now(timezone.utc).isoformat()
        with self.connection() as db:
            result = db.execute(
                f"UPDATE {kind} SET " + ",".join(c + " = ?" for c in columns) +
                ", updated_at = ? WHERE id = ? AND workspace_id = 'local'",
                tuple(values[c] for c in columns) + (now, record_id),
            )
            if result.rowcount == 0:
                raise NotFound("Record not found.")
            return self.decode(db.execute(f"SELECT * FROM {kind} WHERE id = ?", (record_id,)).fetchone())

    def delete(self, kind, record_id):
        self.columns(kind)
        with self.connection() as db:
            result = db.execute(f"DELETE FROM {kind} WHERE id = ? AND workspace_id = 'local'", (record_id,))
            if result.rowcount == 0:
                raise NotFound("Record not found.")

    def list(self, kind, *, q="", limit=50, offset=0, company_id=None):
        self.columns(kind)
        where = "r.workspace_id = 'local'"
        args = []
        if q:
            escaped = q.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
            pattern = "%" + escaped + "%"
            fields = ["r.name", "r.industry"] if kind == "companies" else ["r.name", "r.email", "r.tags", "c.name"]
            where += " AND (" + " OR ".join(f"{f} LIKE ? ESCAPE '\\'" for f in fields) + ")"
            args.extend([pattern] * len(fields))
        if company_id and kind == "contacts":
            where += " AND r.company_id = ?"
            args.append(company_id)
        join = " LEFT JOIN companies c ON c.id = r.company_id AND c.workspace_id = r.workspace_id" if kind == "contacts" else ""
        with self.connection() as db:
            total = db.execute(f"SELECT COUNT(*) FROM {kind} r{join} WHERE {where}", args).fetchone()[0]
            rows = db.execute(
                f"SELECT r.* FROM {kind} r{join} WHERE {where} ORDER BY r.name COLLATE NOCASE, r.id LIMIT ? OFFSET ?",
                args + [limit, offset],
            ).fetchall()
            return {"items": [self.decode(row) for row in rows], "total": total, "limit": limit, "offset": offset}
