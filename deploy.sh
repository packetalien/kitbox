#!/bin/bash

# Exit immediately if a command exits with a non-zero status.
set -e

# Variables (customize if needed)
APP_USER="kitboxapp"
APP_DIR="/var/www/kitbox"
GIT_REPO_URL="https://github.com/your-username/your-repo-name.git" # Replace with actual repo URL if pulling from git
PROJECT_ROOT_FILES_TO_COPY=("app.py" "requirements.txt" "kitbox.db" "src/" "containers.html" "dynamic_containers.html" "dynamic_master_list.html" "dynamic_paperdoll.html" "master_list.html" "paperdoll.html" ".flaskenv" "LICENSE") # Add other files/dirs from root
VENV_DIR="${APP_DIR}/venv"
SOCKET_PATH="${APP_DIR}/kitbox.sock"
DB_NAME="kitbox.db"

echo "Starting KitBox deployment script..."

# --- System Update and Dependency Installation ---
echo "Updating system packages..."
sudo apt-get update
sudo apt-get upgrade -y

echo "Installing Nginx, Python, PIP, venv, SQLite..."
sudo apt-get install -y nginx python3 python3-pip python3-venv sqlite3

# --- Application User and Directory Setup ---
echo "Setting up application user and directory..."
if ! id -u ${APP_USER} >/dev/null 2>&1; then
    sudo useradd -r -s /bin/false ${APP_USER}
    echo "User ${APP_USER} created."
else
    echo "User ${APP_USER} already exists."
fi

sudo mkdir -p ${APP_DIR}

# --- Python Virtual Environment ---
echo "Setting up Python virtual environment at ${VENV_DIR}..."
sudo python3 -m venv ${VENV_DIR}

# --- Copy Application Files (Assuming script is run from project root) ---
# This section needs to be adapted if deploying from Git directly on server
echo "Copying application files to ${APP_DIR}..."
# Instead of rsync or git clone for this initial script, we'll assume files are copied manually or by CI
# For files expected to be in the project root:
for item in "${PROJECT_ROOT_FILES_TO_COPY[@]}"; do
    if [ -e "$item" ]; then
        sudo cp -R "$item" "${APP_DIR}/"
    else
        echo "Warning: $item not found in script execution directory."
    fi
done
# If your static/template files are within a subdirectory already copied (e.g. "src"), adjust as needed.

# --- Install Python Dependencies ---
echo "Installing Python dependencies..."
sudo ${VENV_DIR}/bin/pip install --upgrade pip
sudo ${VENV_DIR}/bin/pip install -r ${APP_DIR}/requirements.txt
sudo ${VENV_DIR}/bin/pip install gunicorn # Install Gunicorn here

# --- Set Ownership and Permissions ---
echo "Setting ownership and permissions..."
sudo chown -R ${APP_USER}:${APP_USER} ${APP_DIR}
sudo chmod -R 755 ${APP_DIR}
# Ensure the venv activate script is executable if needed by other scripts, though systemd won't directly use it.
# sudo chmod +x ${VENV_DIR}/bin/activate

# --- Initialize Database ---
echo "Initializing database (if ${DB_NAME} is empty or schema needs update)..."
# The app initializes the DB on first run if it doesn't exist.
# For explicit control or re-initialization, use flask init-db.
# This command should be run as the APP_USER if possible, or ensure APP_USER can write to the DB.
DB_PATH="${APP_DIR}/${DB_NAME}"
if [ -f "${DB_PATH}" ]; then
    echo "Database ${DB_PATH} already exists. Checking if it needs initialization by the app."
    # If the app handles schema creation on startup, this might be sufficient.
    # For explicit re-initialization:
    # sudo -u ${APP_USER} ${VENV_DIR}/bin/flask init-db
