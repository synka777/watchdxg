CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    account_id INTEGER REFERENCES accounts(id) ON DELETE CASCADE,
    handle VARCHAR(255),
    username VARCHAR(255),
    certified BOOLEAN,
    bio TEXT,
    created_at DATE,
    following_count INTEGER,
    followers_count INTEGER,
    following_str VARCHAR(255),
    followers_str VARCHAR(255),
    featured_url VARCHAR,
    follower BOOLEAN,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (handle, created_at)
);