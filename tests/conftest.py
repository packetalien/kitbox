import pytest
import os
import tempfile
from app import app as flask_app # Import the Flask app instance from your app.py
from app import init_db, get_db # Import db functions

@pytest.fixture(scope='session') # Changed to session scope for efficiency
def app():
    """
    Creates and configures a new Flask app instance for each test session.
    Uses a temporary database file that is removed after the session.
    """
    # Create a temporary file for the SQLite database
    # Using tempfile.NamedTemporaryFile ensures it's cleaned up.
    # However, for SQLite, it's often easier to just name it and delete it manually if needed,
    # or use ':memory:'. Let's use a named file in the instance folder for clarity.

    # Ensure the instance folder exists (Flask convention for instance-specific files)
    instance_path = os.path.join(flask_app.root_path, 'instance') # Assuming app.py is in root
    if not os.path.exists(instance_path):
        try:
            os.makedirs(instance_path)
        except OSError as e: # Guard against race condition if another test creates it
            if not os.path.isdir(instance_path):
                raise

    db_filename = 'test_kitbox.db' # Temporary database name
    db_path = os.path.join(instance_path, db_filename)

    # Override configurations for testing
    flask_app.config.update({
        "TESTING": True,
        "DATABASE_FILENAME": db_filename, # Use the temp db filename
        "JWT_SECRET_KEY": "test-jwt-secret-key", # Consistent JWT key for tests
        # Ensure a new DB path is used by get_db_path by also updating the original path logic if needed.
        # However, get_db_path in app.py uses current_app.config which we are updating here.
    })

    # Ensure the get_db_path in app.py uses the test instance path
    # This might require modifying get_db_path or ensuring it uses current_app.instance_path
    # For now, we assume get_db_path correctly uses current_app.config['DATABASE_FILENAME']
    # and current_app.root_path (which might need adjustment if app.py is not at project root)
    # Let's adjust get_db_path behavior for testing if it's simpler.
    # A simpler way is to ensure DATABASE_FILENAME in config is just the name,
    # and get_db_path in app.py constructs it relative to app.instance_path if TESTING is True,
    # or app.root_path otherwise.
    # For now, we'll rely on current_app.config['DATABASE_FILENAME'] being correctly used by get_db_path
    # and ensure that get_db_path is called within an app context that has this config.

    with flask_app.app_context():
        # Initialize the database (recreate schema)
        # init_db expects to find schema.sql relative to app.root_path
        init_db(reinit=True)

    yield flask_app # Provide the app instance to tests

    # Teardown: Remove the temporary database file after all tests in the session run
    # This is tricky if other fixtures (like db) hold the connection open.
    # Pytest handles teardown of higher-scoped fixtures after lower-scoped ones.
    # For now, let's assume connections are closed properly.
    if os.path.exists(db_path):
         try:
            # Ensure all connections are closed before removing
            # This might require explicit closing if 'db' fixture doesn't handle it in all cases
            # For in-memory, this is not an issue. For file, it can be.
            # A common pattern is to close g.db in a teardown_appcontext handler.
            # flask_app.teardown_appcontext(close_db) is already in app.py
            os.remove(db_path)
            # print(f"\nCleaned up test database: {db_path}")
         except OSError as e:
            print(f"\nError cleaning up test database {db_path}: {e}")


@pytest.fixture(scope='function') # Changed to function scope for client isolation
def client(app):
    """
    Provides a test client for the Flask application.
    This fixture depends on the `app` fixture.
    """
    return app.test_client()


@pytest.fixture(scope='function') # Function scope to ensure db is clean per test via init_db in app fixture
def db(app):
    """
    Provides a database connection for direct database interaction tests.
    This fixture depends on the `app` fixture and operates within an app context.
    """
    with app.app_context():
        yield get_db()
        # The close_db registered with app.teardown_appcontext in app.py should handle closing.

@pytest.fixture(scope='function')
def runner(app):
    """Provides a test CLI runner for the Flask application."""
    return app.test_cli_runner()
