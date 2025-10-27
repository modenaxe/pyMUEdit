import sqlite3
from pathlib import Path
from datetime import datetime


PATH_TO_SCHEMA = Path("./core/database/schema.sql")
PATH_TO_DATABASE = Path("./core/database/database.db")

schema_test = Path("./schema.sql")

# testsed == remember to change back to constnats
def init_db():
    """
    On app start up, initialise the database
    Create database.db if not present
    """
    try:
        with sqlite3.connect("database.db") as connection:
            print(f"Set up SQLite database successfully")
            
            cursor = connection.cursor()
            #testing update schema back 
            schema = schema_test.read_text()
            cursor.executescript(schema)
            connection.commit()
    except (sqlite3.OperationalError) as e:
        print("Failed to initialise database:", e)
        return None

# tested remember to change back to constants
def get_connection():
    """
    Starts connection to the database
    Returns a dictionary cursor
    """
    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    return conn


#--------------------------
# Session helper functions
#--------------------------

# tested 
def create_new_session() -> int:
    """
    Creates a new session 
    Returns sessionid of created session
    """
    with get_connection() as conn:
        cur = conn.execute("""
                INSERT INTO sessions (created_at)
                VALUES (?)
            """, (get_timestamp(),))
        conn.commit()
        return cur.lastrowid

# get session 

# -------------------------
# Files Helper functions
# -------------------------

def update_files(filepath):
    ts = get_timestamp()
    connection = get_connection()
    connection.execute("""
        INSERT INTO files (filepath, last_opened)
        VALUES (?, ?)
    """, (filepath, ts))
    connection.commit()





def get_recent_files(limit: int = 10):
    with get_connection() as conn:
        rows = conn.execute("""
            SELECT filepath, last_opened
            FROM files
            ORDER BY last_opened DESC
            LIMIT ?
        """, (limit,))
        return [dict(row) for row in rows]

def get_table_testing():
    with get_connection() as conn:
        rows = conn.execute("""
            SELECT sessionid, created_at 
            FROM sessions             
        """)
    return [dict(row) for row in rows]

# Session
# get session
# get all files from session




def get_timestamp() -> int:
    return int(datetime.now().timestamp())

init_db()
update_files('/Users/bboy221/capstone-project-25t3-3900-w14b-banana/data/trial1_20MVC.otb+')
p = create_new_session()
print(p)
print(get_table_testing())

