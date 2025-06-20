# Full app.py content for the worker to use:

import sqlite3
import os # For os.path.exists and os.path.join
from flask import Flask, render_template, g, current_app, request, jsonify, abort
from pydantic import BaseModel, Field, ValidationError # Pydantic v2
from typing import Optional, List
from config import Config # Import the Config class

# DATABASE = 'kitbox.db' # Replaced by config
app = Flask(__name__, template_folder='.') # Serve templates from project root.
app.config.from_object(Config) # Load configuration from config.py

# --- Pydantic Models ---
class LocationBase(BaseModel):
    name: str = Field(..., min_length=1, description="Name of the location, e.g., 'Head', 'Backpack'")
    type: str = Field(..., description="Type of location, e.g., 'Body Slot', 'Container', 'Generic'")
    parent_id: Optional[int] = Field(None, description="ID of the parent location, for nested containers")

class LocationCreate(LocationBase):
    pass

class LocationUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, description="Name of the location, e.g., 'Head', 'Backpack'")
    type: Optional[str] = Field(None, description="Type of location, e.g., 'Body Slot', 'Container', 'Generic'")
    parent_id: Optional[int] = Field(None, description="ID of the parent location, for nested containers")

class LocationInDB(LocationBase):
    id: int
    class Config:
        from_attributes = True

# --- User Pydantic Models ---
class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)

class UserCreate(UserBase):
    password: str = Field(..., min_length=8)

class UserInDB(UserBase):
    id: int
    # password_hash: str # Not typically exposed in API responses

    class Config:
        from_attributes = True

class GearBase(BaseModel):
    name: str = Field(..., min_length=1, description="Name of the gear, e.g., 'Steel Helmet'")
    description: Optional[str] = None
    weight: float = Field(..., ge=0, description="Weight in lbs, e.g., 2.0")
    cost: Optional[float] = Field(None, ge=0, description="Cost in currency, e.g., 50.0")
    value: Optional[float] = Field(None, ge=0, description="Value in currency, e.g., 45.0")
    legality: Optional[str] = Field(None, description="E.g., 'Legal', 'Restricted'")
    category: Optional[str] = None # Added category
    location_id: Optional[int] = Field(None, description="ID of the location where the item is stored")

class GearCreate(GearBase):
    category: Optional[str] = None # Explicitly adding, though GearBase has it. Ensures it can be set.
    pass

class GearUpdate(BaseModel): 
    name: Optional[str] = Field(None, min_length=1)
    description: Optional[str] = None
    weight: Optional[float] = Field(None, ge=0)
    cost: Optional[float] = Field(None, ge=0)
    value: Optional[float] = Field(None, ge=0)
    legality: Optional[str] = None
    category: Optional[str] = None # Added category
    location_id: Optional[int] = None 

class GearInDB(GearBase): 
    id: int
    location: Optional[LocationInDB] = None 

    class Config:
        from_attributes = True

# --- Database Helper Functions ---
def get_db_path():
    # Use DATABASE_FILENAME from app.config, accessed via current_app
    return os.path.join(current_app.root_path, current_app.config['DATABASE_FILENAME'])

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
    # Use DATABASE_FILENAME from app.config, accessed via current_app
    print(f"Database '{current_app.config['DATABASE_FILENAME']}' initialized (or re-initialized).")

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

from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash # Already in user_queries, but useful here too for clarity

# Data Access Layer Imports
from src.data_access import gear_queries, location_queries, user_queries

# --- App Configuration & JWT Setup ---
# app.config["JWT_SECRET_KEY"] is now loaded from Config object via app.config.from_object(Config)
jwt = JWTManager(app) # JWTManager will use app.config["JWT_SECRET_KEY"]

# --- Helper for Standardized JSON Error Responses ---
def make_error_response(message: str, status_code: int, **kwargs):
    error_payload = {"code": status_code, "message": message}
    if kwargs:
        error_payload.update(kwargs)
    return jsonify({"error": error_payload}), status_code

# --- User Loader for JWT ---
@jwt.user_lookup_loader
def user_lookup_callback(_jwt_header, jwt_data):
    identity = jwt_data["sub"] # "sub" is where the user_id is stored by create_access_token
    db = get_db()
    user = user_queries.get_user_by_id(db, identity)
    return user # Returns UserInDB instance or None

