# Full app.py content for the worker to use:

import sqlite3
import os # For os.path.exists and os.path.join
from flask import Flask, render_template, g, current_app, request, jsonify, abort
from pydantic import BaseModel, Field, ValidationError # Pydantic v2
from typing import Optional, List

DATABASE = 'kitbox.db' # Database file name
app = Flask(__name__, template_folder='.') # Serve templates from project root.

# --- Pydantic Models ---
class LocationBase(BaseModel):
    name: str = Field(..., min_length=1, description="Name of the location, e.g., 'Head', 'Backpack'")
    type: str = Field(..., description="Type of location, e.g., 'Body Slot', 'Container', 'Generic'")
    parent_id: Optional[int] = Field(None, description="ID of the parent location, for nested containers")

class LocationCreate(LocationBase): 
    pass

class LocationInDB(LocationBase):
    id: int
    class Config:
        from_attributes = True 

class GearBase(BaseModel):
    name: str = Field(..., min_length=1, description="Name of the gear, e.g., 'Steel Helmet'")
    description: Optional[str] = None
    weight: float = Field(..., ge=0, description="Weight in lbs, e.g., 2.0")
    cost: Optional[float] = Field(None, ge=0, description="Cost in currency, e.g., 50.0")
    value: Optional[float] = Field(None, ge=0, description="Value in currency, e.g., 45.0")
    legality: Optional[str] = Field(None, description="E.g., 'Legal', 'Restricted'")
    location_id: Optional[int] = Field(None, description="ID of the location where the item is stored")

class GearCreate(GearBase):
    pass

class GearUpdate(BaseModel): 
    name: Optional[str] = Field(None, min_length=1)
    description: Optional[str] = None
    weight: Optional[float] = Field(None, ge=0)
    cost: Optional[float] = Field(None, ge=0)
    value: Optional[float] = Field(None, ge=0)
    legality: Optional[str] = None
    location_id: Optional[int] = None 

class GearInDB(GearBase): 
    id: int
    location: Optional[LocationInDB] = None 

    class Config:
        from_attributes = True

# --- Database Helper Functions ---
def get_db_path():
    return os.path.join(app.root_path, DATABASE)

def get_db():
    if 'db' not in g:
        db_path = get_db_path()
        g.db = sqlite3.connect(db_path, detect_types=sqlite3.PARSE_DECLTYPES)
        g.db.row_factory = sqlite3.Row
    return g.db

def close_db(e=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()

def init_db(reinit=False):
    db_path = get_db_path()
    db_exists = os.path.exists(db_path)

    if reinit and db_exists:
        try:
            os.remove(db_path)
            current_app.logger.info(f"Removed existing database {db_path} for reinitialization.")
            db_exists = False
        except OSError as e:
            current_app.logger.error(f"Error removing database {db_path}: {e}")
            return 

    if not db_exists or reinit:
        conn = None
        try:
            conn = sqlite3.connect(db_path)
            schema_path = os.path.join(app.root_path, 'src', 'database', 'schema.sql')
            with open(schema_path, mode='r') as f:
                conn.executescript(f.read())
            conn.commit()
            current_app.logger.info(f"Initialized the database {db_path} from schema: {schema_path}")
        except sqlite3.Error as e:
            current_app.logger.error(f"SQLite error during DB initialization: {e}")
        except FileNotFoundError:
            current_app.logger.error(f"Failed to find schema.sql at {schema_path}.")
        except Exception as e:
            current_app.logger.error(f"An unexpected error occurred during DB init: {e}")
        finally:
            if conn:
                conn.close()
    else:
        current_app.logger.info(f"Database {db_path} already exists. Skipping initialization.")
    
app.teardown_appcontext(close_db) 

@app.cli.command('init-db') 
def init_db_command():
    with app.app_context(): 
        init_db(reinit=True) 
    print(f"Database '{DATABASE}' initialized (or re-initialized).")

@app.before_request
def ensure_db_initialized():
    if not hasattr(app, '_db_initialized_this_session'): 
        with app.app_context():
            init_db()
        app._db_initialized_this_session = True

# --- Routes to serve HTML files ---
@app.route('/')
def master_list_page():
    return render_template('master_list.html')

@app.route('/paperdoll')
def paperdoll_page():
    return render_template('paperdoll.html')

@app.route('/containers') 
def containers_page():
    return render_template('containers.html')

# --- Helper function to build GearInDB from a database row ---
def _make_gear_in_db_from_row(row_data):
    row_dict = dict(row_data) 
    location_info = None
    if row_dict.get('loc_id') is not None: 
        location_info = LocationInDB(
            id=row_dict['loc_id'], 
            name=row_dict['loc_name'], 
            type=row_dict['loc_type'], 
            parent_id=row_dict['loc_parent_id']
        )
    
    gear_data_for_model = {
        'id': row_dict['id'],
        'name': row_dict['name'],
        'description': row_dict['description'],
        'weight': row_dict['weight'],
        'cost': row_dict['cost'],
        'value': row_dict['value'],
        'legality': row_dict['legality'],
        'location_id': row_dict['location_id'], 
        'location': location_info 
    }
    return GearInDB.model_validate(gear_data_for_model) 

# --- Gear CRUD API Endpoints ---
@app.route('/api/gear', methods=['POST'])
def create_gear_item_api():
    try:
        gear_data = GearCreate(**request.json)
    except ValidationError as e:
        return jsonify(e.errors()), 400 
    
    db = get_db()
    try:
        cursor = db.execute(
            "INSERT INTO gear (name, description, weight, cost, value, legality, location_id) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (gear_data.name, gear_data.description, gear_data.weight, gear_data.cost, gear_data.value, gear_data.legality, gear_data.location_id)
        )
        db.commit()
        new_gear_id = cursor.lastrowid
        response_data, status_code = get_gear_item_api(new_gear_id) 
        return response_data, 201 
    except sqlite3.IntegrityError as e: 
        db.rollback()
        current_app.logger.error(f"Integrity error creating gear: {e}")
        return jsonify({"error": "Database integrity error", "details": str(e)}), 400
    except Exception as e: 
        db.rollback()
        current_app.logger.error(f"Unexpected error creating gear: {e}")
        return jsonify({"error": "Failed to create gear item"}), 500

@app.route('/api/gear', methods=['GET'])
def get_all_gear_api():
    db = get_db()
    query = """
        SELECT
            g.id, g.name, g.description, g.weight, g.cost, g.value, g.legality, g.location_id,
            l.id as loc_id, l.name as loc_name, l.type as loc_type, l.parent_id as loc_parent_id
        FROM gear g
        LEFT JOIN locations l ON g.location_id = l.id
    """
    cursor = db.execute(query)
    gear_rows = cursor.fetchall()
    gear_list = [_make_gear_in_db_from_row(row) for row in gear_rows]
    return jsonify([gear.model_dump() for gear in gear_list]) 

@app.route('/api/gear/<int:gear_id>', methods=['GET'])
def get_gear_item_api(gear_id):
    db = get_db()
    query = """
        SELECT
            g.id, g.name, g.description, g.weight, g.cost, g.value, g.legality, g.location_id,
            l.id as loc_id, l.name as loc_name, l.type as loc_type, l.parent_id as loc_parent_id
        FROM gear g
        LEFT JOIN locations l ON g.location_id = l.id
        WHERE g.id = ?
    """
    cursor = db.execute(query, (gear_id,))
    row_data = cursor.fetchone()
    if row_data is None:
        abort(404, description=f"Gear item with id {gear_id} not found")
    
    gear_item = _make_gear_in_db_from_row(row_data)
    return jsonify(gear_item.model_dump()), 200

@app.route('/api/gear/<int:gear_id>', methods=['PUT'])
def update_gear_item_api(gear_id):
    try:
        update_data = GearUpdate(**request.json)
    except ValidationError as e:
        return jsonify(e.errors()), 400

    db = get_db()
    cursor = db.execute("SELECT id FROM gear WHERE id = ?", (gear_id,))
    if cursor.fetchone() is None:
        abort(404, description=f"Gear item with id {gear_id} not found for update")

    set_clauses = []
    params = []
    for field, value in update_data.model_dump(exclude_unset=True).items():
        set_clauses.append(f"{field} = ?")
        params.append(value)
    
    if not set_clauses: 
        return jsonify({"message": "No update fields provided"}), 400
    
    params.append(gear_id) 
    query = f"UPDATE gear SET {', '.join(set_clauses)} WHERE id = ?"
    
    try:
        db.execute(query, tuple(params))
        db.commit()
        return get_gear_item_api(gear_id) 
    except sqlite3.IntegrityError as e: 
        db.rollback()
        current_app.logger.error(f"Integrity error updating gear {gear_id}: {e}")
        return jsonify({"error": "Database integrity error", "details": str(e)}), 400
    except Exception as e:
        db.rollback()
        current_app.logger.error(f"Unexpected error updating gear {gear_id}: {e}")
        return jsonify({"error": "Failed to update gear item"}), 500

@app.route('/api/gear/<int:gear_id>', methods=['DELETE'])
def delete_gear_item_api(gear_id):
    db = get_db()
    cursor = db.execute("SELECT id FROM gear WHERE id = ?", (gear_id,))
    if cursor.fetchone() is None:
        abort(404, description=f"Gear item with id {gear_id} not found for deletion")
    
    try:
        db.execute("DELETE FROM gear WHERE id = ?", (gear_id,))
        db.commit()
        return jsonify({"message": f"Gear item with id {gear_id} deleted successfully"}), 200
    except Exception as e: 
        db.rollback()
        current_app.logger.error(f"Error deleting gear {gear_id}: {e}")
        return jsonify({"error": "Failed to delete gear item"}), 500

# --- Location API Endpoints ---
@app.route('/api/locations', methods=['GET'])
def get_all_locations_api():
    db = get_db()
    cursor = db.execute("SELECT * FROM locations")
    location_rows = cursor.fetchall()
    location_list = [LocationInDB.model_validate(row) for row in location_rows] 
    return jsonify([loc.model_dump() for loc in location_list])

@app.route('/api/locations/<int:location_id>', methods=['GET'])
def get_location_item_api(location_id):
    db = get_db()
    cursor = db.execute("SELECT * FROM locations WHERE id = ?", (location_id,))
    row = cursor.fetchone()
    if row is None:
        abort(404, description=f"Location with id {location_id} not found")
    location_item = LocationInDB.model_validate(row) 
    return jsonify(location_item.model_dump())

@app.route('/api/locations/<int:location_id>/items', methods=['GET'])
def get_items_in_location_api(location_id):
    db = get_db()
    loc_cursor = db.execute("SELECT id FROM locations WHERE id = ?", (location_id,))
    if loc_cursor.fetchone() is None:
        abort(404, description=f"Location with id {location_id} not found.")
    
    query = """
        SELECT
            g.id, g.name, g.description, g.weight, g.cost, g.value, g.legality, g.location_id,
            l.id as loc_id, l.name as loc_name, l.type as loc_type, l.parent_id as loc_parent_id
        FROM gear g
        LEFT JOIN locations l ON g.location_id = l.id 
        WHERE g.location_id = ? 
    """
    gear_cursor = db.execute(query, (location_id,))
    gear_rows = gear_cursor.fetchall()
    
    gear_list = [_make_gear_in_db_from_row(row) for row in gear_rows]
    return jsonify([gear.model_dump() for gear in gear_list])

@app.route('/api/test')
def api_test():
    return {"message": "Flask API is running!"}

if __name__ == '__main__':
    with app.app_context(): 
        init_db() 
    app.run(debug=True, port=5000)
