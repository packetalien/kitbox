# KitBox Installation Guide

This guide provides instructions to set up and run the KitBox application, which consists of a Python Flask backend API and a JavaScript frontend, served by Nginx.

## Prerequisites

Before you begin, ensure you have the following installed:

*   **Python** (version 3.8 or higher recommended)
*   **pip** (Python package installer)
*   **Nginx** (web server)
*   **Gunicorn** (WSGI HTTP server for Python)
*   A tool to clone the repository, like `git`.

## 1. Clone the Repository

If you haven't already, clone the project repository to your local machine:

```bash
git clone <repository-url>
cd <repository-directory> # e.g., kitbox
```

## 2. Backend Setup (Flask API)

The backend is a Python Flask application.

### a. Create a Virtual Environment

It's highly recommended to use a Python virtual environment to manage dependencies.

```bash
python3 -m venv venv
```

Activate the virtual environment:
*   On macOS/Linux:
    ```bash
    source venv/bin/activate
    ```
*   On Windows:
    ```bash
    .\venv\Scripts\activate
    ```

### b. Install Python Dependencies

Install the required Python packages listed in `requirements.txt`:

```bash
pip install -r requirements.txt
```
If `requirements.txt` is missing, you can typically install the core dependencies with:
`pip install Flask pydantic python-dotenv Flask-JWT-Extended Werkzeug`
(Ensure `requirements.txt` is up-to-date in the project).

### c. Configure Environment Variables

The application uses environment variables for configuration. You can set these directly in your shell, or create a `.env` file in the project root directory.
Key environment variables (see `config.py` for defaults and more options):

*   `FLASK_APP=app.py` (Usually set for Flask CLI)
*   `FLASK_DEBUG=False` (Set to `True` for development, `False` for production with Gunicorn)
*   `JWT_SECRET_KEY`: **Crucial for security.** Set this to a strong, random string.
    Example for `.env` file:
    ```env
    FLASK_DEBUG=False
    JWT_SECRET_KEY='your-very-strong-and-secret-random-string-here'
    KITBOX_DATABASE_FILENAME='kitbox.db' # Default, can be changed
    ```
    *Note: The `.env` file is loaded by `python-dotenv` if you run the app directly with `flask run`. For Gunicorn, these variables should ideally be passed through the Gunicorn service or environment.*

### d. Initialize the Database

The application uses SQLite. The database schema and initial data are defined in `src/database/schema.sql`. To initialize (or re-initialize) the database, run the following Flask CLI command from the project root (with the virtual environment activated):

```bash
flask init-db
```
This will create/recreate the `kitbox.db` file (or the filename specified by `KITBOX_DATABASE_FILENAME`) in your project root.

## 3. Frontend Setup

The frontend consists of static HTML, CSS, and JavaScript files located in the `frontend/` directory. These files will be served directly by Nginx. No separate build step is required for the frontend as it's written in vanilla JavaScript and uses CDN for Tailwind CSS.

## 4. Nginx Configuration

Nginx will serve the static frontend files and act as a reverse proxy for the backend API (running via Gunicorn).

### a. Create/Edit Nginx Configuration File

An example Nginx configuration is provided in `nginx.conf` in the project root. You'll need to adapt this and place it in your Nginx configuration directory. This is typically `/etc/nginx/sites-available/`.

1.  Copy or adapt `nginx.conf` to your Nginx setup. For example:
    ```bash
    sudo cp nginx.conf /etc/nginx/sites-available/kitbox
    ```

2.  **Modify the configuration file** (`/etc/nginx/sites-available/kitbox`):
    *   **`root` directive:** Change `/usr/src/app/frontend` to the absolute path of the `frontend` directory within your cloned project.
        For example, if you cloned KitBox to `/var/www/kitbox`, the root should be `/var/www/kitbox/frontend`.
    *   **`server_name`:** Change `_` to your server's domain name or IP address if applicable (e.g., `kitbox.example.com` or `localhost` if testing locally).
    *   Ensure the `proxy_pass http://127.0.0.1:5000;` line points to the address and port Gunicorn will use.

    Example snippet from the Nginx server block:
    ```nginx
    server {
        listen 80;
        server_name your_domain_or_ip; # e.g., localhost or kitbox.example.com

        root /path/to/your/project/frontend; # IMPORTANT: Update this path

        index index.html;

        location / {
            try_files $uri $uri/ /index.html;
        }

        location /api/ {
            proxy_pass http://127.0.0.1:5000; # Gunicorn's address
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }
    }
    ```

### b. Enable the Site and Test Nginx Configuration

1.  Create a symbolic link from `sites-available` to `sites-enabled`:
    ```bash
    sudo ln -s /etc/nginx/sites-available/kitbox /etc/nginx/sites-enabled/
    ```
    (Remove the default site if it conflicts: `sudo rm /etc/nginx/sites-enabled/default`)

2.  Test your Nginx configuration for syntax errors:
    ```bash
    sudo nginx -t
    ```

3.  If the test is successful, reload or restart Nginx:
    ```bash
    sudo systemctl reload nginx
    # or
    sudo systemctl restart nginx
    ```

## 5. Running the Application

### a. Start the Backend API with Gunicorn

From your project's root directory (with the virtual environment activated and environment variables like `JWT_SECRET_KEY` set):

```bash
gunicorn --workers 4 --bind 127.0.0.1:5000 app:app
```

*   `--workers 4`: Adjust the number of worker processes based on your server's CPU cores.
*   `--bind 127.0.0.1:5000`: Gunicorn will listen on localhost port 5000. This matches the `proxy_pass` directive in the Nginx configuration.
*   `app:app`: Tells Gunicorn to use the `app` instance from the `app.py` file.

For a production setup, you would typically run Gunicorn as a systemd service.

### b. Access the Application

Once Nginx and Gunicorn are running, open your web browser and navigate to the address you configured for Nginx (e.g., `http://localhost` or `http://your_domain_or_ip`).

You should see the KitBox login page.

## Environment Variables Summary

*   **`FLASK_DEBUG`**: (Default: `True`) Set to `False` for production. Controls Flask's debug mode.
*   **`DATABASE_FILENAME`**: (Default: `kitbox.db`) Filename for the SQLite database.
*   **`JWT_SECRET_KEY`**: (Default: `your-default-dev-jwt-secret-key-CHANGE-THIS-IN-PROD`) **MUST be changed to a strong, unique secret for production.** Used for signing JWTs.

These can be set in your shell environment, a `.env` file (if running `flask run` or your Gunicorn service loads it), or through systemd service files for Gunicorn.

## Troubleshooting

*   **502 Bad Gateway from Nginx:**
    *   Gunicorn is likely not running or not accessible at `127.0.0.1:5000`. Check Gunicorn logs.
    *   Ensure `proxy_pass` in Nginx matches Gunicorn's bind address.
*   **404 Not Found for static files (CSS, JS, images):**
    *   The `root` path in your Nginx configuration is incorrect. Double-check it points to the `frontend` directory.
    *   File permissions issues for the `frontend` directory or its contents.
*   **API calls failing (40x, 50x errors in browser console):**
    *   Check Gunicorn logs for backend errors.
    *   Ensure the API endpoints are correct and the backend is functioning.
*   **Permission Denied errors (Nginx or Gunicorn logs):**
    *   Nginx user (e.g., `www-data`) might not have read access to the `frontend` directory.
    *   The user running Gunicorn might not have write access to the directory where `kitbox.db` is located (or to the DB file itself).

This guide should help you get KitBox up and running. Enjoy managing your gear!
