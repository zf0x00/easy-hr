-- candidates table
CREATE SEQUENCE IF NOT EXISTS seq_candidates_id;
CREATE TABLE IF NOT EXISTS candidates (
    id INTEGER PRIMARY KEY DEFAULT nextval('seq_candidates_id'),
    name TEXT,
    email TEXT,
    phone TEXT,
    experience_years TEXT,
    skills TEXT,
    education_summary TEXT,
    professional_summary TEXT,
    raw_text TEXT,
    embedding DOUBLE[],
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- chat tables
CREATE SEQUENCE IF NOT EXISTS seq_chats_id;
CREATE SEQUENCE IF NOT EXISTS seq_chat_messages_id;

CREATE TABLE IF NOT EXISTS chats (
    id INTEGER PRIMARY KEY DEFAULT nextval('seq_chats_id'),
    title TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS chat_messages (
    id INTEGER PRIMARY KEY DEFAULT nextval('seq_chat_messages_id'),
    chat_id INTEGER REFERENCES chats(id),
    role TEXT NOT NULL, -- 'user' or 'assistant'
    content TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
