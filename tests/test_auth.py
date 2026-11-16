import pytest

from capstone.auth import validate_registration


def test_register_and_login(client, query):
    r = client.post("/auth/register", data={"name": "New Student", "email": "New@Test.edu",
                                            "password": "longpassword", "role": "student", "srn": "pes1"})
    assert r.headers["Location"].endswith("/auth/login")
    row = query("SELECT * FROM users WHERE email = 'new@test.edu'")[0]
    assert row["role"] == "student" and row["srn"] == "PES1"
    assert row["password_hash"] != "longpassword"  # NFR-01: never stored in plain text
    r = client.post("/auth/login", data={"email": "new@test.edu", "password": "longpassword"})
    assert r.headers["Location"].endswith("/dashboard")


def test_duplicate_email_rejected(client):
    r = client.post("/auth/register", data={"name": "X", "email": "s1@test.edu",
                                            "password": "longpassword", "role": "student"},
                    follow_redirects=True)
    assert b"already exists" in r.data


@pytest.mark.parametrize("form, message", [
    ({"name": "", "email": "a@b.co", "password": "longpassword"}, "Name is required."),
    ({"name": "A", "email": "not-an-email", "password": "longpassword"}, "Enter a valid email address."),
    ({"name": "A", "email": "a@b.co", "password": "short"}, "Password must be at least 8 characters."),
    ({"name": "A", "email": "a@b.co", "password": "longpassword", "role": "admin"}, "Choose a valid role."),
    ({"name": "A", "email": "a@b.co", "password": "longpassword", "role": "faculty",
      "faculty_code": "wrong"}, "Invalid faculty sign-up code."),
])
def test_validate_registration(form, message):
    assert message in validate_registration(form, "secret")


def test_faculty_needs_code(client, app, query):
    data = {"name": "Prof", "email": "prof@test.edu", "password": "longpassword", "role": "faculty",
            "faculty_code": app.config["FACULTY_SIGNUP_CODE"]}
    client.post("/auth/register", data=data)
    assert query("SELECT role FROM users WHERE email = 'prof@test.edu'")[0]["role"] == "faculty"


def test_bad_login(client):
    r = client.post("/auth/login", data={"email": "s1@test.edu", "password": "nope"})
    assert b"Incorrect email or password" in r.data


def test_login_next_is_safe(client):
    r = client.post("/auth/login?next=//evil.com", data={"email": "s1@test.edu", "password": "password123"})
    assert r.headers["Location"].endswith("/dashboard")
    client.post("/auth/logout")
    r = client.post("/auth/login?next=/ideas/", data={"email": "s1@test.edu", "password": "password123"})
    assert r.headers["Location"].endswith("/ideas/")


def test_dashboard_requires_login(client):
    r = client.get("/dashboard")
    assert "/auth/login" in r.headers["Location"]


def test_logout(client, login):
    login("s1")
    assert client.get("/dashboard").status_code == 200
    client.post("/auth/logout")
    assert client.get("/dashboard").status_code == 302


def test_home_redirects_logged_in_user(client, login):
    login("s1")
    assert client.get("/").headers["Location"].endswith("/dashboard")


def test_csrf_enforced(app, tmp_path):
    app.config["CSRF_DISABLED"] = False
    client = app.test_client()
    assert client.post("/auth/login", data={"email": "s1@test.edu", "password": "password123"}).status_code == 400
    client.get("/auth/login")  # renders a form, which issues the token
    with client.session_transaction() as sess:
        token = sess["csrf_token"]
    r = client.post("/auth/login", data={"email": "s1@test.edu", "password": "password123",
                                         "csrf_token": token})
    assert r.status_code == 302
