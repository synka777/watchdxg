CREATE TABLE actions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    action_type VARCHAR(50),
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    notes TEXT
);