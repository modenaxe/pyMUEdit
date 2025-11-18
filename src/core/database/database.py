import re
import sqlite3
from pathlib import Path
from datetime import datetime
import json
from core.logger import logger

PATH_TO_SCHEMA = Path("./core/database/schema.sql")
PATH_TO_DATABASE = Path("./core/database/database.db")
RECENT_FILES_MAX = 10
STAGES = {}

# =================================
# Database Setup/Utility functions
# =================================

def init_db():
    """
    On app start up, initialise the database
    Create database.db if not present
    """
    try:
        with sqlite3.connect(PATH_TO_DATABASE) as connection:
            logger.debug(f"Set up SQLite database successfully")

            cursor = connection.cursor()
            schema = PATH_TO_SCHEMA.read_text()
            cursor.executescript(schema)
            connection.commit()

            load_stage_map()
    except (sqlite3.OperationalError) as e:
        logger.exception("Failed to initialise database:")
        return None

def get_connection():
    """
    Starts connection to the database

    Returns a dictionary cursor
    """
    conn = sqlite3.connect(PATH_TO_DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def load_stage_map():
    """
    Loads the stages into the global stage constant
    The mapping to the name and the stage id
    """
    global STAGES
    with get_connection() as conn:
        rows = conn.execute("SELECT stageid, name FROM stages")
        STAGES = {row["name"]: row["stageid"] for row in rows}

# ========================
# Session Helper functions
# ========================

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

def get_session_files(sessionid: int):
    """
    Get all files, version filepaths and logs for session.
    Returns a list of objects for each file and file_version
    respectively
    """
    with get_connection() as conn:
        rows = conn.execute("""
            SELECT
                f.fileid,
                f.filename,
                f.filepath AS original_filepath,
                fv.versionid,
                st.name AS stage,
                fv.filepath AS version_filepath,
                fv.last_opened,
                l.logid,
                l.actions,
                l.config
            FROM files f
            JOIN file_versions fv ON fv.fileid = f.fileid
            JOIN stages st ON st.stageid = fv.stageid
            LEFT JOIN logs l ON l.versionid = fv.versionid
            WHERE f.sessionid = ?
            ORDER BY f.fileid, fv.stageid
        """, (sessionid,))
        rows = [dict(row) for row in rows]

    # Group by file version
    grouped = {}
    for row in rows:
        fid = row["fileid"]
        if fid not in grouped:
            grouped[fid] = {
                "fileid": fid,
                "filename": row["filename"],
                "original_filepath": row["original_filepath"],
                "versions": []
            }

        grouped[fid]["versions"].append({
            "versionid": row["versionid"],
            "stage": row["stage"],
            "version_filepath": row["version_filepath"],
            "last_opened": row["last_opened"],
            "log": {
                "logid": row["logid"],
                "actions": row["actions"],
                "config": row["config"],
            } if row["logid"] else None
        })

    return list(grouped.values())

# =======================
# Files Helper functions
# =======================

def insert_files(filepath: str, filename: str, sessionid: int):
    """
    Insert original, raw files into database.
    note: we will handle files under file_versions

    Returns fileid
    """
    with get_connection() as conn:
        cur = conn.execute("""
            INSERT INTO files (filepath, filename, sessionid, created_at)
            VALUES (?, ?, ?, ?)
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
    stageid = get_stageid(stage)

    with get_connection() as conn:
        curr = conn.execute("""
            INSERT INTO file_versions (fileid, stageid, filepath, last_opened)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(filepath) DO UPDATE SET
            last_opened = excluded.last_opened
            """, (fileid, stageid, filepath, get_timestamp()))
        conn.commit()
        return curr.lastrowid


def get_recent_files():
    """
    Get the recent files last opened by user

    Returns list of file objects(max 10)
    """
    with get_connection() as conn:
        rows = conn.execute("""
            SELECT fv.filepath, fv.last_opened, f.sessionid, fv.stageid
            FROM file_versions fv
            JOIN files f ON fv.fileid = f.fileid
            ORDER BY fv.last_opened DESC
            LIMIT ?
        """, (RECENT_FILES_MAX,))
        return [dict(row) for row in rows]

# =======================
# Log helper functions
# =======================

def insert_log(versionid, actions, config) -> int:
    """
    Insert log for versionid with actions and config jsonified
    Paramater: action and config are lists
    Returns logid
    """

    actions_json = json.dumps(actions) if actions else None
    config_json = json.dumps(config) if config else None

    with get_connection() as conn:
        cur = conn.execute(
            """
            INSERT INTO logs (versionid, actions, config)
            VALUES (?, ?, ?)
            """,
            (versionid, actions_json, config_json),
        )
        conn.commit()
        return cur.lastrowid


def get_log_for_version(versionid: int):
    """
    Get all log for specified file version
    Return lists of logid, actions and config
    """
    with get_connection() as conn:
        cur = conn.execute(
            """
            SELECT logid, versionid, actions, config
            FROM logs
            WHERE versionid = ?
            ORDER BY logid
            """,
            (versionid,),
        )

        rows = cur.fetchall()
        results = []

        for row in rows:
            results.append(
                {
                    "logid": row["logid"],
                    "versionid": row["versionid"],
                    "actions": json.loads(row["actions"]) if row["actions"] else None,
                    "config": json.loads(row["config"]) if row["config"] else None,
                }
            )
        return results

# =======================
# Utility functions
# =======================

def get_timestamp() -> int:
    """
    Returns the current time as an int
    """
    return int(datetime.now().timestamp())

def get_stageid(stage: str) -> id:
    """
    Return stageid for given stage name
    Raises exception if stage name is invalid.
    Valid stage names: readin, segmented, decomposed, edited, processed
    """
    try:
        return STAGES[stage]
    except Exception as e:
        logger.exception(f"Invalid stage '{e}': must be one of {STAGES}")

def get_fileid_by_path(filepath: str):
    """Return fileid if the file already exists in the database, else None"""
    from core.database.database import get_connection
    with get_connection() as conn:
        row = conn.execute("SELECT fileid FROM files WHERE filepath = ?", (filepath,)).fetchone()
        return row["fileid"] if row else None

def get_or_create_session_for_file(filepath: str) -> int:
    """
    Get existing session for a file, or create a new one if it doesn't exist.
    Returns sessionid.
    """
    with get_connection() as conn:
        row = conn.execute("""
            SELECT sessionid FROM files WHERE filepath = ?
        """, (filepath,)).fetchone()

        if row:
            return row["sessionid"]
        else:
            cur = conn.execute("""
                INSERT INTO sessions (created_at)
                VALUES (?)
            """, (get_timestamp(),))
            conn.commit()
            return cur.lastrowid