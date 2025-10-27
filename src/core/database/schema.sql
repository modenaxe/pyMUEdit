CREATE TABLE IF NOT EXISTS files (
    fileid INTEGER PRIMARY KEY AUTOINCREMENT,
    filename TEXT NOT NULL,
    filepath TEXT NOT NULL,
    config BLOB
);

CREATE TABLE IF NOT EXISTS sessions (
    sessionid INTEGER PRIMARY KEY AUTOINCREMENT,
    fileid INTEGER,
    last_opened INTEGER,
    FOREIGN KEY (fileid) REFERENCES files(fileid)
);