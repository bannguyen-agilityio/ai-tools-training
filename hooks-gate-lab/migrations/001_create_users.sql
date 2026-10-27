-- Protected path: edits need a change ticket (see .claude/hooks/protected_paths_gate.py)
CREATE TABLE users (
  id    INTEGER PRIMARY KEY,
  email TEXT NOT NULL UNIQUE
);
