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
    This project uses a `requirements.txt` file to manage dependencies. Install them using pip:
    ```bash
    pip install -r requirements.txt
    ```

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

## Deployment

This section describes how to deploy the KitBox application to a server.

### Manual Deployment (Initial Server Setup)

A `deploy.sh` script is provided to automate the initial setup of the KitBox application on a fresh Ubuntu 24.04 server. This script will:

1.  Update system packages.
2.  Install Nginx, Python 3, pip, and virtual environment tools.
3.  Create a dedicated application user (`kitboxapp`).
4.  Set up the application directory (`/var/www/kitbox`).
5.  Create a Python virtual environment.
6.  Install Python dependencies (Flask, Pydantic, Gunicorn).
7.  Configure and start a Gunicorn systemd service to run the Flask application.
8.  Configure Nginx as a reverse proxy to Gunicorn.
9.  Optionally, configure UFW (Uncomplicated Firewall) to allow HTTP/HTTPS traffic.

**Steps to use `deploy.sh`:**

1.  **Transfer Script and Application Files:**
    *   Copy the `deploy.sh` script to your Ubuntu server.
    *   Copy your entire KitBox application project (or clone it from your Git repository) to a temporary location on the server (e.g., `/tmp/kitbox_source`). The `deploy.sh` script currently assumes it's run from the project root and copies files from there. You might need to adjust paths in the script or ensure it's run from the correct directory containing all project files (`app.py`, `requirements.txt`, HTML files, `src/` directory, etc.).

2.  **Make `deploy.sh` Executable:**
    ```bash
    chmod +x deploy.sh
    ```

3.  **Run the Script:**
    Execute the script with `sudo` (as it performs system-level installations and configurations):
    ```bash
    sudo ./deploy.sh
    ```
    The script will prompt for any necessary password confirmations for `sudo` operations.

4.  **Post-Deployment:**
    *   After the script completes, your application should be accessible via the server's IP address or domain name (if configured).
    *   The Gunicorn service (`kitbox.service`) will manage the application process and ensure it runs on boot.
    *   Nginx will serve as the front-end web server, proxying requests to Gunicorn.

**Important Notes for `deploy.sh`:**
*   Review the variables at the top of `deploy.sh` (like `APP_USER`, `APP_DIR`) and adjust if necessary before running.
*   The script is designed for an initial setup. If you re-run it, some steps are idempotent (safe to run multiple times), but others (like user creation) might output warnings if the resource already exists.
*   The script attempts to copy application files from the directory where it is executed. Ensure all necessary project files (`app.py`, `requirements.txt`, HTML files, `src/` etc.) are present in that location relative to the script.
*   The database `kitbox.db` will be created in the application directory (`/var/www/kitbox`) and initialized by the Flask application on its first run.

### CI/CD with GitHub Actions

This project includes a GitHub Actions workflow defined in `.github/workflows/main.yml` to automate the continuous integration and deployment process.

**Pipeline Overview:**

1.  **Trigger:** The workflow automatically triggers on every push to the `main` branch.
2.  **Lint & Test (`lint-and-test` job):**
    *   Checks out the latest code.
    *   Sets up the specified Python environment.
    *   Installs project dependencies from `requirements.txt`.
    *   Runs Flake8 to lint the Python codebase. (Actual tests can be added to this job in the future).
3.  **Deploy (`deploy` job):**
    *   This job runs only if the `lint-and-test` job is successful and the push is to the `main` branch.
    *   It securely connects to the deployment server using SSH.
    *   On the server, it performs the following actions:
        *   Navigates to the application directory (e.g., `/var/www/kitbox`).
        *   Pulls the latest changes from the `main` branch of your Git repository.
        *   Activates the Python virtual environment.
        *   Installs or updates dependencies from `requirements.txt`.
        *   Restarts the Gunicorn systemd service (`kitbox.service`) to apply changes.

**Setup for CI/CD Deployment:**

To enable the automated deployment part of the CI/CD pipeline, you need to configure the following secrets in your GitHub repository settings (under `Settings` > `Secrets and variables` > `Actions`):

*   `SERVER_HOST`: The hostname or IP address of your deployment server.
*   `SERVER_USERNAME`: The username to use for SSH login to the server (this user should have `sudo` privileges to restart services, or the Gunicorn service restart command should be runnable without `sudo` for this user).
*   `SSH_PRIVATE_KEY`: The private SSH key that corresponds to an authorized public key on your server for the `SERVER_USERNAME`.
*   `SERVER_PORT` (Optional): The SSH port on your server if it's not the default port 22.

**Workflow Details:**

*   The `deploy.sh` script is intended for the *initial provisioning* of the server. The CI/CD pipeline handles *updates* to an already provisioned server.
*   Ensure the application user on the server (e.g., `kitboxapp`) has the necessary permissions to pull from the Git repository if you are deploying from a private repository (e.g., by setting up deploy keys).
*   The workflow uses `appleboy/ssh-action` to interact with the remote server.
