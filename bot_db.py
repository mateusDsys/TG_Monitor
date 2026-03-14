import sqlite3
import datetime

DB_FILE = "monitor_history.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    # MELHORIA: Ativa o modo WAL (Write-Ahead Logging) 
    # Isso evita o erro "database is locked" permitindo que a interface leia o histórico 
    # exatamente no mesmo milissegundo que o Telegram estiver gravando uma nova mensagem.
    conn.execute('PRAGMA journal_mode=WAL;')
    
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS matches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            rule TEXT,
            chat_name TEXT,
            chat_id INTEGER,
            sender_name TEXT,
            sender_id INTEGER,
            message_text TEXT,
            is_duplicate BOOLEAN DEFAULT 0
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS blacklist (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            entity_id INTEGER UNIQUE,
            entity_name TEXT,
            type TEXT
        )
    ''')
    
    conn.commit()
    conn.close()

def save_match(rule, chat_name, chat_id, sender_name, sender_id, message_text, is_duplicate=False):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO matches (timestamp, rule, chat_name, chat_id, sender_name, sender_id, message_text, is_duplicate)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (datetime.datetime.now(), rule, chat_name, chat_id, sender_name, sender_id, message_text, is_duplicate))
    conn.commit()
    conn.close()

def get_history(limit=100, filter_rule=None):
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    query = "SELECT * FROM matches"
    params = []
    
    if filter_rule:
        query += " WHERE rule = ?"
        params.append(filter_rule)
        
    query += " ORDER BY timestamp DESC LIMIT ?"
    params.append(limit)
    
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    return rows

def add_to_blacklist(entity_id, name, type_):
    conn = sqlite3.connect(DB_FILE)
    try:
        conn.execute("INSERT OR IGNORE INTO blacklist (entity_id, entity_name, type) VALUES (?, ?, ?)", 
                     (entity_id, name, type_))
        conn.commit()
    finally:
        conn.close()

def get_blacklist():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT entity_id FROM blacklist")
    ids = [row[0] for row in cursor.fetchall()]
    conn.close()
    return set(ids)

def clear_history():
    conn = sqlite3.connect(DB_FILE)
    conn.execute("DELETE FROM matches")
    conn.commit()
    conn.close()
