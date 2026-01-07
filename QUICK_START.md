# Quick Start Guide

## Superuser Setup

A superuser has been created with the following credentials:
- **Username:** `admin`
- **Password:** `admin123`

To create or update the superuser manually, run:
```bash
cd backend
source venv/bin/activate
python3 create_superuser.py
```

## Running the Application

### Backend (Django)
```bash
cd backend
source venv/bin/activate
python3 manage.py runserver 0.0.0.0:8000
```

The backend will be available at: http://localhost:8000

### Frontend (React + Vite)
```bash
cd frontend
npm run dev
```

The frontend will be available at: http://localhost:5173

## Accessing the Application

1. Open your browser and navigate to: **http://localhost:5173**
2. You should see the login page
3. Login with:
   - Username: `admin`
   - Password: `admin123`

## Troubleshooting

### Blank Page Issue

If you see a blank page:

1. **Check Browser Console** (F12):
   - Look for JavaScript errors
   - Check Network tab for failed API requests

2. **Verify Servers are Running**:
   ```bash
   # Check backend
   curl http://localhost:8000/api/health/
   # Should return: {"status": "ok"}
   
   # Check frontend
   curl http://localhost:5173/
   # Should return HTML
   ```

3. **Clear Browser Cache**:
   - Hard refresh: Ctrl+Shift+R (Linux/Windows) or Cmd+Shift+R (Mac)
   - Or clear browser cache and localStorage

4. **Check CORS Settings**:
   - Backend CORS is configured for `http://localhost:5173`
   - Verify this matches your frontend URL

5. **Verify API Connection**:
   - Open browser DevTools → Network tab
   - Try logging in and check if `/api/auth/token/` request succeeds

### Common Issues

- **"No page displayed"**: Usually means React isn't mounting. Check browser console for errors.
- **Login fails**: Verify backend is running and superuser exists.
- **CORS errors**: Ensure backend CORS settings include your frontend URL.

## API Endpoints

- Health check: `GET http://localhost:8000/api/health/`
- Login: `POST http://localhost:8000/api/auth/token/`
- API docs: `http://localhost:8000/api/docs/`
