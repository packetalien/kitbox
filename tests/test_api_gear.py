import pytest
import json

# Helper to get an auth token.
# For a larger test suite, this could be a fixture in conftest.py
def get_auth_token(client, username="test_gear_user", password="password123"):
    # Ensure user is registered
    client.post('/api/auth/register', json={"username": username, "password": password})
    # Login to get token
    response = client.post('/api/auth/login', json={"username": username, "password": password})
    if response.status_code == 200:
        return response.get_json().get('access_token')
    pytest.fail(f"Failed to get auth token for {username}. Status: {response.status_code}, Response: {response.data}")


@pytest.fixture(scope="module") # Token can be reused for all tests in this module
def auth_headers(client):
    token = get_auth_token(client)
    return {"Authorization": f"Bearer {token}"}

# --- Test GET /api/gear ---
def test_get_all_gear_unauthenticated(client):
    response = client.get('/api/gear')
    assert response.status_code == 401 # Expecting JWT Missing error

def test_get_all_gear_authenticated(client, auth_headers):
    response = client.get('/api/gear', headers=auth_headers)
    assert response.status_code == 200
    assert isinstance(response.get_json(), list)

# --- Test POST /api/gear ---
def test_post_gear_unauthenticated(client):
    gear_data = {"name": "Test Sword", "weight": 1.0, "description": "A test item"}
    response = client.post('/api/gear', json=gear_data)
    assert response.status_code == 401

def test_post_gear_authenticated_valid_data(client, auth_headers):
    gear_data = {"name": "Shiny Helm", "weight": 1.5, "description": "Protects the noggin"}
    response = client.post('/api/gear', json=gear_data, headers=auth_headers)
    assert response.status_code == 201
    data = response.get_json()
    assert data["name"] == "Shiny Helm"
    assert "id" in data

def test_post_gear_authenticated_invalid_data(client, auth_headers):
    gear_data = {"name": "Heavy Rock"} # Missing 'weight'
    response = client.post('/api/gear', json=gear_data, headers=auth_headers)
    assert response.status_code == 400 # Pydantic validation error
    # Pydantic errors are a list of error objects
    assert any("weight" in err.get('loc', []) and err.get('type') == 'missing' for err in response.get_json())


# --- Test GET /api/gear/{id} ---
def test_get_gear_by_id_unauthenticated(client):
    # Assuming a gear item with ID 1 might exist from schema or previous tests (careful with state)
    # Better to create one if sure about state, or if not, this test is less deterministic.
    # For now, just test the auth part.
    response = client.get('/api/gear/1')
    assert response.status_code == 401

def test_get_gear_by_id_authenticated_valid(client, auth_headers):
    # Create an item first to ensure it exists
    gear_data = {"name": "Specific Test Gauntlets", "weight": 0.5}
    post_response = client.post('/api/gear', json=gear_data, headers=auth_headers)
    assert post_response.status_code == 201
    item_id = post_response.get_json()["id"]

    response = client.get(f'/api/gear/{item_id}', headers=auth_headers)
    assert response.status_code == 200
    data = response.get_json()
    assert data["id"] == item_id
    assert data["name"] == "Specific Test Gauntlets"

def test_get_gear_by_id_authenticated_invalid_id(client, auth_headers):
    response = client.get('/api/gear/99999', headers=auth_headers) # Non-existent ID
    assert response.status_code == 404


# --- Test PUT /api/gear/{id} ---
def test_put_gear_unauthenticated(client):
    response = client.put('/api/gear/1', json={"name": "Updated Name", "weight": 1.0})
    assert response.status_code == 401

def test_put_gear_authenticated_valid(client, auth_headers):
    # Create an item
    gear_data = {"name": "ItemToUpdate", "weight": 1.0}
    post_response = client.post('/api/gear', json=gear_data, headers=auth_headers)
    item_id = post_response.get_json()["id"]

    update_data = {"name": "UpdatedItemName", "weight": 1.2, "description": "Now updated."}
    response = client.put(f'/api/gear/{item_id}', json=update_data, headers=auth_headers)
    assert response.status_code == 200
    data = response.get_json()
    assert data["name"] == "UpdatedItemName"
    assert data["weight"] == 1.2
    assert data["description"] == "Now updated."

# --- Test PATCH /api/gear/{id} ---
def test_patch_gear_unauthenticated(client):
    response = client.patch('/api/gear/1', json={"description": "Patched description"})
    assert response.status_code == 401

def test_patch_gear_authenticated_valid(client, auth_headers):
    # Create an item
    gear_data = {"name": "ItemToPatch", "weight": 2.0, "description": "Original Desc"}
    post_response = client.post('/api/gear', json=gear_data, headers=auth_headers)
    item_id = post_response.get_json()["id"]

    patch_data = {"description": "Patched Description Only"}
    response = client.patch(f'/api/gear/{item_id}', json=patch_data, headers=auth_headers)
    assert response.status_code == 200
    data = response.get_json()
    assert data["name"] == "ItemToPatch" # Name should be unchanged
    assert data["description"] == "Patched Description Only"

# --- Test DELETE /api/gear/{id} ---
def test_delete_gear_unauthenticated(client):
    response = client.delete('/api/gear/1')
    assert response.status_code == 401

def test_delete_gear_authenticated_valid(client, auth_headers):
    # Create an item
    gear_data = {"name": "ItemToDelete", "weight": 0.1}
    post_response = client.post('/api/gear', json=gear_data, headers=auth_headers)
    item_id = post_response.get_json()["id"]

    delete_response = client.delete(f'/api/gear/{item_id}', headers=auth_headers)
    assert delete_response.status_code == 200
    assert delete_response.get_json()["message"] == f"Gear item with id {item_id} deleted successfully"

    # Verify it's gone
    get_response = client.get(f'/api/gear/{item_id}', headers=auth_headers)
    assert get_response.status_code == 404

# Note: Uses a module-scoped auth_headers fixture. This means one user login for all gear tests.
# The database state is shared across these tests due to session-scoped app fixture.
# Tests are written to be mostly independent by creating new items as needed.
# Using unique names for items helps avoid collisions if tests were to run concurrently or if cleanup wasn't perfect.
