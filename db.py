import sqlite3

DB_PATH = "fantasy_bot.db"
TEST_DB_PATH = "fantasy_bot_test.db"


def get_connection(db_path=DB_PATH):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def get_test_connection(db_path=TEST_DB_PATH):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn
