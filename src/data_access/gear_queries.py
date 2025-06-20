import sqlite3
from typing import Optional, List

# Import Pydantic models from app.py, assuming app.py can be imported or models are defined in a way that avoids circularity.
# This is a common challenge in Flask/Pydantic setups and might require a dedicated models.py in a real app.
from app import GearCreate, GearUpdate, GearInDB, LocationInDB # LocationInDB is needed for _make_gear_in_db_from_row


def _make_gear_in_db_from_row(row_data: sqlite3.Row) -> GearInDB:
    """
    Helper function to convert a database row (potentially from a join) into a GearInDB Pydantic model.
    Expects row_data to be a sqlite3.Row object or a dictionary.
    """
    row_dict = dict(row_data)
    location_info = None
    # Check if location information is present (e.g. from a JOIN)
    if row_dict.get('loc_id') is not None and row_dict.get('loc_name') is not None and row_dict.get('loc_type') is not None:
        location_info = LocationInDB(
            id=row_dict['loc_id'],
            name=row_dict['loc_name'],
            type=row_dict['loc_type'],
            parent_id=row_dict.get('loc_parent_id') # Use .get for optional parent_id from join
        )

    gear_data_for_model = {
        'id': row_dict['id'],
        'name': row_dict['name'],
        'description': row_dict.get('description'), # Use .get for optional fields
        'weight': row_dict['weight'],
        'cost': row_dict.get('cost'),
        'value': row_dict.get('value'),
        'legality': row_dict.get('legality'),
        'category': row_dict.get('category'),
        'location_id': row_dict.get('location_id'),
        'location': location_info
    }
    return GearInDB.model_validate(gear_data_for_model)


def create_gear(db: sqlite3.Connection, gear_data: GearCreate) -> GearInDB:
    """
    Creates a new gear item in the database.
    Commits the transaction if successful.
    Returns the created GearInDB item, including joined location data.
    Raises sqlite3.IntegrityError for database integrity issues.
    """
    try:
        cursor = db.execute(
            "INSERT INTO gear (name, description, weight, cost, value, legality, category, location_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (gear_data.name, gear_data.description, gear_data.weight, gear_data.cost, gear_data.value, gear_data.legality, gear_data.category, gear_data.location_id)
        )
        db.commit()
        new_gear_id = cursor.lastrowid

        # Fetch the newly created gear item with its location data
        fetched_gear = get_gear_by_id(db, new_gear_id)
        if fetched_gear is None:
             raise Exception(f"Failed to fetch newly created gear with id {new_gear_id}")
        return fetched_gear
    except sqlite3.IntegrityError:
        # db.rollback() # Handled by app level
        raise


def get_gear_by_id(db: sqlite3.Connection, gear_id: int) -> Optional[GearInDB]:
    """
    Fetches a single gear item by its ID, including its location data.
    Returns GearInDB instance or None if not found.
    """
    query = """
        SELECT
            g.id, g.name, g.description, g.weight, g.cost, g.value, g.legality, g.category, g.location_id,
            l.id as loc_id, l.name as loc_name, l.type as loc_type, l.parent_id as loc_parent_id
        FROM gear g
        LEFT JOIN locations l ON g.location_id = l.id
        WHERE g.id = ?
    """
    cursor = db.execute(query, (gear_id,))
    row_data = cursor.fetchone()
    if row_data is None:
        return None
    return _make_gear_in_db_from_row(row_data)


def get_all_gear(db: sqlite3.Connection, name_filter: Optional[str], category_filter: Optional[str]) -> List[GearInDB]:
    """
    Fetches all gear items, optionally filtered by name and/or category, including location data.
    """
    base_query = """
        SELECT
            g.id, g.name, g.description, g.weight, g.cost, g.value, g.legality, g.category, g.location_id,
            l.id as loc_id, l.name as loc_name, l.type as loc_type, l.parent_id as loc_parent_id
        FROM gear g
        LEFT JOIN locations l ON g.location_id = l.id
    """
    filters = []
    params = []

    if name_filter:
        filters.append("g.name LIKE ?")
        params.append(f"%{name_filter}%")

    if category_filter:
        filters.append("g.category = ?")
        params.append(category_filter)

    if filters:
        base_query += " WHERE " + " AND ".join(filters)

    cursor = db.execute(base_query, tuple(params))
    gear_rows = cursor.fetchall()
    return [_make_gear_in_db_from_row(row) for row in gear_rows]


def update_gear(db: sqlite3.Connection, gear_id: int, gear_data: GearUpdate) -> Optional[GearInDB]:
    """
    Updates an existing gear item.
    Only updates fields present in gear_data using model_dump(exclude_unset=True).
    Commits transaction if successful.
    Returns updated GearInDB or None if gear_id not found.
    Raises sqlite3.IntegrityError for database integrity issues.
    """
    existing_gear = get_gear_by_id(db, gear_id) # Check existence and get current data (not strictly needed here but good check)
    if existing_gear is None:
        return None

    update_fields = gear_data.model_dump(exclude_unset=True)
    if not update_fields:
        return existing_gear # No fields to update, return current state

    set_clauses = [f"{field} = ?" for field in update_fields.keys()]
    params = list(update_fields.values())
    params.append(gear_id)

    query = f"UPDATE gear SET {', '.join(set_clauses)} WHERE id = ?"

    try:
        db.execute(query, tuple(params))
        db.commit()
        return get_gear_by_id(db, gear_id) # Fetch the updated record with location
    except sqlite3.IntegrityError:
        # db.rollback()
        raise


def delete_gear(db: sqlite3.Connection, gear_id: int) -> bool:
    """
    Deletes a gear item by its ID.
    Commits transaction if successful.
    Returns True if deletion occurred, False if gear_id not found.
    """
    cursor = db.execute("SELECT id FROM gear WHERE id = ?", (gear_id,))
    if cursor.fetchone() is None:
        return False

    try:
        db.execute("DELETE FROM gear WHERE id = ?", (gear_id,))
        db.commit()
        return True
    except sqlite3.IntegrityError: # Should not happen with gear unless other tables FK to it without ON DELETE CASCADE/SET NULL
        # db.rollback()
        raise
