"""
Tests for the Mergington High School API
"""
import pytest
from fastapi.testclient import TestClient
from src.app import app, activities


@pytest.fixture
def client():
    """Create a test client for the FastAPI app"""
    return TestClient(app)


@pytest.fixture(autouse=True)
def reset_activities():
    """Reset activities data before each test"""
    activities.clear()
    activities.update({
        "Chess Club": {
            "description": "Learn strategies and compete in chess tournaments",
            "schedule": "Fridays, 3:30 PM - 5:00 PM",
            "max_participants": 12,
            "participants": ["michael@mergington.edu", "daniel@mergington.edu"]
        },
        "Programming Class": {
            "description": "Learn programming fundamentals and build software projects",
            "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
            "max_participants": 20,
            "participants": ["emma@mergington.edu", "sophia@mergington.edu"]
        },
    })


def test_root_redirects_to_static_index(client):
    """Test that the root endpoint redirects to static/index.html"""
    response = client.get("/", follow_redirects=False)
    assert response.status_code == 307
    assert response.headers["location"] == "/static/index.html"


def test_get_activities(client):
    """Test getting all activities"""
    response = client.get("/activities")
    assert response.status_code == 200
    data = response.json()
    assert "Chess Club" in data
    assert "Programming Class" in data
    assert len(data["Chess Club"]["participants"]) == 2
    assert data["Chess Club"]["max_participants"] == 12


def test_signup_for_activity_success(client):
    """Test successful signup for an activity"""
    response = client.post(
        "/activities/Chess%20Club/signup?email=newstudent@mergington.edu"
    )
    assert response.status_code == 200
    data = response.json()
    assert "Signed up newstudent@mergington.edu for Chess Club" in data["message"]
    
    # Verify the student was added
    activities_response = client.get("/activities")
    activities_data = activities_response.json()
    assert "newstudent@mergington.edu" in activities_data["Chess Club"]["participants"]


def test_signup_for_nonexistent_activity(client):
    """Test signup for an activity that doesn't exist"""
    response = client.post(
        "/activities/Nonexistent%20Activity/signup?email=test@mergington.edu"
    )
    assert response.status_code == 404
    assert "Activity not found" in response.json()["detail"]


def test_signup_duplicate_student(client):
    """Test that a student cannot sign up twice for the same activity"""
    # First signup
    response = client.post(
        "/activities/Chess%20Club/signup?email=test@mergington.edu"
    )
    assert response.status_code == 200
    
    # Second signup - should fail
    response = client.post(
        "/activities/Chess%20Club/signup?email=test@mergington.edu"
    )
    assert response.status_code == 400
    assert "already signed up" in response.json()["detail"]


def test_unregister_from_activity_success(client):
    """Test successful unregistering from an activity"""
    # First, ensure the student is registered
    email = "michael@mergington.edu"
    assert email in activities["Chess Club"]["participants"]
    
    # Unregister
    response = client.delete(
        f"/activities/Chess%20Club/unregister?email={email}"
    )
    assert response.status_code == 200
    data = response.json()
    assert f"Unregistered {email} from Chess Club" in data["message"]
    
    # Verify the student was removed
    activities_response = client.get("/activities")
    activities_data = activities_response.json()
    assert email not in activities_data["Chess Club"]["participants"]


def test_unregister_from_nonexistent_activity(client):
    """Test unregistering from an activity that doesn't exist"""
    response = client.delete(
        "/activities/Nonexistent%20Activity/unregister?email=test@mergington.edu"
    )
    assert response.status_code == 404
    assert "Activity not found" in response.json()["detail"]


def test_unregister_student_not_registered(client):
    """Test unregistering a student who is not registered for the activity"""
    response = client.delete(
        "/activities/Chess%20Club/unregister?email=notregistered@mergington.edu"
    )
    assert response.status_code == 400
    assert "not registered" in response.json()["detail"]


def test_activity_participants_count(client):
    """Test that participant count is accurate"""
    # Get initial count
    response = client.get("/activities")
    initial_count = len(response.json()["Programming Class"]["participants"])
    
    # Add a student
    client.post(
        "/activities/Programming%20Class/signup?email=newstudent@mergington.edu"
    )
    
    # Check new count
    response = client.get("/activities")
    new_count = len(response.json()["Programming Class"]["participants"])
    assert new_count == initial_count + 1


def test_multiple_signups_and_unregistrations(client):
    """Test multiple operations on activities"""
    activity_name = "Programming Class"
    
    # Add three students
    emails = [
        "student1@mergington.edu",
        "student2@mergington.edu",
        "student3@mergington.edu"
    ]
    
    for email in emails:
        response = client.post(
            f"/activities/{activity_name.replace(' ', '%20')}/signup?email={email}"
        )
        assert response.status_code == 200
    
    # Verify all were added
    response = client.get("/activities")
    participants = response.json()[activity_name]["participants"]
    for email in emails:
        assert email in participants
    
    # Remove two students
    for email in emails[:2]:
        response = client.delete(
            f"/activities/{activity_name.replace(' ', '%20')}/unregister?email={email}"
        )
        assert response.status_code == 200
    
    # Verify they were removed
    response = client.get("/activities")
    participants = response.json()[activity_name]["participants"]
    assert emails[0] not in participants
    assert emails[1] not in participants
    assert emails[2] in participants
