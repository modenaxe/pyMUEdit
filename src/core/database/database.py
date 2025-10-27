import sqlite3
from pathlib import Path

schema_path = Path("./schema.sql")

def init_db():
    try:
        with sqlite3.conntect("database.db") as connection:
            print(f"Set up SQLite database successfully")
            
            cursor = connection.cursor()
            schema = schema_path.read_text()
            cursor.executescript(schema)
            connection.commit()

            return cursor
    except (sqlite3.OperationalError) as e:
        print("Failed to initialise database:", e)
        return None

def get_connection():
    with sqlite3.connect("database.db") as connection:
        cursor = connection.cursor()
        return connection, cursor
