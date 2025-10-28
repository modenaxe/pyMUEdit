/*
    Database schema for pyMUEdit
    Stores sessions and in each session holds the
    file version at their respective stage.
*/


-- Stages: Static reference table
-- Readin -> Processed -> Decomposition -> Edit 
CREATE TABLE IF NOT EXISTS stages (
    stageid INTEGER PRIMARY KEY,
    name TEXT 
);

-- Sessions: A group of file versions in one workflow
CREATE TABLE IF NOT EXISTS sessions (
    sessionid INTEGER UNIQUE PRIMARY KEY AUTOINCREMENT,
    created_at INTEGER
);

-- Files: Import data file
CREATE TABLE IF NOT EXISTS files (
    fileid INTEGER PRIMARY KEY AUTOINCREMENT,
    sessionid INTEGER NOT NULL,
    filename TEXT,
    filepath TEXT UNIQUE NOT NULL,
    created_at INTEGER,

    FOREIGN KEY (sessionid) references sessions(sessionid)
);

-- Versions: A file through its various stages
CREATE TABLE IF NOT EXISTS file_versions (
    versionid INTEGER PRIMARY KEY AUTOINCREMENT,
    fileid INTEGER NOT NULL,
    stageid INTEGER NOT NULL,
    filepath TEXT UNIQUE NOT NULL,
    last_opened INTEGER,
    
    FOREIGN KEY (stageid) REFERENCES stages(stageid),
    FOREIGN KEY (fileid) REFERENCES files(fileid)
);

CREATE TABLE IF NOT EXISTS logs (
    logid INTEGER PRIMARY KEY AUTOINCREMENT, 
    versionid INTEGER NOT NULL,
    actions TEXT,    -- JSON blob of user changes to file
    config TEXT,    -- JSON blob of file parameters/config

    FOREIGN KEY (versionid) REFERENCES file_versions(versionid)
);

-- Inserts stage values once 
INSERT OR IGNORE INTO stages (stageid, name)
VALUES 
    (1, 'readin'),
    (2, 'processed'),
    (3, 'decomposed'),
    (4, 'edited');