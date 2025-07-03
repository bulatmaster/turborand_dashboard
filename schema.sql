CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    name TEXT,
    photo_url TEXT,
    is_sales INTEGER DEFAULT 0,
    is_supply INTEGER DEFAULT 0
)