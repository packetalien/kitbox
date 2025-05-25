# KitBox - Equipment Management Application

KitBox is a web application designed to help users manage equipment for tabletop roleplaying games. It features a master equipment list, a paperdoll interface to visualize equipped items, and management of items within containers like backpacks.

This version is implemented with a Python Flask backend and an HTML/JavaScript frontend, adapted from an original concept for an Electron application.

## Features

*   **Master Equipment List:** View, add, edit, and delete all available gear items. Includes details like name, description, weight, cost, value, legality, and current location.
*   **Paperdoll Interface:** Visually represent character equipment on a paperdoll with designated slots (Head, Torso, Hands, etc.).
*   **Container Management:** Manage items within containers (e.g., Backpack, Pouch). View contents, total weight, and total value for each container.
*   **Parchment Theme:** A medieval parchment-style user interface.

## Tech Stack

*   **Backend:** Python (Flask)
*   **Database:** SQLite
*   **Frontend:** HTML, Tailwind CSS, JavaScript
*   **Data Validation:** Pydantic (for Flask API)

## Project Structure

*   `app.py`: The main Flask application file containing backend logic, API endpoints, and routes to serve HTML pages.
*   `dynamic_master_list.html`: HTML page for the master equipment list.
*   `dynamic_paperdoll.html`: HTML page for the paperdoll interface.
*   `dynamic_containers.html`: HTML page for viewing container contents.
*   `src/database/schema.sql`: SQL script to initialize the SQLite database schema and some default data.
*   `kitbox.db`: The SQLite database file (will be created when the app is run/initialized).
*   `.flaskenv`: Environment variables for Flask CLI (optional, but recommended).

## Setup and Running the Application

1.  **Clone the Repository (if applicable):**
    ```bash
    # git clone <repository-url>
    # cd <repository-directory>
    ```

2.  **Create a Python Virtual Environment:**
    It's highly recommended to use a virtual environment.
    ```bash
    python -m venv venv
    ```
    Activate the virtual environment:
    *   On Windows:
        ```bash
        .\venv\Scripts\activate
        ```
    *   On macOS/Linux:
        ```bash
        source venv/bin/activate
        ```

3.  **Install Dependencies:**
    You will need Flask and Pydantic. You can install them using pip:
    ```bash
    pip install Flask Pydantic
    ```
    (Ideally, this project would have a `requirements.txt` file. You can create one after installing dependencies with `pip freeze > requirements.txt`)

4.  **Initialize the Database:**
    The application uses SQLite. The database schema and initial data are defined in `src/database/schema.sql`. To initialize (or re-initialize) the database, run the following Flask CLI command from the project root:
    ```bash
    flask init-db
    ```
    This will create a `kitbox.db` file in your project root if it doesn't exist, or recreate it if it does.

5.  **Run the Flask Application:**
    Once the database is initialized, you can run the Flask development server:
    ```bash
    flask run
    ```
    By default, this usually starts the server at `http://127.0.0.1:5000/`. Open this URL in your web browser.

    *   The main equipment list is at `/`
    *   The paperdoll view is at `/paperdoll`
    *   The container view is at `/containers?location_id=<ID>` (e.g., `/containers?location_id=18` to see the contents of the default "Backpack"). You can find location IDs by inspecting the `/api/locations` endpoint or by looking at the `location_id` of container items in the master list.

## API Endpoints (Brief Overview)

The application provides several API endpoints for managing data:

*   **Gear:**
    *   `GET /api/gear`: List all gear items.
    *   `POST /api/gear`: Create a new gear item.
    *   `GET /api/gear/<id>`: Get a specific gear item.
    *   `PUT /api/gear/<id>`: Update a specific gear item.
    *   `DELETE /api/gear/<id>`: Delete a specific gear item.
*   **Locations:**
    *   `GET /api/locations`: List all locations (body slots, containers).
    *   `GET /api/locations/<id>`: Get a specific location.
    *   `GET /api/locations/<id>/items`: List all items within a specific location (container).

These endpoints return JSON data and are used by the JavaScript in the HTML pages to provide dynamic functionality.

## Development Notes
*   The HTML pages use Tailwind CSS for styling and include custom styles for the parchment theme.
*   JavaScript is embedded in the HTML files to handle API interactions and DOM manipulation.
*   The application is designed to be run locally.
