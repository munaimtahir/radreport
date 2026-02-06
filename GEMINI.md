# GEMINI Project Context: RIMS (Radiology Information Management System)

This document provides context for the RIMS project, a full-stack web application designed for radiology information management.

## Project Overview

RIMS is a modular and scalable system built to manage radiology workflows, from patient registration to report delivery. It is designed to be easily integrated with other systems like a LIMS (Laboratory Information Management System).

**Key Technologies:**

*   **Backend:**
    *   **Framework:** Django 5 with Django REST Framework (DRF)
    *   **Database:** PostgreSQL
    *   **Authentication:** JWT (JSON Web Tokens)
    *   **API Documentation:** `drf-spectacular` for OpenAPI/Swagger UI
    *   **Other:** `django-filter` for filtering, `ReportLab` for PDF generation.
*   **Frontend:**
    *   **Framework:** React 18 with TypeScript
    *   **Build Tool:** Vite
    *   **Routing:** React Router
    *   **Testing:** Vitest
*   **Infrastructure:**
    *   **Containerization:** Docker and Docker Compose
    *   **Reverse Proxy:** Caddy is used in production to direct traffic to the frontend and backend services.

**Architecture:**

The project follows a decoupled, service-oriented architecture:

1.  **`backend` service:** A Django application that serves the REST API. It is organized into modular Django apps, each handling a specific domain concern (e.g., `patients`, `catalog`, `studies`, `reporting`).
2.  **`frontend` service:** A single-page application (SPA) built with React that consumes the backend API.
3.  **`db` service:** A PostgreSQL database for data persistence.

## Building and Running the Project

There are two primary ways to run the project for development.

### Method 1: Automated Dev Script (Recommended)

The `develop.sh` script automates the setup process using the development-specific Docker Compose configuration.

```bash
# This script starts all services and initializes a superuser.
./develop.sh
```

### Method 2: Manual Setup

Follow the steps in the `README.md` for a manual setup of the backend and frontend. This is useful for more control over the individual components.

**Backend (Manual):**
```bash
cd backend
cp .env.example .env # And configure it
docker compose up -d db # Using the production config for the db
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver 0.0.0.0:8000
```

**Frontend (Manual):**
```bash
cd frontend
npm install
npm run dev
```

### Key Endpoints (Local Development)

*   **Frontend Application:** [http://localhost:5173](http://localhost:5173)
*   **Backend API Base:** [http://localhost:8000/api/](http://localhost:8000/api/)
*   **Swagger API Docs:** [http://localhost:8000/api/docs/](http://localhost:8000/api/docs/)
*   **OpenAPI Schema:** [http://localhost:8000/api/schema/](http://localhost:8000/api/schema/)

## Development Conventions

*   **Modular Backend:** The Django backend is split into several apps (`patients`, `catalog`, `studies`, `templates`, `reporting`, `audit`, `accounts`). When adding new features, consider if they belong in an existing app or a new one.
*   **API-First:** The frontend is fully decoupled from the backend and interacts with it exclusively through the REST API.
*   **Workflows:** The application implements a three-desk workflow (Registration, Performance, Verification). For more details, see `CORE_WORKFLOW_README.md`.
*   **Testing:** The frontend uses `vitest` for unit and component testing. Run tests with `npm test` in the `frontend` directory. Backend testing conventions are not explicitly defined but follow Django standards.
*   **Configuration:** The application uses `.env` files for configuration. `docker-compose.yml` is intended for production, while `docker-compose.dev.yml` is used for local development via the `develop.sh` script.
