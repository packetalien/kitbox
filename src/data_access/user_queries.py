import sqlite3
from typing import Optional
from werkzeug.security import generate_password_hash, check_password_hash

# Assuming Pydantic models are in app.py or a models.py file accessible.
from app import UserCreate, UserInDB # UserBase is implicitly handled by UserInDB for returns

def create_user(db: sqlite3.Connection, user_data: UserCreate) -> UserInDB:
    """
    Creates a new user in the database with a hashed password.
    Commits the transaction if successful.
    Raises sqlite3.IntegrityError if the username already exists.
    """
    hashed_password = generate_password_hash(user_data.password)
    try:
        cursor = db.execute(
            "INSERT INTO users (username, password_hash) VALUES (?, ?)",
            (user_data.username, hashed_password)
        )
        db.commit()
        new_user_id = cursor.lastrowid
        # Fetch the user to return as UserInDB (without password hash)
        created_user_row = db.execute("SELECT id, username FROM users WHERE id = ?", (new_user_id,)).fetchone()
        if created_user_row is None:
            # This should not happen if INSERT was successful
            raise Exception(f"Failed to fetch newly created user with id {new_user_id} after insert.")
        return UserInDB.model_validate(created_user_row)
    except sqlite3.IntegrityError: # Handles UNIQUE constraint on username
        # db.rollback() should be handled by the route calling this if an error bubbles up
        raise

def get_user_row_by_username(db: sqlite3.Connection, username: str) -> Optional[sqlite3.Row]:
    """
    Fetches a user by their username and returns the raw sqlite3.Row object.
    This is primarily for internal use by authentication logic that needs the password_hash.
    """
    cursor = db.execute("SELECT * FROM users WHERE username = ?", (username,))
    row = cursor.fetchone()
    return row

def get_user_by_id(db: sqlite3.Connection, user_id: int) -> Optional[UserInDB]:
    """
    Fetches a user by their ID.
    Returns UserInDB instance (without password hash for security) or None if not found.
    Used by JWT user_lookup_loader.
    """
    cursor = db.execute("SELECT id, username FROM users WHERE id = ?", (user_id,))
    row = cursor.fetchone()
    if row is None:
        return None
    return UserInDB.model_validate(row)
