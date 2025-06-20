# Kitbox Project Roadmap

## 1. Introduction

The goal of the Kitbox project is to evolve the existing application into a robust, full server-side web service and a feature-rich desktop application. This roadmap outlines the planned stages of development, from foundational backend enhancements to frontend integration and future feature development.

## 2. Completed Foundational Work (Summary)

The initial phase focused on building a solid backend and preparing for future development. Key achievements include:

-   **Enhanced RESTful API:** Implemented full CRUD operations for gear and locations, including PATCH for partial updates and basic filtering capabilities.
-   **Refactored Data Access Layer:** Database interaction logic has been separated from API route handlers into a dedicated data access layer (`src/data_access/`).
-   **JWT Authentication:** Basic JWT-based authentication and authorization have been implemented for API endpoints.
-   **Configuration Management:** Application settings (database, JWT secret, debug mode) are managed via `config.py` and environment variables.
-   **Improved Error Handling and Logging:** Standardized JSON error responses, implemented custom error handlers, and enhanced logging throughout the application.
-   **Initial Test Suite:** Developed automated tests using Pytest for the user data access layer, authentication API, and gear API endpoints.
-   **Dockerization Setup:** Created `Dockerfile`, `requirements.txt`, and `.dockerignore` to enable containerization of the application.
-   **API Documentation Strategy:** Outlined the approach for API documentation using OpenAPI and recommended `APIFlask` for future integration.

## 3. Short-Term Goals (Next 1-3 Months)

-   **API Documentation:**
    -   Choose and integrate an OpenAPI generation tool (**APIFlask** is highly recommended due to its Pydantic support).
    -   Thoroughly document all existing API endpoints (`/auth`, `/gear`, `/locations`), including request/response models (Pydantic schemas) and authentication schemes (JWT).
    -   Serve interactive API documentation (e.g., Swagger UI and/or ReDoc).
-   **Frontend - Initial API Integration:**
    -   Review and understand the existing frontend code in the `public/` directory.
    -   Implement JWT authentication handling in the frontend:
        -   Login and registration forms/logic.
        -   Secure storage of JWT tokens.
        -   Attaching tokens to authenticated API requests.
        -   Logout functionality.
    -   Adapt existing frontend JavaScript to correctly consume the enhanced backend API, including error handling and adapting to any changes in endpoint structure or response format.
-   **Production Database Setup (Initial):**
    -   Plan and execute the migration from SQLite to a production-grade relational database (e.g., PostgreSQL or MySQL) for development and staging environments.
    -   Update database connection logic in `app.py` / `config.py` to support the new database system (e.g., using environment variables for connection strings).
-   **CI/CD Pipeline (Basic):**
    -   Set up a basic Continuous Integration/Continuous Deployment pipeline (e.g., using GitHub Actions).
    -   Automate:
        -   Linting and static code analysis.
        -   Running the Pytest test suite.
        -   Building the Docker image.
        -   (Optional) Pushing the Docker image to a container registry.

## 4. Medium-Term Goals (3-6 Months)

-   **Advanced API Features:**
    -   Implement API pagination for `GET /api/gear` and `GET /api/locations` to handle large datasets.
    -   Add more sophisticated filtering and sorting options to list endpoints.
    -   Evaluate the need for user roles and permissions; if required, implement basic Role-Based Access Control (RBAC) for more granular API authorization.
-   **Frontend Enhancements:**
    -   Based on the initial API integration, improve the UI/UX for displaying, creating, and managing gear and locations.
    -   Implement frontend components for new API features (e.g., pagination controls, advanced filter UI).
    -   Evaluate the current vanilla JavaScript approach. If it becomes too cumbersome for planned features, begin planning and potentially start migration to a modern frontend framework (e.g., Vue.js, React, Svelte).
-   **Deployment to Staging/Production:**
    -   Choose a primary hosting platform for the containerized application (e.g., Google Cloud Run, AWS Fargate, or a small VPS with Docker).
    -   Deploy the application to a staging environment that mirrors production.
    -   Implement robust secrets management for production (JWT secret, database credentials, API keys) using environment variables injected by the hosting platform or a dedicated secrets management service.
    -   After thorough testing in staging, deploy the application to a production environment.
-   **Data Expansion:**
    -   Curate and add a diverse range of cyberpunk and space opera themed equipment, weapons, armor, cyberware, and other items to the database (either through seed data scripts or a basic admin interface if developed).
    -   Update frontend categories, filters, and display logic if necessary to support these new item types.
-   **Comprehensive Testing:**
    -   Expand API test coverage to include more edge cases, all endpoints, and different user scenarios.
    -   Increase Data Access Layer test coverage.
    -   Introduce basic end-to-end (E2E) tests if feasible, potentially using tools like Selenium or Playwright, to test user flows from the frontend through the API to the database.

## 5. Long-Term Goals (6+ Months)

-   **Full-Fledged Frontend Application:**
    -   If a modern frontend framework migration was initiated, complete it.
    -   Develop a rich, interactive user interface with advanced features for inventory management, character loadouts, item comparisons, etc.
-   **Advanced Authorization & User Management:**
    -   If RBAC was started, fully implement and refine it.
    -   Add more comprehensive user management features like password reset via email, email verification, user profiles, and account settings.
-   **Scalability and Monitoring:**
    -   Implement robust monitoring, logging, and alerting for the production environment (e.g., using Prometheus, Grafana, Sentry, or cloud provider tools).
    -   Optimize application performance and database queries for scalability as user load increases.
    -   Consider database read replicas or other scaling strategies if needed.
-   **Electron App Enhancements:**
    -   Further leverage Electron-specific features to create a richer desktop experience (e.g., offline capabilities for viewing/managing local kits, deeper OS integrations like custom context menus or notifications, if applicable).
    -   Ensure smooth updates and packaging for the Electron application.
-   **Potential New Features (Examples):**
    -   Ability for users to share their kit lists or loadouts with others (e.g., via public links or user-to-user sharing).
    -   Creating and using kit templates or "starter packs."
    -   Integration with other services, game systems, or virtual tabletops (VTTs) via APIs if relevant.
    -   Community features (e.g., rating items, commenting on kits).

## 6. Technology Stack Summary (Current & Planned)

-   **Backend:**
    -   Language: Python
    -   Framework: Flask (current), considering migration to **APIFlask** (recommended for integrated OpenAPI documentation).
    -   WSGI Server: Gunicorn (for production).
-   **Database:**
    -   Development: SQLite (current).
    -   Production: PostgreSQL or MySQL (planned).
-   **Frontend:**
    -   Web: HTML, CSS, JavaScript (current, in `public/`).
    -   Desktop: Electron (wrapping the web frontend).
    -   Future: Potential migration to a modern JavaScript framework (e.g., Vue.js, React, Svelte).
-   **API Specification:** OpenAPI 3.x.
-   **Testing:** Pytest.
-   **Deployment & DevOps:**
    -   Containerization: Docker.
    -   CI/CD: GitHub Actions (planned).
    -   Hosting: CaaS (e.g., Google Cloud Run, AWS Fargate) or other cloud-based solutions (planned).
    -   Configuration Management: Environment variables, `config.py`.
    -   Secrets Management: Platform-specific solutions or dedicated services (planned).
-   **Logging/Monitoring:** Standard Python logging, potentially ELK stack, Prometheus/Grafana, or cloud provider tools (planned).
