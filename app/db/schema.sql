-- Defines the schema for the posts table.

CREATE TABLE IF NOT EXISTS posts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    content TEXT NOT NULL,
    hashtags TEXT,
    status TEXT NOT NULL DEFAULT 'draft', -- e.g., 'draft', 'posted'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    posted_at TIMESTAMP
);
