from capstone import create_app


def test_config_defaults():
    assert not create_app().testing
    assert create_app({"TESTING": True}).testing


def test_health(client):
    assert client.get("/health").get_json() == {"status": "ok"}


def test_home_page(client):
    r = client.get("/")
    assert r.status_code == 200
    assert b"Capstone Hub" in r.data


def test_init_db_command(app):
    result = app.test_cli_runner().invoke(args=["init-db"])
    assert "Initialized" in result.output
