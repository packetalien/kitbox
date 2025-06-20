import sqlite3
from typing import Optional, List

# Assuming Pydantic models are in app.py or a models.py file accessible via from .. import
# For now, to avoid circular dependency issues if models are in app.py and app.py imports these query files,
# we might need to redefine or pass models.
# However, the prompt implies app.py defines routes and Pydantic models are self-contained enough.
# Let's try importing directly from app.py. This can be risky if app.py also imports this.
# A better structure would be a dedicated models.py.
# For the purpose of this task, we'll assume this import works or will be resolved later.
from app import LocationCreate, LocationInDB, GearInDB, LocationUpdate # GearInDB for get_items_in_location
from .gear_queries import _make_gear_in_db_from_row # Import from sibling module

def create_location(db: sqlite3.Connection, location_data: LocationCreate) -> LocationInDB:
    """
    Creates a new location in the database.
    Commits the transaction if successful.
    Raises sqlite3.IntegrityError for database integrity issues.
    """
    try:
        cursor = db.execute(
            "INSERT INTO locations (name, type, parent_id) VALUES (?, ?, ?)",
            (location_data.name, location_data.type, location_data.parent_id)
        )
        db.commit()
        new_location_id = cursor.lastrowid

        created_location_row = db.execute("SELECT * FROM locations WHERE id = ?", (new_location_id,)).fetchone()
        if created_location_row is None:
            # This case should ideally not be reached if INSERT was successful and auto-increment ID works
            raise Exception(f"Failed to fetch newly created location with id {new_location_id}")

        return LocationInDB.model_validate(created_location_row)
    except sqlite3.IntegrityError:
        # db.rollback() # Handled by app level error handler or teardown
        raise
    except Exception as e:
        # db.rollback()
        raise Exception(f"Error creating location: {e}")


def get_location_by_id(db: sqlite3.Connection, location_id: int) -> Optional[LocationInDB]:
    """
    Fetches a single location by its ID.
    Returns LocationInDB instance or None if not found.
    """
    cursor = db.execute("SELECT * FROM locations WHERE id = ?", (location_id,))
    row = cursor.fetchone()
    if row is None:
        return None
    return LocationInDB.model_validate(row)


def get_all_locations(db: sqlite3.Connection, name_filter: Optional[str], type_filter: Optional[str]) -> List[LocationInDB]:
    """
    Fetches all locations, optionally filtered by name and/or type.
    """
    base_query = "SELECT * FROM locations"
    filters = []
    params = []

    if name_filter:
        filters.append("name LIKE ?")
        params.append(f"%{name_filter}%")

    if type_filter:
        filters.append("type = ?")
        params.append(type_filter)

    if filters:
        base_query += " WHERE " + " AND ".join(filters)

    cursor = db.execute(base_query, tuple(params))
    location_rows = cursor.fetchall()
    return [LocationInDB.model_validate(row) for row in location_rows]


def update_location(db: sqlite3.Connection, location_id: int, location_data: LocationUpdate) -> Optional[LocationInDB]:
    """
    Updates an existing location.
    Only updates fields present in location_data.
    Commits transaction if successful.
    Returns updated LocationInDB or None if location_id not found.
    Raises sqlite3.IntegrityError for database integrity issues.
    """
    # First, check if the location exists
    existing_location_row = db.execute("SELECT id FROM locations WHERE id = ?", (location_id,)).fetchone()
    if existing_location_row is None:
        return None

    update_fields = location_data.model_dump(exclude_unset=True)
    if not update_fields:
        # No fields to update, but location exists. Return current state.
        return get_location_by_id(db, location_id)

    set_clauses = [f"{field} = ?" for field in update_fields.keys()]
    params = list(update_fields.values())
    params.append(location_id)

    query = f"UPDATE locations SET {', '.join(set_clauses)} WHERE id = ?"

    try:
        db.execute(query, tuple(params))
        db.commit()

        updated_location_row = db.execute("SELECT * FROM locations WHERE id = ?", (location_id,)).fetchone()
        if updated_location_row is None: # Should not happen
            raise Exception("Failed to fetch location post-update, though update seemed successful.")
        return LocationInDB.model_validate(updated_location_row)
    except sqlite3.IntegrityError:
        # db.rollback()
        raise


def delete_location(db: sqlite3.Connection, location_id: int) -> bool:
    """
    Deletes a location by its ID.
    Commits transaction if successful.
    Returns True if deletion occurred, False if location_id not found.
    """
    # Check if location exists first
    cursor = db.execute("SELECT id FROM locations WHERE id = ?", (location_id,))
    if cursor.fetchone() is None:
        return False

    try:
        db.execute("DELETE FROM locations WHERE id = ?", (location_id,))
        db.commit()
        return True
    except sqlite3.IntegrityError: # Should be less likely due to ON DELETE SET NULL
        # db.rollback()
        raise


def get_items_in_location(db: sqlite3.Connection, location_id: int) -> Optional[List[GearInDB]]:
    """
    Fetches all gear items for a given location_id.
    Returns a list of GearInDB items, or None if the location itself doesn't exist.
    Uses _make_gear_in_db_from_row (or similar logic) for object creation.
    """
    loc_cursor = db.execute("SELECT id FROM locations WHERE id = ?", (location_id,))
    if loc_cursor.fetchone() is None:
        return None # Location not found

    query = """
        SELECT
            g.id, g.name, g.description, g.weight, g.cost, g.value, g.legality, g.category, g.location_id,
            l.id as loc_id, l.name as loc_name, l.type as loc_type, l.parent_id as loc_parent_id
        FROM gear g
        LEFT JOIN locations l ON g.location_id = l.id
        WHERE g.location_id = ?
    """
    gear_cursor = db.execute(query, (location_id,))
    gear_rows = gear_cursor.fetchall()

    # _make_gear_in_db_from_row is now imported from .gear_queries
    gear_list = [_make_gear_in_db_from_row(row) for row in gear_rows]
    return gear_list