# --- Auth API Endpoints ---
@app.route('/api/auth/register', methods=['POST'])
def register_user():
    try:
        user_create_data = UserCreate(**request.json)
    except ValidationError as e:
        # Pydantic validation errors are already JSON and quite descriptive.
        # Keeping them as is.
        current_app.logger.warning(f"Validation error during user registration: {e.errors()} from {request.remote_addr}")
        return jsonify(e.errors()), 400

    db = get_db()
    try:
        new_user = user_queries.create_user(db, user_create_data)
        current_app.logger.info(f"User '{new_user.username}' registered successfully from {request.remote_addr}.")
        return jsonify(UserInDB.model_validate(new_user).model_dump()), 201
    except sqlite3.IntegrityError: # Username already exists
        db.rollback()
        current_app.logger.warning(f"Attempt to register existing username '{user_create_data.username}' from {request.remote_addr}.")
        return make_error_response("Username already exists", 409) # Caught by 409 handler or direct
    except Exception as e:
        db.rollback()
        current_app.logger.error(f"Error registering user '{user_create_data.username}': {e}", exc_info=True)
        return make_error_response("Failed to register user", 500) # Caught by 500 handler

@app.route('/api/auth/login', methods=['POST'])
def login_user():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return make_error_response("Username and password required", 400)

    db = get_db()
    user_row = user_queries.get_user_row_by_username(db, username)

    if user_row and check_password_hash(user_row['password_hash'], password):
        user_for_token = UserInDB.model_validate(user_row)
        access_token = create_access_token(identity=user_for_token.id)
        current_app.logger.info(f"User '{username}' logged in successfully from {request.remote_addr}.")
        return jsonify(access_token=access_token), 200
    else:
        current_app.logger.warning(f"Failed login attempt for username '{username}' from {request.remote_addr}.")
        return make_error_response("Invalid username or password", 401)

# --- Gear CRUD API Endpoints (Protected) ---
@app.route('/api/gear', methods=['POST'])
@jwt_required()
def create_gear_item_api():
    try:
        gear_data = GearCreate(**request.json)
    except ValidationError as e:
        current_app.logger.warning(f"Validation error creating gear: {e.errors()} by user {get_jwt_identity_if_available()} from {request.remote_addr}")
        return jsonify(e.errors()), 400 # Pydantic errors are fine as is
    
    db = get_db()
    try:
        created_gear = gear_queries.create_gear(db, gear_data)
        current_app.logger.info(f"Gear item '{created_gear.name}' created by user {get_jwt_identity_if_available()}.")
        return jsonify(created_gear.model_dump()), 201
    except sqlite3.IntegrityError as e:
        db.rollback()
        current_app.logger.error(f"Integrity error creating gear '{gear_data.name}': {e}", exc_info=True)
        if "FOREIGN KEY constraint failed" in str(e):
            return make_error_response("Invalid location_id or other foreign key constraint failed.", 400, details=str(e))
        return make_error_response(f"Database integrity error: {str(e)}", 400)
    except Exception as e: 
        db.rollback()
        current_app.logger.error(f"Unexpected error creating gear '{gear_data.name}': {e}", exc_info=True)
        return make_error_response("Failed to create gear item", 500)

@app.route('/api/gear', methods=['GET'])
@jwt_required()
def get_all_gear_api():
    db = get_db()
    name_filter = request.args.get('name')
    category_filter = request.args.get('category')

    gear_list = gear_queries.get_all_gear(db, name_filter, category_filter)
    return jsonify([gear.model_dump() for gear in gear_list])

@app.route('/api/gear/<int:gear_id>', methods=['GET'])
@jwt_required()
def get_gear_item_api(gear_id):
    db = get_db()
    gear_item = gear_queries.get_gear_by_id(db, gear_id)
    if gear_item is None:
        abort(404, description=f"Gear item with id {gear_id} not found")
    return jsonify(gear_item.model_dump()), 200

