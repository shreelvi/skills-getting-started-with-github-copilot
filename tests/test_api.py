import copy

import pytest
from fastapi.testclient import TestClient

from src.app import app, activities as activities_db


client = TestClient(app)

# Keep an immutable copy of initial activities so tests can restore state between runs
initial_activities = copy.deepcopy(activities_db)


@pytest.fixture(autouse=True)
def restore_activities():
    # Reset the in-memory activities dict before each test
    activities_db.clear()
    activities_db.update(copy.deepcopy(initial_activities))
    yield
    activities_db.clear()
    activities_db.update(copy.deepcopy(initial_activities))


def test_get_activities():
    resp = client.get("/activities")
    assert resp.status_code == 200
    data = resp.json()
    assert "Chess Club" in data
    assert isinstance(data["Chess Club"]["participants"], list)


def test_signup_success():
    email = "test_student@mergington.edu"
    # Sign up for an activity that has capacity
    resp = client.post(f"/activities/Swimming%20Club/signup?email={email}")
    assert resp.status_code == 200
    body = resp.json()
    assert "Signed up" in body["message"]

    # Verify participants list updated
    resp2 = client.get("/activities")
    assert email in resp2.json()["Swimming Club"]["participants"]


def test_signup_duplicate():
    email = "duplicate@mergington.edu"
    # First signup should succeed
    r1 = client.post(f"/activities/Science%20Olympiad/signup?email={email}")
    assert r1.status_code == 200

    # Second signup should fail with 400
    r2 = client.post(f"/activities/Science%20Olympiad/signup?email={email}")
    assert r2.status_code == 400


def test_signup_not_found():
    r = client.post("/activities/ThisActivityDoesNotExist/signup?email=abc@x.com")
    assert r.status_code == 404


def test_signup_full():
    # Create a tiny activity that's already full
    activities_db["Tiny Club"] = {
        "description": "Tiny",
        "schedule": "Now",
        "max_participants": 1,
        "participants": ["one@mergington.edu"],
    }

    r = client.post("/activities/Tiny%20Club/signup?email=new@x.com")
    assert r.status_code == 400
