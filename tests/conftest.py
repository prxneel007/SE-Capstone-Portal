import pytest
from werkzeug.security import generate_password_hash

from capstone import create_app
from capstone.db import get_db, init_db

PASSWORD = "password123"
USERS = {
    "s1": ("Student One", "s1@test.edu", "student"),
    "s2": ("Student Two", "s2@test.edu", "student"),
    "s3": ("Student Three", "s3@test.edu", "student"),
    "s4": ("Student Four", "s4@test.edu", "student"),
    "s5": ("Student Five", "s5@test.edu", "student"),
    "f1": ("Faculty One", "f1@test.edu", "faculty"),
    "f2": ("Faculty Two", "f2@test.edu", "faculty"),
    "admin": ("Admin", "admin@test.edu", "admin"),
}


@pytest.fixture
def app(tmp_path):
    app = create_app({
        "TESTING": True,
        "SECRET_KEY": "test",
        "DATABASE": str(tmp_path / "test.sqlite"),
        "UPLOAD_FOLDER": str(tmp_path / "uploads"),
        "CSRF_DISABLED": True,
        "FAKE_TODAY": "2026-10-20",
    })
    with app.app_context():
        init_db()
        db = get_db()
        pw = generate_password_hash(PASSWORD)
        for name, email, role in USERS.values():
            db.execute("INSERT INTO users (name, email, password_hash, role) VALUES (?, ?, ?, ?)",
                       (name, email, pw, role))
        db.commit()
    return app


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def uid(app):
    """uid('s1') -> database id of that test user."""
    def lookup(key):
        with app.app_context():
            return get_db().execute("SELECT id FROM users WHERE email = ?", (USERS[key][1],)).fetchone()[0]
    return lookup


@pytest.fixture
def login(client):
    def do_login(key):
        client.post("/auth/logout")
        return client.post("/auth/login", data={"email": USERS[key][1], "password": PASSWORD})
    return do_login


@pytest.fixture
def query(app):
    """Run a SQL statement against the test database and return all rows."""
    def run(sql, params=()):
        with app.app_context():
            db = get_db()
            rows = db.execute(sql, params).fetchall()
            db.commit()
            return rows
    return run
