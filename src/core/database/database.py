import sqlite3
from pathlib import Path
from datetime import datetime


PATH_TO_SCHEMA = Path("./core/database/schema.sql")
PATH_TO_DATABASE = Path("./core/database/database.db")
RECENT_FILES_MAX = 10
STAGES = {}

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

            load_stage_map()
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

def load_stage_map():
    global STAGES
    with get_connection() as conn:
        rows = conn.execute("SELECT stageid, name FROM stages")
        STAGES = {row["name"]: row["stageid"] for row in rows}

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

# get session information

# get session files


# -------------------------
# Files Helper functions
# -------------------------

def insert_files(filepath: str, filename: str, sessionid: int):
    """
    Insert original, raw files into database.
    note: we will handle files under file_versions
    
    Returns fileid 
    """
    with get_connection() as conn:
        cur = conn.execute("""
            INSERT INTO files (filepath, filename, sessionid, created_at)
            VALUES (?, ?, ?)
        """, (filepath, filename, sessionid, get_timestamp()))
        conn.commit()
        return cur.lastrowid

def upsert_file_versions(filepath: str, fileid: int, stage: str):
    """
    Inserts file version if not present in database
    Otherwise, update the timestamp
    stage takes in string "readin", "processed", "decomposed", "edited"

    returns versionid
    """
    stageid = get_stageid()

    with get_connection() as conn:
        curr = conn.execute("""
            INSERT INTO file_versions (fileid, stageid, filepath, last_opened)
            VALUES (?, ?, ?, ?)                
            ON CONFLICT(filepath) DO UPDATE SET
            last_opened = excluded.last_opened
            """, (fileid, stageid, filepath, get_timestamp()))
        conn.commit()
        return curr.lastrowid

def get_recent_files(stage: str):
    """
    Get the recent files last opened by user
    Only displays files from the specified stage/window
    
    It will prioritise recent files from current session 
    then show files from other sessions. 
    
    Current session is assumed to the latest one.

    Returns list of filepaths (max 10)
    """
    stageid = get_stageid()

    with get_connection() as conn:
        rows = conn.execute("""
            SELECT fv.filepath, fv.last_opened, f.sessionid
            FROM files_versions fv
            JOIN files f on fv.fileid = f.fileid
            WHERE fv.stageid = ?
            ORDER BY f.sessionid DESC, fv.last_opened DESC
            LIMIT ?
        """, (stageid, RECENT_FILES_MAX,))
        return [dict(row) for row in rows]


def get_table_testing():
    with get_connection() as conn:
        rows = conn.execute("""
            SELECT sessionid, created_at 
            FROM sessions             
        """)
    return [dict(row) for row in rows]

def get_timestamp() -> int:
    """
    Returns the current time as an int
    """
    return int(datetime.now().timestamp())

def get_stageid(stage: str) -> id:
    """
    Return stageid for given stage name
    Raises exception if stage name is invalid.
    Valid stage names: readin, processed, decomposed, edited
    """
    try:
        return STAGES[stage]
    except Exception as e:
        print(f"Invalid stage '{e}': must be one of {STAGES}")


# init_db()
# # update_files('/Users/bboy221/capstone-project-25t3-3900-w14b-banana/data/trial1_20MVC.otb+')

# upsert_file_versions("hi", 2, "decomposed")

# p = create_new_session()
# print(p)
# print(get_table_testing())

