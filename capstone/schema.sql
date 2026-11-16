-- Capstone Hub schema (see docs/Design_Document.md, section 4)
DROP TABLE IF EXISTS meta;
DROP TABLE IF EXISTS notifications;
DROP TABLE IF EXISTS feedback;
DROP TABLE IF EXISTS submissions;
DROP TABLE IF EXISTS milestones;
DROP TABLE IF EXISTS team_members;
DROP TABLE IF EXISTS teams;
DROP TABLE IF EXISTS votes;
DROP TABLE IF EXISTS ideas;
DROP TABLE IF EXISTS users;

CREATE TABLE users (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL,
  email TEXT UNIQUE NOT NULL,
  srn TEXT NOT NULL DEFAULT '',
  password_hash TEXT NOT NULL,
  role TEXT NOT NULL CHECK (role IN ('student', 'faculty', 'admin')),
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE ideas (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  title TEXT NOT NULL,
  description TEXT NOT NULL,
  domain TEXT NOT NULL,
  tags TEXT NOT NULL DEFAULT '',
  author_id INTEGER NOT NULL REFERENCES users (id),
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE votes (
  user_id INTEGER NOT NULL REFERENCES users (id),
  idea_id INTEGER NOT NULL REFERENCES ideas (id) ON DELETE CASCADE,
  PRIMARY KEY (user_id, idea_id)
);

CREATE TABLE teams (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT UNIQUE NOT NULL,
  invite_code TEXT UNIQUE NOT NULL,
  idea_id INTEGER UNIQUE REFERENCES ideas (id),
  mentor_id INTEGER REFERENCES users (id),
  created_by INTEGER NOT NULL REFERENCES users (id),
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE team_members (
  team_id INTEGER NOT NULL REFERENCES teams (id) ON DELETE CASCADE,
  user_id INTEGER NOT NULL UNIQUE REFERENCES users (id),
  joined_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (team_id, user_id)
);

CREATE TABLE milestones (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  team_id INTEGER NOT NULL REFERENCES teams (id) ON DELETE CASCADE,
  title TEXT NOT NULL,
  description TEXT NOT NULL DEFAULT '',
  due_date TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'in_progress', 'done')),
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE submissions (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  team_id INTEGER NOT NULL REFERENCES teams (id) ON DELETE CASCADE,
  milestone_id INTEGER REFERENCES milestones (id) ON DELETE SET NULL,
  filename TEXT NOT NULL,
  stored_name TEXT NOT NULL,
  text_content TEXT NOT NULL DEFAULT '',
  similarity REAL NOT NULL DEFAULT 0,
  similar_to INTEGER REFERENCES submissions (id) ON DELETE SET NULL,
  version INTEGER NOT NULL,
  submitted_by INTEGER NOT NULL REFERENCES users (id),
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE feedback (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  submission_id INTEGER NOT NULL REFERENCES submissions (id) ON DELETE CASCADE,
  faculty_id INTEGER NOT NULL REFERENCES users (id),
  comment TEXT NOT NULL,
  grade TEXT NOT NULL DEFAULT '',
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE notifications (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL REFERENCES users (id),
  message TEXT NOT NULL,
  link TEXT NOT NULL DEFAULT '',
  is_read INTEGER NOT NULL DEFAULT 0,
  dedupe_key TEXT UNIQUE,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE meta (
  key TEXT PRIMARY KEY,
  value TEXT NOT NULL
);

-- NFR-02: indexes for the hot list/filter queries
CREATE INDEX idx_ideas_domain ON ideas (domain);
CREATE INDEX idx_votes_idea ON votes (idea_id);
CREATE INDEX idx_milestones_team ON milestones (team_id);
CREATE INDEX idx_submissions_team ON submissions (team_id);
CREATE INDEX idx_notifications_user ON notifications (user_id, is_read);
