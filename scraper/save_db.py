
import sqlite3
import logging
from config.config_loader import load_config

# Setup basic logging
logging.basicConfig(level=logging.INFO)

config = load_config()
dbName = config["database"]

# Function to save the links to a SQLite database
def save_to_db(links, db_name=dbName):
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    
    # Create table if it doesn't exist
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS links (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT,
            text TEXT,
            href TEXT,
            classification TEXT,
            relevance_score REAL
        )
    ''')
    
    # Insert links into the database
    for link in links:
        cursor.execute('''
            INSERT INTO links (url, text, href, classification, relevance_score) 
            VALUES (?, ?, ?, ?, ?)
        ''', (link['url'],link['text'], link['href'], link['classification'], link['relevance_score']))
    
    conn.commit()
    conn.close()