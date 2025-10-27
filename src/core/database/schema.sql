/*
    Database schema for pyMUEdit
    Stores sessions and in each session holds the
    file version at their respective stage.
*/


-- Stages: Static reference table
-- Readin -> Processed -> Decomposition -> Edit 
CREATE TABLE IF NOT EXISTS stages (
    stageid INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT
);

-- Files: Import data file
CREATE TABLE IF NOT EXISTS files (
    fileid INTEGER PRIMARY KEY AUTOINCREMENT,
    filename TEXT,
    filepath TEXT UNIQUE NOT NULL,
    last_opened INTEGER
);

-- Sessions: A group of file versions in one workflow
CREATE TABLE IF NOT EXISTS sessions (
    sessionid INTEGER UNIQUE PRIMARY KEY AUTOINCREMENT,
    created_at INTEGER
);

-- Versions: A file through its various stages
CREATE TABLE IF NOT EXISTS versions (
    versionid INTEGER PRIMARY KEY AUTOINCREMENT,
    stageid INTEGER NOT NULL,
    fileid INTEGER NOT NULL,
    sessionid INTEGER NOT NULL,
    log TEXT,    -- JSON blob: logs file changes

    FOREIGN KEY (stageid) REFERENCES stages(stageid),
    FOREIGN KEY (fileid) REFERENCES files(fileid),
    FOREIGN KEY (sessionid) REFERENCES sessions(sessionid)
);

-- Inserts stage values once 
INSERT OR IGNORE INTO stages (name)
VALUES 
    ('readin'),
    ('processed'),
    ('decomposed'),
    ('edited');