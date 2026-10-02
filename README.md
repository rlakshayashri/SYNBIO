# SynDataX

**SynDataX** is a modular scientific data intelligence platform designed to connect:

**Design → Experiment → Data → Validation → Analysis → Interpretation → Reporting**

This repository contains the backend foundation for SynDataX, built with modularity, maintainability, and reproducibility as core architectural principles.

---

## 📌 Project Status

**Current Milestone:** Module 1 — Backend Foundation  
The current release initializes the core backend infrastructure (FastAPI, PostgreSQL database ORM, Alembic migrations, modular service architecture, and empty scientific module placeholders). The scientific computation engines (validation, statistics, preprocessing, visualization) will be implemented in subsequent milestones.

---

## 🛠 Technology Stack

- **Language:** Python 3.12+
- **API Framework:** FastAPI & Uvicorn
- **Validation & Settings:** Pydantic v2 & `pydantic-settings`
- **Database & ORM:** PostgreSQL 16 & SQLAlchemy 2.x
- **Schema Migrations:** Alembic
- **Scientific Computing Ready:** Pandas, NumPy, SciPy, statsmodels, scikit-learn, openpyxl
- **Code Quality & Testing:** Ruff & Pytest
- **Containerization:** Docker & Docker Compose

---

## 📁 Project Structure

```text
SynDataX/
├── backend/
│   ├── app/
│   │   ├── api/          # Versioned API routes (/api/v1/health)
│   │   ├── core/         # Settings (Pydantic v2) and logging configuration
│   │   ├── db/           # SQLAlchemy 2.x session, base, and engine setup
│   │   ├── models/       # Database ORM models (Project, Dataset, Analysis)
│   │   ├── schemas/      # Pydantic request/response validation schemas
│   │   ├── services/     # Business logic layer (ProjectService, DatasetService, etc.)
│   │   └── scientific/   # Future scientific engines (validation, stats, etc.)
│   ├── tests/            # Test suite for health endpoints & database connectivity
│   ├── alembic/          # Reproducible database schema migrations
│   ├── alembic.ini       # Alembic configuration
│   ├── pyproject.toml    # Dependencies and tool configurations (Ruff, pytest)
│   └── .env.example      # Environment configuration template
├── database/
│   └── docker-compose.yml # PostgreSQL 16 Docker setup
├── frontend/             # Reserved for future web UI
├── docs/                 # Documentation directory
└── README.md
```

---

## 🚀 Local Development Setup

Follow these steps to set up the backend locally:

### 1. Start PostgreSQL Database

Use Docker Compose to launch PostgreSQL:

```bash
docker compose -f database/docker-compose.yml up -d
```

### 2. Configure Environment Variables

Navigate to the `backend/` folder and copy `.env.example` to `.env`:

```bash
cd backend
cp .env.example .env
```

Default credentials in `.env`:
```env
APP_NAME=SynDataX
APP_ENV=development
LOG_LEVEL=INFO
DATABASE_URL=postgresql+psycopg://syndatax:syndatax@localhost:5432/syndatax
```

### 3. Create Python Virtual Environment & Install Dependencies

```bash
python -m venv .venv
# On Windows PowerShell:
.venv\Scripts\Activate.ps1
# On Linux/macOS:
source .venv/bin/activate

pip install -r requirements.txt
```

### 4. Run Database Migrations

Apply Alembic migrations to create the database schema:

```bash
alembic upgrade head
```

### 5. Start the FastAPI Development Server

```bash
uvicorn app.main:app --reload --port 8000
```

Access the interactive API documentation at:
- **Swagger UI:** [http://localhost:8000/docs](http://localhost:8000/docs)
- **Health Check:** [http://localhost:8000/api/v1/health](http://localhost:8000/api/v1/health)

---

## 🧪 Testing & Code Quality

Run tests using Pytest:

```bash
pytest
```

Run linter and code formatter using Ruff:

```bash
ruff check app tests
ruff format --check app tests
```

---

## 🏛 Architectural Guidelines

1. **Separation of Concerns:**  
   `API Route -> Service Layer -> Scientific Engine -> Database Model`  
   Never write complex data calculations directly inside route handlers.

2. **API Versioning:**  
   All endpoints must be namespaced under `/api/v1/`.

3. **Database Migrations:**  
   `alembic upgrade head` is the single source of truth for schema management. Never use `Base.metadata.create_all()` in production code.
