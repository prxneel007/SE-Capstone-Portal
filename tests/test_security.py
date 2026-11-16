"""Unit tests for the security core and event bus, using throwaway routes."""
import pytest
from flask import Blueprint, session

from capstone.events import emit, subscribe
from capstone.security import login_required, role_required, safe_next


@pytest.fixture
def guarded(app):
    if "auth" not in app.blueprints:  # login_required redirects to auth.login
        stub = Blueprint("auth", __name__)
        stub.add_url_rule("/auth/login", "login", lambda: "login page")
        app.register_blueprint(stub)

    @app.route("/_t/any")
    @login_required
    def any_user():
        return "ok"

    @app.route("/_t/staff", methods=("GET", "POST"))
    @role_required("faculty", "admin")
    def staff_only():
        return "staff"

    @app.route("/_t/as/<int:user_id>")
    def as_user(user_id):
        session["user_id"] = user_id
        return "set"

    return app.test_client()


def test_login_required_redirects(guarded):
    r = guarded.get("/_t/any")
    assert r.status_code == 302
    assert "next=/_t/any" in r.headers["Location"]


def test_role_required(guarded, uid):
    guarded.get(f"/_t/as/{uid('s1')}")
    assert guarded.get("/_t/any").data == b"ok"
    assert guarded.get("/_t/staff").status_code == 403
    guarded.get(f"/_t/as/{uid('f1')}")
    assert guarded.get("/_t/staff").data == b"staff"


def test_csrf_blocks_post_without_token(app, guarded, uid):
    app.config["CSRF_DISABLED"] = False
    guarded.get(f"/_t/as/{uid('admin')}")
    assert guarded.post("/_t/staff").status_code == 400
    with guarded.session_transaction() as sess:
        sess["csrf_token"] = "abc"
    assert guarded.post("/_t/staff", data={"csrf_token": "wrong"}).status_code == 400
    assert guarded.post("/_t/staff", data={"csrf_token": "abc"}).data == b"staff"


def test_csrf_token_issued_when_rendering(client):
    client.get("/")
    with client.session_transaction() as sess:
        assert len(sess["csrf_token"]) == 32


@pytest.mark.parametrize("target, expected", [
    ("/ideas/", "/ideas/"), ("//evil.com", "/d"), ("https://evil.com", "/d"), ("", "/d"), (None, "/d"),
])
def test_safe_next(target, expected):
    assert safe_next(target, "/d") == expected


def test_event_bus(app):
    seen = []
    subscribe(app, "ping", lambda **data: seen.append(data))
    with app.app_context():
        emit("ping", x=1)
        emit("nobody-listens")
    assert seen == [{"x": 1}]
