# KitBox - Equipment Management Application

KitBox is a web application designed to help users manage equipment, primarily for contexts like tabletop roleplaying games. It features a master equipment list, a paperdoll interface to visualize equipped items, and management of items within containers like backpacks.

This version is implemented with a **Python Flask backend API**, a **JavaScript-driven frontend**, and **Nginx** as the web server and reverse proxy.

## Features

*   **User Authentication:** Secure login and registration.
*   **Master Equipment List:** View, add, edit, and delete all available gear items. Includes details like name, description, weight, cost, value, legality, category, and current location.
*   **Paperdoll Interface:** Visually represent character equipment on a paperdoll with designated slots (Head, Torso, Hands, etc.).
*   **Container Management:** Manage items within containers (e.g., Backpack, Pouch). View contents, total weight, and total value for each container. Add items from the master list to containers, or remove them.
*   **Dynamic UI:** The frontend is built with vanilla JavaScript, interacting with the backend API to provide a responsive user experience.
*   **Parchment Theme:** A medieval parchment-style user interface.

## Tech Stack

*   **Backend API:** Python (Flask), Pydantic (for data validation)
*   **Database:** SQLite
*   **Frontend:** HTML, Tailwind CSS, JavaScript (Vanilla JS)
*   **Web Server / Reverse Proxy:** Nginx
*   **WSGI Server:** Gunicorn (for running the Flask API)

## Project Structure

*   `app.py`: The main Flask application file, now primarily serving as the backend API.
*   `frontend/`: Directory containing all frontend assets.
    *   `frontend/index.html`: Login/Registration page, and entry point for the application.
    *   `frontend/master_list.html`: HTML for the master equipment list page.
    *   `frontend/paperdoll.html`: HTML for the paperdoll interface page.
    *   `frontend/containers.html`: HTML for the container contents page.
    *   `frontend/js/`: Contains JavaScript modules (`api.js`, `auth.js`, `master_list.js`, etc.).
    *   `frontend/css/`: Contains custom CSS (`style.css`).
*   `src/`: Contains Python source code for the backend.
    *   `src/data_access/`: Python modules for database query logic.
    *   `src/database/schema.sql`: SQL script to initialize the SQLite database schema and some default data.
*   `kitbox.db`: The SQLite database file (will be created when the backend app is initialized).
*   `requirements.txt`: Python dependencies for the backend.
*   `nginx.conf`: Example Nginx configuration file.
*   `INSTALL.md`: Detailed setup and installation instructions.

## Setup and Running the Application

For detailed setup and instructions on how to run the application with Nginx and Gunicorn, please refer to **INSTALL.md**.

A brief overview involves:
1.  Setting up the Python backend (installing dependencies, initializing the database).
2.  Running the Flask API using Gunicorn.
3.  Configuring Nginx to serve the `frontend/` directory and proxy API calls to Gunicorn.

## API Endpoints (Brief Overview)

The application provides several API endpoints for managing data. These are consumed by the JavaScript frontend. All data is exchanged in JSON format. Authentication is handled via JWT.

*   **Auth:**
    *   `POST /api/auth/register`: Register a new user.
    *   `POST /api/auth/login`: Log in a user, returns JWT.
*   **Gear:**
    *   `GET /api/gear`: List all gear items. Supports filtering by `name` and `category`.
    *   `POST /api/gear`: Create a new gear item.
    *   `GET /api/gear/<id>`: Get a specific gear item.
    *   `PUT /api/gear/<id>`: Update a specific gear item.
    *   `DELETE /api/gear/<id>`: Delete a specific gear item.
*   **Locations:**
    *   `GET /api/locations`: List all locations (body slots, containers). Supports filtering by `name` and `type`.
    *   `POST /api/locations`: Create a new location.
    *   `GET /api/locations/<id>`: Get a specific location.
    *   `PUT /api/locations/<id>`: Update a specific location.
    *   `DELETE /api/locations/<id>`: Delete a specific location.
    *   `GET /api/locations/<id>/items`: List all items within a specific location (container).

## Development Notes
*   The frontend uses Tailwind CSS for styling, loaded via CDN, and includes custom styles in `frontend/css/style.css` for the parchment theme.
*   JavaScript modules in `frontend/js/` handle API interactions, DOM manipulation, and application logic for each page.
*   The Flask backend API uses Pydantic for request validation and data serialization.
*   The application is designed to be run with Nginx acting as a reverse proxy and static file server.
*   Ensure `JWT_SECRET_KEY` environment variable is set to a strong, random secret in production.
*   The `kitbox.db` SQLite database file will be created in the project root by default when the Flask app initializes it. The path can be configured via environment variables (see `config.py`).
