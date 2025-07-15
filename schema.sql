CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    name TEXT,
    photo_url TEXT,
    is_sales INTEGER DEFAULT 0,
    is_supply INTEGER DEFAULT 0
);
CREATE TABLE calls (
    id INTEGER PRIMARY KEY,
    user_id INTEGER,
    duration INTEGER,
    start_time TEXT
);
CREATE TABLE deals (
    id INTEGER PRIMARY KEY,
    sales_user_id INTEGER,
    supply_user_id INTEGER,
    pipeline_id INTEGER,
    stage_id INTEGER,
    opportunity INTEGER,
    profit INTEGER
);
CREATE TABLE payments (
    id INTEGER PRIMARY KEY,
    deal_id INTEGER,
    amount INTEGER,
    payment_date INTEGER,
    payment_type TEXT
);
CREATE TABLE deals_stage_history (
    id INTEGER PRIMARY KEY,
    deal_id INTEGER,
    pipeline_id INTEGER,
    stage_id INTEGER,
    stage_semantic_id INTEGER,
    record_time TEXT
);