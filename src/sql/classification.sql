CREATE TABLE IF NOT EXISTS classification (
    user_id INTEGER PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    harmful BOOLEAN DEFAULT FALSE,
    inactive BOOLEAN DEFAULT FALSE,
    classified_at TIMESTAMPTZ DEFAULT NOW(),
    notes TEXT  -- optional
);