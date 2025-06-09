CREATE TABLE IF NOT EXISTS posts (
    id BIGINT PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    timestamp TIMESTAMPTZ,
    username VARCHAR(255),
    handle VARCHAR(255),
    text TEXT,
    reposts INTEGER,
    likes INTEGER,
    replies INTEGER,
    views INTEGER,
    repost BOOLEAN,
    UNIQUE (user_id, timestamp)
);