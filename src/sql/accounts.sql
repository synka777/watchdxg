CREATE TABLE IF NOT EXISTS accounts (
    id SERIAL PRIMARY KEY,
    handle VARCHAR(255),
    UNIQUE (handle)
);