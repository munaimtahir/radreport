# System Architecture

## Backend
- Django 5
- Django REST Framework
- PostgreSQL
- JWT Authentication
- ReportLab for PDF
- Celery + Redis (future-ready)

## Frontend
- React
- TypeScript
- Vite
- Plain CSS

## Core Design Rule
Each domain concern is isolated in its own Django app to allow future merging with LIMS.
