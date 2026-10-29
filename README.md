# ClubSphere

ClubSphere is a unified campus student club and event management platform built with FastAPI, SQLite, React 19, TypeScript, and TailwindCSS v4. It streamlines club administration, event registration, proposal workflows, and student engagement across campus.

## Architecture

ClubSphere follows a clean, decoupled architecture separating UI presentation, domain business rules, and API infrastructure:

* **Backend (`backend/`)**: FastAPI application providing secure REST APIs, role-based access control (RBAC), SQLite/SQLAlchemy ORM models, Pydantic schemas, and Pytest coverage.
* **Frontend (`frontend/`)**: React 19 single-page application powered by Vite, TailwindCSS v4, React Router, and a domain-driven service architecture with centralized authentication.
* **Runner (`app.py`)**: Unified Python runner that detects port conflicts, verifies dependencies, and concurrently boots both backend and frontend servers with colored logs.
* **Documentation (`docs/`)**: Entity-Relationship documentation including DBML and Mermaid visual schemas.

## Quick Start

### Option 1: Unified Runner (Recommended)

From the project root:

```powershell
python app.py
```

This checks prerequisites, initializes required folders, and launches both services:
* Frontend: `http://localhost:5173`
* Backend API: `http://localhost:8000`
* Interactive API Docs: `http://localhost:8000/docs`

### Option 2: Running Services Individually

#### Backend Setup

```powershell
cd backend
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

#### Frontend Setup

```powershell
cd frontend
npm install
npm run dev
```

## Role-Based Access Control

The platform provides dedicated access tiers:

* **Super Admin**: Complete administrative oversight over all clubs, approvals, and platform analytics.
* **Club Lead**: Manage club profile, schedule events, review memberships, and submit proposals.
* **Student Member**: Discover clubs, register for campus events, view past registrations, and submit club applications.

## Verification & Testing

### Backend Test Suite

Run unit and integration tests covering authentication, clubs, events, registrations, proposals, and RBAC security:

```powershell
cd backend
pytest
```

### Frontend Code Quality

Run Oxlint and production TypeScript compilation:

```powershell
cd frontend
npm run lint
npm run build
```

## Database Schema & Documentation

For comprehensive schema diagrams, foreign key relationships, and design notes, consult:
* `docs/DATABASE_ER_SCHEMA.md`
* `docs/schema.mermaid`
* `docs/schema.dbml`
