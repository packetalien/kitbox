import pytest
import sqlite3
from app import UserCreate, UserInDB # Import Pydantic models
from src.data_access import user_queries # Import user query functions
from werkzeug.security import check_password_hash

def test_create_user_success(db):
    """Test successful user creation."""
    user_data = UserCreate(username="testuser_dal", password="password123")
    created_user = user_queries.create_user(db, user_data)

    assert created_user is not None
    assert created_user.id is not None
    assert created_user.username == user_data.username

    # Verify password was hashed and stored correctly (indirectly)
    # We can fetch the raw row to check the hash if needed, or trust create_user
    user_row = db.execute("SELECT password_hash FROM users WHERE username = ?", (user_data.username,)).fetchone()
    assert user_row is not None
    assert check_password_hash(user_row['password_hash'], user_data.password)

def test_create_user_duplicate_username(db):
    """Test creating a user with a username that already exists."""
    user_data1 = UserCreate(username="test_duplicate", password="password123")
    user_queries.create_user(db, user_data1) # Create first user

    user_data2 = UserCreate(username="test_duplicate", password="password456")
    with pytest.raises(sqlite3.IntegrityError): # Expecting an IntegrityError due to UNIQUE constraint
        user_queries.create_user(db, user_data2)

def test_get_user_row_by_username_existing(db):
    """Test fetching an existing user row by username."""
    user_data = UserCreate(username="test_get_user", password="password123")
    user_queries.create_user(db, user_data)

    user_row = user_queries.get_user_row_by_username(db, "test_get_user")
    assert user_row is not None
    assert user_row["username"] == "test_get_user"
    assert "password_hash" in user_row.keys() # Ensure hash is present
    assert check_password_hash(user_row['password_hash'], "password123")

def test_get_user_row_by_username_non_existent(db):
    """Test fetching a non-existent user row by username."""
    user_row = user_queries.get_user_row_by_username(db, "nonexistentuser_dal")
    assert user_row is None

def test_get_user_by_id_existing(db):
    """Test fetching an existing user by ID."""
    user_data = UserCreate(username="test_get_id", password="password123")
    created_user_info = user_queries.create_user(db, user_data) # This returns UserInDB

    fetched_user = user_queries.get_user_by_id(db, created_user_info.id)
    assert fetched_user is not None
    assert fetched_user.id == created_user_info.id
    assert fetched_user.username == "test_get_id"
    # UserInDB should not contain password_hash
    assert not hasattr(fetched_user, 'password_hash')

def test_get_user_by_id_non_existent(db):
    """Test fetching a non-existent user by ID."""
    fetched_user = user_queries.get_user_by_id(db, 99999) # Assuming 99999 is not a valid ID
    assert fetched_user is None

# Note: The conftest.py app fixture is session-scoped and reinitializes the DB once per session.
# These DAL tests, if they modify data (like create_user), will have those modifications
# visible to subsequent tests within the same session.
# For true isolation in DAL tests, the `db` or `app` fixture might need to be function-scoped
# or tests need to ensure unique data / cleanup.
# Given the current setup, using unique usernames per test function is a good practice.
