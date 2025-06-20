import pytest
import json
from app import UserInDB # To validate response structure if needed

# Helper function to register a user (used in multiple tests)
def register_user_util(client, username, password):
    return client.post('/api/auth/register', json={
        "username": username,
        "password": password
    })

# Helper function to login a user and get token (used in multiple tests)
def login_user_util(client, username, password):
    response = client.post('/api/auth/login', json={
        "username": username,
        "password": password
    })
    if response.status_code == 200:
        return response.get_json().get('access_token')
    return None

def test_register_user_success(client):
    """Test successful user registration."""
    response = register_user_util(client, "testuser_api_reg", "password123")
    assert response.status_code == 201
    data = response.get_json()
    assert data["username"] == "testuser_api_reg"
    assert "id" in data
    # Password hash should not be in the response

def test_register_user_duplicate_username(client):
    """Test registering a user with a username that already exists."""
    register_user_util(client, "test_api_duplicate", "password123") # First registration
    response = register_user_util(client, "test_api_duplicate", "password456") # Second attempt

    assert response.status_code == 409
    data = response.get_json()
    assert "error" in data
    assert "Username already exists" in data["error"]["message"]

def test_register_user_missing_fields(client):
    """Test registration with missing fields (e.g., no password)."""
    response = client.post('/api/auth/register', json={"username": "missing_password"})
    assert response.status_code == 400 # Pydantic validation error
    data = response.get_json()
    assert isinstance(data, list) # Pydantic errors are a list of error objects
    # Example check for a specific error detail, structure might vary
    assert any(err.get('type') == 'missing' and 'password' in err.get('loc', []) for err in data)


def test_login_user_success(client):
    """Test successful user login."""
    register_user_util(client, "testuser_api_login", "password123") # Register user first

    response = client.post('/api/auth/login', json={
        "username": "testuser_api_login",
        "password": "password123"
    })
    assert response.status_code == 200
    data = response.get_json()
    assert "access_token" in data
    assert data["access_token"] is not None

def test_login_user_invalid_username(client):
    """Test login with a username that does not exist."""
    response = client.post('/api/auth/login', json={
        "username": "nonexistentuser_api",
        "password": "password123"
    })
    assert response.status_code == 401 # Or as per your app's error handling
    data = response.get_json()
    assert "error" in data
    assert "Invalid username or password" in data["error"]["message"]

def test_login_user_invalid_password(client):
    """Test login with an incorrect password."""
    register_user_util(client, "testuser_api_badpass", "password123") # Register user

    response = client.post('/api/auth/login', json={
        "username": "testuser_api_badpass",
        "password": "wrongpassword"
    })
    assert response.status_code == 401
    data = response.get_json()
    assert "error" in data
    assert "Invalid username or password" in data["error"]["message"]

def test_login_user_missing_fields(client):
    """Test login with missing username or password."""
    response_no_user = client.post('/api/auth/login', json={"password": "password123"})
    assert response_no_user.status_code == 400
    data_no_user = response_no_user.get_json()
    assert "error" in data_no_user
    assert "Username and password required" in data_no_user["error"]["message"]

    response_no_pass = client.post('/api/auth/login', json={"username": "testuser"})
    assert response_no_pass.status_code == 400
    data_no_pass = response_no_pass.get_json()
    assert "error" in data_no_pass
    assert "Username and password required" in data_no_pass["error"]["message"]

# The session-scoped 'app' fixture means the DB is reset once per session.
# API tests using client modify this shared DB state.
# Using unique usernames/data per test is important here.
# For example, 'testuser_api_reg', 'test_api_duplicate', 'testuser_api_login' are all unique.
