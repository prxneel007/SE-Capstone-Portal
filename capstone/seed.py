"""`flask --app capstone seed-demo`: reset the database and load demo data for the sprint videos."""
from datetime import timedelta

import click
from flask.cli import with_appcontext
from werkzeug.security import generate_password_hash

from .db import get_db, init_db, today

DEMO_PASSWORD = "password123"

USERS = [
    ("Admin User", "admin@demo.edu", "", "admin"),
    ("Dr. Asha Rao", "faculty@demo.edu", "FAC001", "faculty"),
    ("Prof. Vikram Iyer", "faculty2@demo.edu", "FAC002", "faculty"),
    ("Chirra Yuktha Praneel", "praneel@demo.edu", "PES2UG24AM049", "student"),
    ("Dhruv Uppalapati", "dhruv@demo.edu", "PES2UG24AM054", "student"),
    ("Dhriti L Krishna", "dhriti@demo.edu", "PES2UG24AM052", "student"),
    ("Meghana", "meghana@demo.edu", "PES2UG24AM075", "student"),
    ("Rahul Sharma", "rahul@demo.edu", "PES2UG24AM101", "student"),
]

IDEAS = [
    ("Smart Campus Parking Finder",
     "IoT sensors and a mobile app that show free parking slots across campus in real time.",
     "IoT", "iot, mobile, sensors", 1),
    ("AI Resume Screener for Placements",
     "An NLP pipeline that ranks student resumes against job descriptions and explains the ranking.",
     "AI/ML", "nlp, placements, explainability", 1),
    ("Peer Tutoring Marketplace",
     "A web platform that matches students who need help with seniors who tutor, with ratings and scheduling.",
     "Web", "flask, matching, scheduling", 3),
    ("Phishing Email Detector Extension",
     "A browser extension that flags likely phishing emails using a lightweight on-device classifier.",
     "Security", "security, browser, ml", 2),
    ("Canteen Demand Forecasting",
     "Predict daily canteen demand from timetable and weather data to cut food waste.",
     "Data Science", "forecasting, sustainability", 4),
]


@click.command("seed-demo")
@with_appcontext
def seed_demo_command():
    """Reset the database and load demo users, ideas, a team, milestones and votes."""
    init_db()
    db = get_db()
    ids = {}
    for name, email, srn, role in USERS:
        cur = db.execute("INSERT INTO users (name, email, srn, password_hash, role) VALUES (?, ?, ?, ?, ?)",
                         (name, email, srn, generate_password_hash(DEMO_PASSWORD), role))
        ids[email] = cur.lastrowid
    idea_ids = []
    for title, desc, domain, tags, author_idx in IDEAS:
        cur = db.execute("INSERT INTO ideas (title, description, domain, tags, author_id) VALUES (?, ?, ?, ?, ?)",
                         (title, desc, domain, tags, ids[USERS[author_idx][1]]))
        idea_ids.append(cur.lastrowid)
    for voter in ("praneel@demo.edu", "dhruv@demo.edu", "dhriti@demo.edu", "rahul@demo.edu"):
        db.execute("INSERT INTO votes (user_id, idea_id) VALUES (?, ?)", (ids[voter], idea_ids[1]))
    db.execute("INSERT INTO votes (user_id, idea_id) VALUES (?, ?)", (ids["meghana@demo.edu"], idea_ids[0]))
    cur = db.execute("INSERT INTO teams (name, invite_code, idea_id, mentor_id, created_by) VALUES (?, ?, ?, ?, ?)",
                     ("Team Nimbus", "NIMBUS01", idea_ids[1], ids["faculty@demo.edu"], ids["praneel@demo.edu"]))
    team_id = cur.lastrowid
    for email in ("praneel@demo.edu", "dhruv@demo.edu", "dhriti@demo.edu", "meghana@demo.edu"):
        db.execute("INSERT INTO team_members (team_id, user_id) VALUES (?, ?)", (team_id, ids[email]))
    t0 = today()
    for title, offset, status in [("Project proposal", -10, "done"), ("SRS & design review", -2, "in_progress"),
                                  ("Prototype demo", 2, "pending"), ("Final report", 20, "pending")]:
        db.execute("INSERT INTO milestones (team_id, title, due_date, status) VALUES (?, ?, ?, ?)",
                   (team_id, title, (t0 + timedelta(days=offset)).isoformat(), status))
    db.commit()
    click.echo(f"Demo data loaded. All demo accounts use the password '{DEMO_PASSWORD}':")
    for name, email, _, role in USERS:
        click.echo(f"  {role:8} {email:22} {name}")


def init_module(app):
    app.cli.add_command(seed_demo_command)
