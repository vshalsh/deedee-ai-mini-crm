CREATE UNIQUE INDEX contacts_workspace_id ON contacts(workspace_id, id);
CREATE TABLE deals (
 id TEXT PRIMARY KEY, workspace_id TEXT NOT NULL REFERENCES workspaces(id),
 title TEXT NOT NULL, company_id TEXT, contact_id TEXT,
 amount TEXT NOT NULL, currency TEXT NOT NULL,
 stage TEXT NOT NULL CHECK(stage IN ('lead','qualified','proposal','won','lost')),
 expected_close_date TEXT, notes TEXT,
 created_at TEXT NOT NULL, updated_at TEXT NOT NULL,
 UNIQUE(workspace_id,id),
 FOREIGN KEY(workspace_id,company_id) REFERENCES companies(workspace_id,id) ON DELETE RESTRICT,
 FOREIGN KEY(workspace_id,contact_id) REFERENCES contacts(workspace_id,id) ON DELETE RESTRICT
);
CREATE TABLE tasks (
 id TEXT PRIMARY KEY, workspace_id TEXT NOT NULL REFERENCES workspaces(id),
 title TEXT NOT NULL, due_date TEXT, status TEXT NOT NULL CHECK(status IN ('open','in_progress','done')),
 company_id TEXT, contact_id TEXT, deal_id TEXT, notes TEXT,
 created_at TEXT NOT NULL, updated_at TEXT NOT NULL,
 FOREIGN KEY(workspace_id,company_id) REFERENCES companies(workspace_id,id) ON DELETE RESTRICT,
 FOREIGN KEY(workspace_id,contact_id) REFERENCES contacts(workspace_id,id) ON DELETE RESTRICT,
 FOREIGN KEY(workspace_id,deal_id) REFERENCES deals(workspace_id,id) ON DELETE RESTRICT
);
CREATE TABLE activities (
 id TEXT PRIMARY KEY, workspace_id TEXT NOT NULL REFERENCES workspaces(id),
 type TEXT NOT NULL CHECK(type IN ('note','call','meeting','email')),
 occurred_at TEXT NOT NULL, note TEXT NOT NULL, company_id TEXT, contact_id TEXT, deal_id TEXT,
 created_at TEXT NOT NULL, updated_at TEXT NOT NULL,
 FOREIGN KEY(workspace_id,company_id) REFERENCES companies(workspace_id,id) ON DELETE RESTRICT,
 FOREIGN KEY(workspace_id,contact_id) REFERENCES contacts(workspace_id,id) ON DELETE RESTRICT,
 FOREIGN KEY(workspace_id,deal_id) REFERENCES deals(workspace_id,id) ON DELETE RESTRICT
);
CREATE TABLE deal_history (
 id INTEGER PRIMARY KEY AUTOINCREMENT, deal_id TEXT NOT NULL REFERENCES deals(id) ON DELETE CASCADE,
 from_stage TEXT, to_stage TEXT NOT NULL, changed_at TEXT NOT NULL
);
CREATE INDEX deals_workspace_stage ON deals(workspace_id,stage);
CREATE INDEX tasks_workspace_due ON tasks(workspace_id,status,due_date);
CREATE INDEX activities_workspace_time ON activities(workspace_id,occurred_at);
