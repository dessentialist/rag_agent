import os

import pytest


@pytest.fixture(scope="session")
def test_app_client():
    """Provide a Flask test client with an in-memory SQLite DB.

    Sets DATABASE_URL before importing the app so that app initialization
    uses an isolated database for tests.
    """
    os.environ["DATABASE_URL"] = "sqlite:///:memory:"
    # Import here so the env var is applied before config is read
    from app import app as flask_app

    with flask_app.app_context():
        client = flask_app.test_client()
        yield client
