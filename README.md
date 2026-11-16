# Capstone Hub

[![CI](https://github.com/prxneel007/SE-Capstone-Portal/actions/workflows/ci.yml/badge.svg)](https://github.com/prxneel007/SE-Capstone-Portal/actions/workflows/ci.yml)

**Integrated Capstone Idea Bank, Project Management, Tracking and Reporting Platform**
SE Mini Project (Topic #21), PES University

Students browse capstone ideas, form teams, track milestones, submit reports and receive faculty feedback, with idea voting, plagiarism checks and automated progress reminders.

| Team member | SRN | GitHub |
|---|---|---|
| Chirra Yuktha Praneel (repo owner) | PES2UG24AM049 | @prxneel007 |
| Dhruv Uppalapati | PES2UG24AM054 | @dhruv5112 |
| Dhriti L Krishna | PES2UG24AM052 | @dlk27106 |
| Meghana | PES2UG24AM075 | @Meghana-Konduru |

## Features
| Area | What you can do |
|---|---|
| Accounts | Register as student or faculty (faculty need a sign-up code), log in, role-based menus |
| Idea bank | Propose, edit and delete ideas; search, filter by domain, sort by votes; upvote ideas |
| Teams | Create a team, join with an invite code (max 4), claim an idea, get a faculty mentor |
| Milestones | Mentors set dated milestones; teams update status; progress bars and overdue flags |
| Reports | Upload versioned PDF/TXT/MD reports per milestone; download with access checks |
| Plagiarism | Every report compared with other teams' reports (5-word shingles, Jaccard); ≥ 40% is flagged |
| Feedback | Faculty comments and A-F grades on each report |
| Reminders | Daily automatic due-soon and overdue reminders, notification inbox with unread badge |
| Reporting | Progress report of all teams with CSV export |

## Quick start
```bash
python -m venv .venv
source .venv/bin/activate            # Windows: .venv\Scripts\activate
pip install -r requirements.txt
flask --app capstone seed-demo       # creates the database with demo data
flask --app capstone run             # open http://127.0.0.1:5000
```

Demo accounts (password `password123`):

| Role | E-mail |
|---|---|
| Admin | admin@demo.edu |
| Faculty (mentor of Team Nimbus) | faculty@demo.edu |
| Student (Team Nimbus) | praneel@demo.edu, dhruv@demo.edu, dhriti@demo.edu, meghana@demo.edu |
| Student (no team yet) | rahul@demo.edu |

Faculty sign-up code for new faculty accounts: `faculty-2026` (override with the `FACULTY_SIGNUP_CODE` environment variable).

Other commands:
```bash
flask --app capstone init-db         # empty database
flask --app capstone send-reminders  # run the reminder job now (for cron)
```

## Running the tests
```bash
pip install -r requirements-dev.txt
python -m pytest --cov               # 88 tests, 99% branch coverage
flake8 capstone tests
```
GitHub Actions runs lint, the test suite on Python 3.10-3.12 with an 80% coverage gate, and PR automation (labels, assignee, linked-issue and commit-message checks) on every push and pull request.

## Documents
- [Software Requirements Specification](docs/SRS.md)
- [Software Architecture Document](docs/Software_Architecture_Document.md)
- [Software Design Document](docs/Design_Document.md)
- [Test Plan](docs/Test_Plan.md)
- [Product Backlog and Sprint Plan](docs/Product_Backlog.md)

## Project structure
```
capstone/            Flask app: one module per feature (see Design Document §2)
  templates/         Jinja2 pages and partials
  static/style.css   responsive styles
  schema.sql         database schema
tests/               pytest suite (one file per feature)
docs/                SRS, architecture, design, test plan, backlog, diagrams
.github/workflows/   CI and PR automation
```
