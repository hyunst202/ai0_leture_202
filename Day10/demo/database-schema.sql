-- note-demo: SQLite baseline schema.
-- Run this initialization script once against a new database.
-- Enable foreign_keys separately for every application connection as well.
-- UTC timestamps use ISO 8601; the application must update updated_at on edits.
-- PythonAnywhere deployment: use per-user Werkzeug password hashes.
-- Never persist plaintext passwords, shared demo passwords, or NULL hashes.
-- Flask signed sessions compare auth_version with this database on each request.
-- This is a fresh-database schema, not an in-place migration for an older DB.

PRAGMA foreign_keys = ON;

BEGIN TRANSACTION;

CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    email TEXT NOT NULL COLLATE NOCASE UNIQUE
        CHECK (email = trim(email) AND length(email) BETWEEN 3 AND 254),
    nickname TEXT NOT NULL
        CHECK (length(trim(nickname)) >= 1 AND length(nickname) <= 30),
    password_hash TEXT NOT NULL CHECK (length(trim(password_hash)) > 0),
    role TEXT NOT NULL DEFAULT 'USER'
        CHECK (role IN ('USER', 'ADMIN')),
    auth_version INTEGER NOT NULL DEFAULT 0 CHECK (auth_version >= 0),
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);

CREATE TABLE posts (
    id INTEGER PRIMARY KEY,
    author_id INTEGER NOT NULL,
    title TEXT NOT NULL
        CHECK (length(trim(title)) >= 1 AND length(title) <= 200),
    body TEXT NOT NULL
        CHECK (length(trim(body)) >= 1 AND length(body) <= 10000),
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    FOREIGN KEY (author_id) REFERENCES users (id) ON DELETE RESTRICT
);

CREATE TABLE comments (
    id INTEGER PRIMARY KEY,
    post_id INTEGER NOT NULL,
    author_id INTEGER NOT NULL,
    body TEXT NOT NULL
        CHECK (length(trim(body)) >= 1 AND length(body) <= 1000),
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    FOREIGN KEY (post_id) REFERENCES posts (id) ON DELETE CASCADE,
    FOREIGN KEY (author_id) REFERENCES users (id) ON DELETE RESTRICT
);

CREATE TABLE masking_rules (
    id INTEGER PRIMARY KEY,
    keyword TEXT NOT NULL COLLATE NOCASE UNIQUE
        CHECK (keyword = trim(keyword) AND length(keyword) BETWEEN 1 AND 100),
    replacement TEXT NOT NULL DEFAULT '***'
        CHECK (length(replacement) BETWEEN 1 AND 100),
    created_by INTEGER DEFAULT NULL,
    source_url TEXT DEFAULT NULL,
    source_checked_at TEXT DEFAULT NULL,
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    FOREIGN KEY (created_by) REFERENCES users (id) ON DELETE SET NULL
);

CREATE INDEX idx_posts_created_at_id ON posts (created_at DESC, id DESC);
CREATE INDEX idx_posts_author_id ON posts (author_id);
CREATE INDEX idx_comments_post_created_at_id ON comments (post_id, created_at, id);
CREATE INDEX idx_comments_author_id ON comments (author_id);
CREATE INDEX idx_masking_rules_created_by ON masking_rules (created_by);

PRAGMA user_version = 2;

COMMIT;
