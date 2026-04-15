"""
Tests for the Mergington High School API using pytest and FastAPI TestClient.
"""

from copy import deepcopy
from urllib.parse import quote

import pytest
from fastapi.testclient import TestClient
from src.app import app, activities

INITIAL_ACTIVITIES = deepcopy(activities)
client = TestClient(app)


def activity_path(activity_name: str, endpoint: str) -> str:
    return f"/activities/{quote(activity_name, safe='')}/{endpoint}"


@pytest.fixture(autouse=True)
def reset_activities():
    """Reset the in-memory activities state before each test."""
    activities.clear()
    activities.update(deepcopy(INITIAL_ACTIVITIES))
    yield
    activities.clear()
    activities.update(deepcopy(INITIAL_ACTIVITIES))


def test_get_activities_returns_all_activities():
    # Arrange
    expected_activity = "Chess Club"

    # Act
    response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, dict)
    assert expected_activity in data
    assert "Programming Class" in data
    assert len(data) == len(INITIAL_ACTIVITIES)


def test_signup_adds_participant():
    # Arrange
    activity_name = "Soccer Team"
    email = "test@example.com"
    signup_url = activity_path(activity_name, "signup")

    # Act
    response = client.post(signup_url, params={"email": email})

    # Assert
    assert response.status_code == 200
    assert "Signed up" in response.json()["message"]
    assert email in activities[activity_name]["participants"]


def test_signup_duplicate_returns_400():
    # Arrange
    activity_name = "Chess Club"
    email = "duplicate@example.com"
    signup_url = activity_path(activity_name, "signup")

    # Act
    first_response = client.post(signup_url, params={"email": email})
    second_response = client.post(signup_url, params={"email": email})

    # Assert
    assert first_response.status_code == 200
    assert second_response.status_code == 400
    assert second_response.json()["detail"] == "Student already signed up for this activity"


def test_signup_invalid_activity_returns_404():
    # Arrange
    signup_url = activity_path("Nonexistent Club", "signup")

    # Act
    response = client.post(signup_url, params={"email": "test@example.com"})

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_remove_participant_removes_entry():
    # Arrange
    activity_name = "Basketball Team"
    email = "remove_test@example.com"
    signup_url = activity_path(activity_name, "signup")
    remove_url = activity_path(activity_name, "participants")
    client.post(signup_url, params={"email": email})

    # Act
    response = client.delete(remove_url, params={"email": email})

    # Assert
    assert response.status_code == 200
    assert email not in activities[activity_name]["participants"]
    assert "Removed" in response.json()["message"]


def test_remove_nonexistent_participant_returns_404():
    # Arrange
    activity_name = "Drama Club"
    email = "notregistered@example.com"
    remove_url = activity_path(activity_name, "participants")

    # Act
    response = client.delete(remove_url, params={"email": email})

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Participant not found"
