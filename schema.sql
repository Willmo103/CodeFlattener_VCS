-- Schema for CodeFlattener VCS
-- Projects table
CREATE TABLE
    IF NOT EXISTS projects (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        path TEXT NOT NULL UNIQUE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

-- Versions table
CREATE TABLE
    IF NOT EXISTS versions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        project_id INTEGER NOT NULL,
        version_number INTEGER NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (project_id) REFERENCES projects (id),
        UNIQUE (project_id, version_number)
    );

-- Files table
CREATE TABLE
    IF NOT EXISTS files (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        version_id INTEGER NOT NULL,
        rel_path TEXT NOT NULL,
        filename TEXT NOT NULL,
        content TEXT NOT NULL,
        language TEXT,
        FOREIGN KEY (version_id) REFERENCES versions (id),
        UNIQUE (version_id, rel_path, filename)
    );
