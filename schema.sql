CREATE TABLE metadata (
    key TEXT,
    value TEXT
);
INSERT INTO metadata (key, value) VALUES ('last_updated', 'N/A');

CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    name TEXT,
    photo_url TEXT,
    is_sales INTEGER DEFAULT 0,
    is_supply INTEGER DEFAULT 0,
    date_register TEXT
);
CREATE TABLE calls (
    id INTEGER PRIMARY KEY,
    user_id INTEGER,
    duration INTEGER,
    start_time TEXT
);
CREATE TABLE deals (
    id INTEGER PRIMARY KEY,
    title TEXT,
    type_id TEXT,
    sales_user_id INTEGER,
    supply_user_id INTEGER,
    pipeline_id INTEGER,
    stage_id TEXT,
    stage_semantic_id TEXT,
    opportunity INTEGER,
    profit INTEGER,
    date_modify TEXT
);
CREATE TABLE kp_files (
    file_id INTEGER PRIMARY KEY,
    deal_id INTEGER,
    kp_date TEXT,
    original_file_name TEXT,
    remote_file_path TEXT,
    summary TEXT
);
CREATE TABLE deals_stage_history (
    id INTEGER PRIMARY KEY,
    deal_id INTEGER,
    old_pipeline_id INTEGER,
    new_pipeline_id INTEGER,
    old_stage_id TEXT,
    new_stage_id TEXT,
    stage_semantic_id TEXT,
    record_time TEXT
);
CREATE TABLE payments (
    id INTEGER PRIMARY KEY,
    deal_id INTEGER,
    amount INTEGER,
    payment_time INTEGER,
    payment_type TEXT
);
CREATE TABLE trips (
    id INTEGER PRIMARY KEY,
    user_id INTEGER,
    stage_id TEXT,
    begin_time TEXT,
    end_time TEXT,
    date_modify TEXT
);
CREATE TABLE trip_expenses (
    id INTEGER PRIMARY KEY,
    trip_id INTEGER,
    amount INTEGER
)