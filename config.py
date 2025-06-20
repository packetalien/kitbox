import os
from dotenv import load_dotenv

# Load .env file if it exists, for local development environment variables
# This is useful if you prefer .env over .flaskenv or want to use it alongside.
# If .flaskenv is the primary method, this line is optional but doesn't hurt.
load_dotenv()

class Config:
    """
    Application configuration class.
    Settings are loaded from environment variables with sensible defaults for development.
    """

    # Flask debug mode
    # Defaults to True for development, should be False in production.
    DEBUG = os.environ.get('FLASK_DEBUG', 'True').lower() == 'true'

    # Database configuration
    # Just the filename, the full path will be constructed in app.py using app.root_path
    DATABASE_FILENAME = os.environ.get('KITBOX_DATABASE_FILENAME', 'kitbox.db')

    # JWT Secret Key
    # IMPORTANT: This is a default development key.
    # CHANGE THIS IN PRODUCTION to a strong, random, and secret key.
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'your-default-dev-jwt-secret-key-CHANGE-THIS-IN-PROD')

    # Example of another config variable if needed later
    # API_VERSION = os.environ.get('API_VERSION', 'v1')

# For direct import of the class: from config import Config
# Or for app.config.from_object('config.Config')
