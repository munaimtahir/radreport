# Setup Instructions

## Backend Setup

1. **Install Python dependencies:**
   ```bash
   cd backend
   python3 -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Set up database:**
   ```bash
   # Start PostgreSQL and Redis using Docker Compose
   docker compose up -d db redis
   
   # Create migrations
   python manage.py makemigrations
   
   # Apply migrations
   python manage.py migrate
   
   # Create superuser
   python manage.py createsuperuser
   ```

3. **Run development server:**
   ```bash
   python manage.py runserver 0.0.0.0:8000
   ```

## Frontend Setup

1. **Install dependencies:**
   ```bash
   cd frontend
   npm install
   ```

2. **Run development server:**
   ```bash
   npm run dev
   ```

## Access Points

- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/api/docs/
- Frontend: http://localhost:5173

## Authentication

Use the superuser credentials created during setup to log in via the frontend login form.

