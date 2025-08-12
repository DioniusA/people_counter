CREATE TABLE streams (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    url TEXT NOT NULL,
    last_count INTEGER DEFAULT 0,
    last_update TIMESTAMP NULL
);

CREATE TABLE counts (
    id SERIAL PRIMARY KEY,
    stream_id INTEGER NOT NULL REFERENCES streams(id) ON DELETE CASCADE,
    camera_name VARCHAR(255) NOT NULL,
    people_count INTEGER NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    image_path TEXT NULL
);
