CREATE TABLE IF NOT EXISTS todos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    description TEXT,
    complete_by TEXT NOT NULL,
    state TEXT NOT NULL DEFAULT 'NEW',
    created_date TEXT NOT NULL
);
