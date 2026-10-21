CREATE TABLE IF NOT EXISTS workspaces (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL
);
INSERT OR IGNORE INTO workspaces VALUES ('local', 'DeeDee Local Workspace');
CREATE TABLE IF NOT EXISTS companies (
    id TEXT PRIMARY KEY,
    workspace_id TEXT NOT NULL REFERENCES workspaces(id),
    name TEXT NOT NULL,
    website TEXT,
    industry TEXT,
    notes TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    UNIQUE(workspace_id, id)
);
CREATE TABLE IF NOT EXISTS contacts (
    id TEXT PRIMARY KEY,
    workspace_id TEXT NOT NULL REFERENCES workspaces(id),
    name TEXT NOT NULL,
    email TEXT,
    phone TEXT,
    title TEXT,
    company_id TEXT,
    tags TEXT NOT NULL DEFAULT '[]',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY(workspace_id, company_id) REFERENCES companies(workspace_id, id) ON DELETE RESTRICT
);
CREATE INDEX IF NOT EXISTS companies_workspace ON companies(workspace_id, name);
CREATE INDEX IF NOT EXISTS contacts_company ON contacts(workspace_id, company_id);
