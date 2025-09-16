-- TBCparcer Database Schema

-- Таблица пользователей
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    telegram_id BIGINT UNIQUE NOT NULL,
    username VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Таблица операторов (банки, платежные системы)
CREATE TABLE operators (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(255) NOT NULL,
    description VARCHAR(255), -- Приложение которое относится к оператору
    user_id INTEGER NULL, -- NULL для глобальных операторов
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Таблица транзакций
CREATE TABLE transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    date_time DATETIME NOT NULL,
    operation_type VARCHAR(50) NOT NULL, -- 'payment', 'refill', 'conversion', 'cancel'
    amount DECIMAL(15,2) NOT NULL,
    currency VARCHAR(10) NOT NULL DEFAULT 'UZS',
    card_number VARCHAR(20),
    description TEXT,
    balance DECIMAL(15,2),
    operator_id INTEGER,
    raw_text TEXT NOT NULL, -- Оригинальный текст чека
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (operator_id) REFERENCES operators(id) ON DELETE SET NULL
);

-- Таблица настроек форматирования для веб-интерфейса
CREATE TABLE formatting_settings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    column_name VARCHAR(50) NOT NULL,
    alignment VARCHAR(10) DEFAULT 'left', -- 'left', 'center', 'right'
    width INTEGER DEFAULT 150,
    position INTEGER DEFAULT 0,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE(user_id, column_name)
);

-- Таблица настроек цвета ячеек
CREATE TABLE cell_colors (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    transaction_id INTEGER NOT NULL,
    column_name VARCHAR(50) NOT NULL,
    background_color VARCHAR(7) DEFAULT '#FFFFFF', -- HEX цвет
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (transaction_id) REFERENCES transactions(id) ON DELETE CASCADE,
    UNIQUE(user_id, transaction_id, column_name)
);

-- Индексы для оптимизации
CREATE INDEX idx_transactions_user_date ON transactions(user_id, date_time);
CREATE INDEX idx_transactions_operator ON transactions(operator_id);
CREATE INDEX idx_operators_user ON operators(user_id);

-- Пользовательские операторы будут загружены из operators_dictionary.sql

