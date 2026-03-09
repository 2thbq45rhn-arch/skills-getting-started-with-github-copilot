import copy
import pytest
from starlette.testclient import TestClient

import src.app as app_module
from src.app import app

# Snapshot taken once at import time, before any test mutates state
ORIGINAL_ACTIVITIES = copy.deepcopy(app_module.activities)


@pytest.fixture(autouse=True)
def reset_activities():
    """Restore the in-memory activities dict to its original state before each test."""
    # Mutate in-place so endpoints' existing references stay valid
    app_module.activities.clear()
    app_module.activities.update(copy.deepcopy(ORIGINAL_ACTIVITIES))
    yield


@pytest.fixture
def client():
    return TestClient(app)


# ---------------------------------------------------------------------------
# GET /activities
# ---------------------------------------------------------------------------

def test_get_activities_returns_200(client):
    # Act
    response = client.get("/activities")
    # Assert
    assert response.status_code == 200


def test_get_activities_returns_all_nine(client):
    # Act
    response = client.get("/activities")
    # Assert
    assert len(response.json()) == 9


def test_get_activities_structure(client):
    # Act
    response = client.get("/activities")
    # Assert
    for activity in response.json().values():
        assert "description" in activity
        assert "schedule" in activity
        assert "max_participants" in activity
        assert "participants" in activity


def test_get_activities_seeded_participants(client):
    # Act
    response = client.get("/activities")
    # Assert
    assert "michael@mergington.edu" in response.json()["Chess Club"]["participants"]


# ---------------------------------------------------------------------------
# POST /activities/{activity_name}/signup
# ---------------------------------------------------------------------------

def test_signup_happy_path(client):
    # Act
    response = client.post("/activities/Chess Club/signup?email=new@test.edu")
    # Assert
    assert response.status_code == 200
    assert "new@test.edu" in response.json()["message"]


def test_signup_adds_participant_to_list(client):
    # Act
    client.post("/activities/Chess Club/signup?email=new@test.edu")
    activities = client.get("/activities").json()
    # Assert
    assert "new@test.edu" in activities["Chess Club"]["participants"]


def test_signup_activity_not_found_returns_404(client):
    # Act
    response = client.post("/activities/Nonexistent Activity/signup?email=x@test.edu")
    # Assert
    assert response.status_code == 404


def test_signup_activity_not_found_detail(client):
    # Act
    response = client.post("/activities/Nonexistent Activity/signup?email=x@test.edu")
    # Assert
    assert response.json()["detail"] == "Activity not found"


def test_signup_already_signed_up_returns_400(client):
    # Arrange
    client.post("/activities/Chess Club/signup?email=dup@test.edu")
    # Act
    response = client.post("/activities/Chess Club/signup?email=dup@test.edu")
    # Assert
    assert response.status_code == 400


def test_signup_already_signed_up_detail(client):
    # Arrange
    client.post("/activities/Chess Club/signup?email=dup@test.edu")
    # Act
    response = client.post("/activities/Chess Club/signup?email=dup@test.edu")
    # Assert
    assert response.json()["detail"] == "Student is already signed up for this activity"


def test_signup_at_capacity_returns_400(client):
    # Arrange — Chess Club: max 12, starts with 2; fill remaining 10 slots
    for i in range(10):
        client.post(f"/activities/Chess Club/signup?email=fill{i}@test.edu")
    # Act
    response = client.post("/activities/Chess Club/signup?email=overflow@test.edu")
    # Assert
    assert response.status_code == 400


def test_signup_at_capacity_detail(client):
    # Arrange
    for i in range(10):
        client.post(f"/activities/Chess Club/signup?email=fill{i}@test.edu")
    # Act
    response = client.post("/activities/Chess Club/signup?email=overflow@test.edu")
    # Assert
    assert response.json()["detail"] == "Activity is full"


# ---------------------------------------------------------------------------
# DELETE /activities/{activity_name}/signup
# ---------------------------------------------------------------------------

def test_unregister_happy_path(client):
    # Act
    response = client.delete("/activities/Chess Club/signup?email=michael@mergington.edu")
    # Assert
    assert response.status_code == 200
    assert "michael@mergington.edu" in response.json()["message"]


def test_unregister_removes_participant_from_list(client):
    # Act
    client.delete("/activities/Chess Club/signup?email=michael@mergington.edu")
    activities = client.get("/activities").json()
    # Assert
    assert "michael@mergington.edu" not in activities["Chess Club"]["participants"]


def test_unregister_activity_not_found_returns_404(client):
    # Act
    response = client.delete("/activities/Nonexistent Activity/signup?email=x@test.edu")
    # Assert
    assert response.status_code == 404


def test_unregister_activity_not_found_detail(client):
    # Act
    response = client.delete("/activities/Nonexistent Activity/signup?email=x@test.edu")
    # Assert
    assert response.json()["detail"] == "Activity not found"


def test_unregister_student_not_signed_up_returns_404(client):
    # Act
    response = client.delete("/activities/Chess Club/signup?email=ghost@test.edu")
    # Assert
    assert response.status_code == 404


def test_unregister_student_not_signed_up_detail(client):
    # Act
    response = client.delete("/activities/Chess Club/signup?email=ghost@test.edu")
    # Assert
    assert response.json()["detail"] == "Student is not signed up for this activity"