@app.route('/api/gear/<int:gear_id>', methods=['PUT'])
@jwt_required()
def update_gear_item_api(gear_id):
    try:
        update_data = GearUpdate(**request.json)
    except ValidationError as e:
        return jsonify(e.errors()), 400

    if not update_data.model_dump(exclude_unset=True):
        return make_error_response("No update fields provided", 400)

    db = get_db()
    try:
        updated_gear = gear_queries.update_gear(db, gear_id, update_data)
        if updated_gear is None:
            abort(404, description=f"Gear item with id {gear_id} not found for update") # Will be caught by 404 handler
        return jsonify(updated_gear.model_dump()), 200
    except sqlite3.IntegrityError as e:
        db.rollback()
        current_app.logger.error(f"Integrity error updating gear {gear_id}: {e}", exc_info=True)
        if "FOREIGN KEY constraint failed" in str(e):
             return make_error_response("Invalid location_id or other foreign key constraint failed.", 400, details=str(e))
        return make_error_response(f"Database integrity error: {str(e)}", 400)
    except Exception as e:
        db.rollback()
        current_app.logger.error(f"Unexpected error updating gear {gear_id}: {e}", exc_info=True)
        return make_error_response("Failed to update gear item", 500)

@app.route('/api/gear/<int:gear_id>', methods=['PATCH'])
@jwt_required()
def patch_gear_item_api(gear_id):
    try:
        patch_data = GearUpdate(**request.json)
    except ValidationError as e:
        current_app.logger.error(f"Validation error patching gear {gear_id}: {e.errors()}")
        return jsonify(e.errors()), 400

    if not patch_data.model_dump(exclude_unset=True):
        return make_error_response("No update fields provided", 400)
    
    db = get_db()
    try:
        updated_gear = gear_queries.update_gear(db, gear_id, patch_data)
        if updated_gear is None:
             abort(404, description=f"Gear item with id {gear_id} not found for patch") # Will be caught by 404 handler
        return jsonify(updated_gear.model_dump()), 200
    except sqlite3.IntegrityError as e:
        db.rollback()
        current_app.logger.error(f"Integrity error patching gear {gear_id}: {e}", exc_info=True)
        if "FOREIGN KEY constraint failed" in str(e):
             return make_error_response("Invalid location_id or other foreign key constraint failed.", 400, details=str(e))
        return make_error_response(f"Database integrity error: {str(e)}", 400)
    except Exception as e:
        db.rollback()
        current_app.logger.error(f"Unexpected error patching gear {gear_id}: {e}", exc_info=True)
        return make_error_response("Failed to patch gear item", 500)

@app.route('/api/gear/<int:gear_id>', methods=['DELETE'])
@jwt_required()
def delete_gear_item_api(gear_id):
    db = get_db()
    try:
        deleted = gear_queries.delete_gear(db, gear_id)
        if not deleted:
            abort(404, description=f"Gear item with id {gear_id} not found for deletion") # Will be caught by 404 handler
        current_app.logger.info(f"Gear item with id {gear_id} deleted by user {get_jwt_identity_if_available()}.")
        return jsonify({"message": f"Gear item with id {gear_id} deleted successfully"}), 200
    except sqlite3.IntegrityError as e:
        db.rollback()
        current_app.logger.error(f"Integrity error deleting gear {gear_id}: {e}", exc_info=True)
        return make_error_response(f"Database integrity error during deletion: {str(e)}", 400)
    except Exception as e: 
        db.rollback()
        current_app.logger.error(f"Error deleting gear {gear_id}: {e}", exc_info=True)
        return make_error_response("Failed to delete gear item", 500)

# --- Location API Endpoints ---

@app.route('/api/locations', methods=['POST'])
@jwt_required()
def create_location_api():
    try:
        location_data = LocationCreate(**request.json)
    except ValidationError as e:
        current_app.logger.error(f"Validation error creating location: {e.errors()}")
        return jsonify(e.errors()), 400

    db = get_db()
    try:
        created_location = location_queries.create_location(db, location_data)
        current_app.logger.info(f"Location '{created_location.name}' created by user {get_jwt_identity_if_available()}.")
        return jsonify(created_location.model_dump()), 201
    except sqlite3.IntegrityError as e:
        db.rollback()
        current_app.logger.error(f"Integrity error creating location '{location_data.name}': {e}", exc_info=True)
        if "UNIQUE constraint failed: locations.name" in str(e):
            return make_error_response("Location name already exists", 409, details=str(e))
        if "FOREIGN KEY constraint failed" in str(e):
            return make_error_response("Invalid parent_id or other foreign key constraint failed", 400, details=str(e))
        return make_error_response(f"Database integrity error: {str(e)}", 400)
    except Exception as e:
        db.rollback()
        current_app.logger.error(f"Unexpected error creating location '{location_data.name}': {e}", exc_info=True)
        return make_error_response("Failed to create location", 500)

