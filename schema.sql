CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    full_name TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'staff', -- 'admin' or 'staff'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS accounts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,          -- e.g., 'KBZPay Agent', 'Wave Money'
    account_number TEXT,
    balance REAL DEFAULT 0.0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS shifts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    opening_cash REAL NOT NULL,
    closing_cash REAL,
    expected_cash REAL,
    discrepancy REAL,
    status TEXT NOT NULL DEFAULT 'open', -- 'open' or 'closed'
    opened_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    closed_at TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    shift_id INTEGER,
    user_id INTEGER NOT NULL,
    trans_type TEXT NOT NULL, -- 'cash_in' (ငွေလွှဲ) or 'cash_out' (ငွေထုတ်) or 'internal_transfer'
    account_id INTEGER NOT NULL,
    amount REAL NOT NULL,
    commission REAL DEFAULT 0.0,
    customer_info TEXT,
    note TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (shift_id) REFERENCES shifts(id),
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (account_id) REFERENCES accounts(id)
);

CREATE TABLE IF NOT EXISTS audit_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    action TEXT NOT NULL,
    details TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

-- Default Settings
INSERT OR IGNORE INTO settings (key, value) VALUES ('default_commission_cash_out', '0.5');
INSERT OR IGNORE INTO settings (key, value) VALUES ('default_commission_cash_in', '1.0');
INSERT OR IGNORE INTO settings (key, value) VALUES ('shop_name', 'Prime MFS Express');