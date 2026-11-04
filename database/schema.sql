-- PyPath Database Schema
-- Target: PostgreSQL / Neon Serverless Postgres

-- 1. Users table: stores registered learners
CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Case-insensitive lookup index for email during login and registration
CREATE UNIQUE INDEX IF NOT EXISTS users_email_lower_idx ON users(LOWER(email));

-- 2. Tasks table: personal roadmap milestones & practice tasks
CREATE TABLE IF NOT EXISTS tasks (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    description TEXT DEFAULT '',
    category TEXT NOT NULL DEFAULT 'Practice',
    week INTEGER NOT NULL DEFAULT 1 CHECK (week >= 1 AND week <= 24),
    status TEXT NOT NULL DEFAULT 'todo' CHECK (status IN ('todo', 'doing', 'done')),
    due_date DATE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes for tasks:
-- Covers foreign key lookups and cascade deletes
CREATE INDEX IF NOT EXISTS tasks_user_idx ON tasks(user_id);
-- Optimizes GET /api/tasks (SELECT ... WHERE user_id = $1 ORDER BY created_at DESC)
CREATE INDEX IF NOT EXISTS tasks_user_created_idx ON tasks(user_id, created_at DESC);

-- 3. Sessions table: logged study timer sessions & notes
CREATE TABLE IF NOT EXISTS sessions (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    topic TEXT NOT NULL,
    duration_minutes INTEGER NOT NULL CHECK (duration_minutes > 0),
    notes TEXT DEFAULT '',
    session_date DATE NOT NULL DEFAULT CURRENT_DATE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes for study sessions:
-- Optimizes GET /api/sessions (SELECT ... WHERE user_id = $1 ORDER BY created_at DESC LIMIT 100)
CREATE INDEX IF NOT EXISTS sessions_user_created_idx ON sessions(user_id, created_at DESC);
-- Optimizes queries filtering or grouping by study date
CREATE INDEX IF NOT EXISTS sessions_user_date_idx ON sessions(user_id, session_date DESC);