else
    echo "Database ${DB_PATH} not found. The application should create it on first run."
    # Or, to create it explicitly and ensure schema:
    # sudo -u ${APP_USER} ${VENV_DIR}/bin/flask --app ${APP_DIR}/app.py init-db
    # For now, we rely on the app's built-in init_db on startup.
    # Ensure the directory is writable by APP_USER for DB creation.
    sudo chown ${APP_USER}:${APP_USER} $(dirname "${DB_PATH}") # Ensure parent dir is writable if DB doesn't exist
fi
# Ensure the database file (and its directory) is writable by the app user
sudo chown ${APP_USER}:${APP_USER} ${APP_DIR} # Owning the app dir should cover it
# sudo chown ${APP_USER}:${APP_USER} ${DB_PATH} # If db exists
# sudo chmod 664 ${DB_PATH} # If db exists, allow read/write by user/group


# --- Gunicorn Systemd Service ---
echo "Setting up Gunicorn systemd service..."
SYSTEMD_SERVICE_FILE="/etc/systemd/system/kitbox.service"

sudo bash -c "cat > ${SYSTEMD_SERVICE_FILE}" << EOF
[Unit]
Description=Gunicorn instance to serve KitBox app
After=network.target

[Service]
User=${APP_USER}
Group=${APP_USER} # Or www-data if Nginx runs as www-data and needs to access socket
WorkingDirectory=${APP_DIR}
Environment="PATH=${VENV_DIR}/bin"
Environment="FLASK_APP=app.py" # Added FLASK_APP environment variable
ExecStart=${VENV_DIR}/bin/gunicorn --workers 3 --bind unix:${SOCKET_PATH} -m 007 app:app
Restart=always

[Install]
WantedBy=multi-user.target
EOF

echo "Reloading systemd, enabling and starting Gunicorn service..."
sudo systemctl daemon-reload
sudo systemctl enable kitbox.service
sudo systemctl start kitbox.service
sudo systemctl status kitbox.service --no-pager # Display status

# --- Nginx Configuration ---
echo "Configuring Nginx..."
NGINX_CONF_FILE="/etc/nginx/sites-available/kitbox"

sudo bash -c "cat > ${NGINX_CONF_FILE}" << EOF
server {
    listen 80;
    server_name _; # Replace with your domain or IP if available

    location / {
        include proxy_params;
        proxy_pass http://unix:${SOCKET_PATH};
    }

    # Add location block for static files if you create a dedicated static folder later
    # location /static {
    #     alias ${APP_DIR}/static;
    #     expires 30d;
    #     add_header Cache-Control "public, must-revalidate, proxy-revalidate";
    # }
}
EOF

echo "Enabling Nginx site configuration..."
if [ -L /etc/nginx/sites-enabled/default ]; then
    sudo rm /etc/nginx/sites-enabled/default
    echo "Removed default Nginx site."
fi
if [ ! -L /etc/nginx/sites-enabled/kitbox ]; then
    sudo ln -s ${NGINX_CONF_FILE} /etc/nginx/sites-enabled/kitbox
    echo "Enabled KitBox Nginx site."
else
    echo "KitBox Nginx site already enabled."
fi

echo "Testing Nginx configuration..."
sudo nginx -t

echo "Restarting Nginx..."
sudo systemctl restart nginx
sudo systemctl status nginx --no-pager # Display status

# --- Firewall (UFW) ---
# Check if ufw is active, then allow Nginx HTTP
if sudo ufw status | grep -q 'Status: active'; then
    echo "UFW is active. Allowing Nginx HTTP traffic..."
    sudo ufw allow 'Nginx Full' # Allows both HTTP and HTTPS
    sudo ufw allow 'OpenSSH' # Ensure SSH is allowed
    sudo ufw reload
    sudo ufw status
else
    echo "UFW is not active. Consider enabling it for security."
fi

echo "Deployment script finished."
echo "You should be able to access your app at http://<your_server_ip>"
echo "Ensure your Git repo URL is correctly set in the script if you plan to use it for cloning."