@app.route('/api/locations', methods=['GET'])
@jwt_required()
def get_all_locations_api():
    db = get_db()
    name_filter = request.args.get('name')
    type_filter = request.args.get('type')

    locations = location_queries.get_all_locations(db, name_filter, type_filter)
    return jsonify([loc.model_dump() for loc in locations])

@app.route('/api/locations/<int:location_id>', methods=['GET'])
@jwt_required()
def get_location_item_api(location_id):
    db = get_db()
    location_item = location_queries.get_location_by_id(db, location_id)
    if location_item is None:
        abort(404, description=f"Location with id {location_id} not found")
    return jsonify(location_item.model_dump())

@app.route('/api/locations/<int:location_id>', methods=['PUT'])
@jwt_required()
def update_location_api(location_id):
    try:
        update_data = LocationUpdate(**request.json)
    except ValidationError as e:
        current_app.logger.error(f"Validation error updating location {location_id}: {e.errors()}")
        return jsonify(e.errors()), 400

    if not update_data.model_dump(exclude_unset=True):
        return make_error_response("No update fields provided", 400)

    if update_data.parent_id is not None and update_data.parent_id == location_id:
        return make_error_response("Location cannot be its own parent", 400)

    db = get_db()
    try:
        updated_location = location_queries.update_location(db, location_id, update_data)
        if updated_location is None:
            abort(404, description=f"Location with id {location_id} not found for update") # Caught by 404 handler
        return jsonify(updated_location.model_dump()), 200
    except sqlite3.IntegrityError as e:
        db.rollback()
        current_app.logger.error(f"Integrity error updating location {location_id}: {e}", exc_info=True)
        if "UNIQUE constraint failed: locations.name" in str(e):
            return make_error_response("Location name already exists", 409, details=str(e))
        if "FOREIGN KEY constraint failed" in str(e):
            return make_error_response("Invalid parent_id or other foreign key constraint failed", 400, details=str(e))
        return make_error_response(f"Database integrity error: {str(e)}", 400)
    except Exception as e:
        db.rollback()
        current_app.logger.error(f"Unexpected error updating location {location_id}: {e}", exc_info=True)
        return make_error_response("Failed to update location", 500)

@app.route('/api/locations/<int:location_id>', methods=['PATCH'])
@jwt_required()
def patch_location_api(location_id):
    try:
        patch_data = LocationUpdate(**request.json)
    except ValidationError as e:
        current_app.logger.error(f"Validation error patching location {location_id}: {e.errors()}")
        return jsonify(e.errors()), 400

    if not patch_data.model_dump(exclude_unset=True):
        return make_error_response("No update fields provided", 400)

    if patch_data.parent_id is not None and patch_data.parent_id == location_id:
        return make_error_response("Location cannot be its own parent", 400)

    db = get_db()
    try:
        updated_location = location_queries.update_location(db, location_id, patch_data)
        if updated_location is None:
            abort(404, description=f"Location with id {location_id} not found for patch") # Caught by 404 handler
        return jsonify(updated_location.model_dump()), 200
    except sqlite3.IntegrityError as e:
        db.rollback()
        current_app.logger.error(f"Integrity error patching location {location_id}: {e}", exc_info=True)
        if "UNIQUE constraint failed: locations.name" in str(e):
            return make_error_response("Location name already exists", 409, details=str(e))
        if "FOREIGN KEY constraint failed" in str(e):
            return make_error_response("Invalid parent_id or other foreign key constraint failed", 400, details=str(e))
        return make_error_response(f"Database integrity error: {str(e)}", 400)
    except Exception as e:
        db.rollback()
        current_app.logger.error(f"Unexpected error patching location {location_id}: {e}", exc_info=True)
        return make_error_response("Failed to patch location", 500)

@app.route('/api/locations/<int:location_id>', methods=['DELETE'])
@jwt_required()
def delete_location_api(location_id):
    db = get_db()
    try:
        deleted = location_queries.delete_location(db, location_id)
        if not deleted:
            abort(404, description=f"Location with id {location_id} not found for deletion") # Caught by 404 handler
        current_app.logger.info(f"Location with id {location_id} deleted by user {get_jwt_identity_if_available()}.")
        return jsonify({"message": f"Location with id {location_id} deleted successfully"}), 200
    except sqlite3.IntegrityError as e:
        db.rollback()
        current_app.logger.error(f"Integrity error deleting location {location_id}: {e}", exc_info=True)
        return make_error_response(f"Database integrity error during deletion: {str(e)}", 400)
    except Exception as e:
        db.rollback()
        current_app.logger.error(f"Unexpected error deleting location {location_id}: {e}", exc_info=True)
        return make_error_response("Failed to delete location", 500)

