# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container at /app
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
# Using --no-cache-dir to reduce layer size
# Using --upgrade pip to ensure pip is up to date before installing packages
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code into the container at /app
# Ensure .dockerignore is properly set up to exclude unnecessary files
COPY . .

# Make port 8000 available to the world outside this container
# Gunicorn will run on this port by default internally as specified in CMD
EXPOSE 8000

# Define environment variables that can be used by the application
# These are examples and can be overridden at runtime.
# For production, crucial variables like JWT_SECRET_KEY and database connection details
# should be set securely via the runtime environment (e.g., Docker run -e, K8s secrets, etc.).
ENV FLASK_APP=app.py
ENV FLASK_DEBUG=False
# Note: FLASK_DEBUG should ideally be False for production.
# The config.py defaults to True if FLASK_DEBUG env var is not set,
# so explicitly setting it to False here for the production image is good practice.

# Command to run the application using Gunicorn
# Number of workers can be adjusted based on CPU cores (e.g., typical formula is 2 * num_cores + 1)
# Binding to 0.0.0.0 makes the application accessible from outside the container if the port is mapped.
CMD ["gunicorn", "--workers", "4", "--bind", "0.0.0.0:8000", "app:app"]
