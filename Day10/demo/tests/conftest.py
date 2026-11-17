import pytest

from app import create_app


@pytest.fixture
def app(tmp_path):
    instance = create_app({
        "TESTING": True,
        "APP_ENV": "testing",
        "SECRET_KEY": "test-only-key-" * 5,
        "DATABASE_PATH": str(tmp_path / "board.sqlite3"),
    })
    result = instance.test_cli_runner().invoke(args=["init-db"])
    assert result.exit_code == 0, result.output
    return instance


@pytest.fixture
def client(app):
    return app.test_client()


def send(client, path, method="POST", data=None, **kwargs):
    token = client.get("/api/auth/csrf").json["csrf_token"]
    return client.open(path, method=method, json=data, headers={"X-CSRFToken": token}, **kwargs)


def signup(client, address="writer@example.test", nickname="작성자", password="TestPassword123!"):
    return send(client, "/api/auth/signup", data={"email": address, "nickname": nickname, "password": password})


def login(client, address="writer@example.test", password="TestPassword123!"):
    return send(client, "/api/auth/login", data={"email": address, "password": password})


@pytest.fixture
def writer(client):
    assert signup(client).status_code == 201
    assert login(client).status_code == 200
    return client


@pytest.fixture
def admin(app):
    result = app.test_cli_runner().invoke(args=["create-admin", "--email", "admin@example.test", "--nickname", "관리자"],
                                          input="AdminPassword123!\nAdminPassword123!\n")
    assert result.exit_code == 0, result.output
    client = app.test_client()
    assert login(client, "admin@example.test", "AdminPassword123!").status_code == 200
    return client