@app.route('/api/locations/<int:location_id>/items', methods=['GET'])
@jwt_required()
def get_items_in_location_api(location_id):
    db = get_db()
    # location_queries.get_items_in_location will return None if the location itself doesn't exist.
    items_in_location = location_queries.get_items_in_location(db, location_id)
    
    if items_in_location is None:
        abort(404, description=f"Location with id {location_id} not found when trying to list items.") # Caught by 404 handler

    return jsonify([item.model_dump() for item in items_in_location])

@app.route('/api/test')
def api_test():
    # A simple helper to get current user identity if available, for logging or other non-critical uses.
    # Not for security decisions.
    user_identity = get_jwt_identity_if_available()
    current_app.logger.debug(f"/api/test accessed by {user_identity if user_identity else 'anonymous user'}")
    return {"message": "Flask API is running!"}

# Helper to get identity if available, otherwise return 'anonymous' or system
def get_jwt_identity_if_available():
    try:
        return get_jwt_identity()
    except Exception: # Broad exception to catch if not in JWT context or if get_jwt_identity() fails
        return "anonymous_or_system_context"

# --- Logging Configuration ---
import logging

if not app.config['DEBUG']:
    # Basic configuration for production logging
    # For a real production app, consider more advanced logging like JSON formatter,
    # logging to a file, or integrating with a logging service.
    # Note: Flask's default logger is 'flask.app'. Werkzeug also logs.
    # This basicConfig will configure the root logger.
    # If you want to specifically configure Flask's app logger:
    # flask_logger = logging.getLogger('flask.app')
    # flask_logger.setLevel(logging.INFO)
    # For simplicity, basicConfig is used here.
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s %(levelname)s %(name)s %(process)d %(threadName)s : %(message)s')
else:
    # When DEBUG is True, Flask's default logger is usually quite good (logs to console at DEBUG level).
    # You can still customize it if needed.
    # Example: To see more verbose SQLAlchemy logs if it were used:
    # logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)
    pass


if __name__ == '__main__':
    with app.app_context(): 
        init_db() 
    # Use DEBUG from app.config for app.run(), accessed via current_app
    app.run(debug=current_app.config['DEBUG'], port=5000)

# --- Custom Error Handlers (ensure they are defined after make_error_response) ---
@app.errorhandler(404)
def handle_404_error(e):
    message = e.description if hasattr(e, 'description') and e.description else "Resource not found"
    current_app.logger.warning(f"404 Not Found: {request.path} (User: {get_jwt_identity_if_available()}) - Message: {message}")
    return make_error_response(message, 404)

@app.errorhandler(500)
def handle_500_error(e):
    original_exception = getattr(e, 'original_exception', e)
    current_app.logger.error(f"Unhandled exception for path {request.path} (User: {get_jwt_identity_if_available()}): {original_exception}", exc_info=True)
    return make_error_response("Internal server error", 500)

@app.errorhandler(400)
def handle_400_error(e):
    message = e.description if hasattr(e, 'description') and e.description else "Bad request"
    current_app.logger.warning(f"400 Bad Request: {request.path} (User: {get_jwt_identity_if_available()}) - Message: {message}")
    return make_error_response(message, 400)

@app.errorhandler(409)
def handle_409_error(e):
    message = e.description if hasattr(e, 'description') and e.description else "Conflict"
    current_app.logger.warning(f"409 Conflict: {request.path} (User: {get_jwt_identity_if_available()}) - Message: {message}")
    return make_error_response(message, 409)

@app.errorhandler(405)
def handle_405_error(e):
    message = e.description if hasattr(e, 'description') and e.description else "Method not allowed"
    current_app.logger.warning(f"405 Method Not Allowed: {request.method} {request.path} (User: {get_jwt_identity_if_available()}) - Message: {message}")
    return make_error_response(message, 405)

# It's generally good practice to register generic Exception handler as a last resort,
# but Flask's 500 handler usually catches unhandled exceptions.
# @app.errorhandler(Exception)
# def handle_generic_exception(e):
#     current_app.logger.error(f"Unhandled generic exception: {e}", exc_info=True)
#     return make_error_response("An unexpected error occurred", 500)
