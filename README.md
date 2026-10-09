# 🎓 Bulk Certificate Generator API

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.12%2B-blue?style=for-the-badge&logo=python&logoColor=white" alt="Python 3.12" />
  <img src="https://img.shields.io/badge/FastAPI-0.115%2B-009688?style=for-the-badge&logo=fastapi&logoColor=white" alt="FastAPI" />
  <img src="https://img.shields.io/badge/PostgreSQL-16-336791?style=for-the-badge&logo=postgresql&logoColor=white" alt="PostgreSQL" />
  <img src="https://img.shields.io/badge/SQLAlchemy-2.0-red?style=for-the-badge&logo=sqlalchemy&logoColor=white" alt="SQLAlchemy" />
  <img src="https://img.shields.io/badge/Pydantic-v2-E92063?style=for-the-badge&logo=pydantic&logoColor=white" alt="Pydantic v2" />
  <img src="https://img.shields.io/badge/Docker-Enabled-2496ED?style=for-the-badge&logo=docker&logoColor=white" alt="Docker" />
  <img src="https://img.shields.io/badge/Tests-Passing-brightgreen?style=for-the-badge&logo=pytest&logoColor=white" alt="Pytest" />
</p>

A production-grade, asynchronous REST API engineered to generate bulk PDF certificates with enterprise-grade **failure isolation**, background job scheduling, real-time progress tracking, and secure document retrieval.

---

## 📌 Table of Contents
- [Overview](#-overview)
- [Problem Statement](#-problem-statement)
- [Key Features](#-key-features)
- [Architecture & Workflow](#-architecture--workflow)
- [Tech Stack](#-tech-stack)
- [Project Structure](#-project-structure)
- [Prerequisites](#-prerequisites)
- [Local Setup](#-local-setup)
- [Environment Variables](#-environment-variables)
- [Database Setup & Migrations](#-database-setup--migrations)
- [Running Locally](#-running-locally)
- [Running with Docker](#-running-with-docker)
- [Interactive API Documentation (Swagger)](#-interactive-api-documentation-swagger)
- [API Endpoints](#-api-endpoints)
- [Example Request & Response](#-example-request--response)
- [Certificate Retrieval](#-certificate-retrieval)
- [Bulk Processing Mechanism](#-bulk-processing-mechanism)
- [Failure Handling & Isolation](#-failure-handling--isolation)
- [Key Architectural Decisions](#-key-architectural-decisions)
- [Testing & Coverage](#-testing--coverage)
- [Assumptions](#-assumptions)
- [Future Improvements](#-future-improvements)

---

## 📖 Overview
The **Bulk Certificate Generator API** provides a resilient backend service for institutions, bootcamps, and organizations that need to issue verified completion certificates to hundreds or thousands of participants simultaneously. 

Instead of freezing the HTTP connection while generating high-resolution PDF documents, the system adopts an asynchronous **Job Pattern** (`HTTP 202 Accepted`), processing batches in the background while allowing clients to monitor generation progress and download certificates on demand.

---

## ❗ Problem Statement
When generating hundreds of PDF certificates sequentially during a standard synchronous HTTP request:
1. **HTTP Timeouts**: Gateway proxies (Nginx, Cloudflare, AWS ALB) terminate requests after 30–60 seconds, causing client failures.
2. **Cascading Failures**: A single malformed name, unsupported character, or memory hiccup often crashes the entire script, leaving all subsequent recipients without certificates.
3. **Resource Starvation**: PDF compilation is CPU- and I/O-intensive; running it inside web workers locks server resources from answering other API requests.

The **Bulk Certificate Generator API** directly solves these challenges through asynchronous offloading, atomic database updates, and recipient-level failure isolation.

---

## ✨ Key Features
- **🚀 Asynchronous Bulk Processing**: Instantaneous HTTP 202 response with job tracking ID.
- **🛡️ Fault-Tolerant Failure Isolation**: If recipient #45 encounters an error, recipients #46–100 continue generating without interruption.
- **📊 Granular Progress Tracking**: Live progress percentage, counts (`total`, `completed`, `failed`), and state visibility per recipient.
- **📜 Professional PDF Engine**: High-fidelity ReportLab template featuring dual navy/gold borders, ornamental accents, and clean typography.
- **🔒 Path-Traversal & Injection Defense**: System-generated UUID filenames (`certificate_<uuid>.pdf`) and parameterized SQLAlchemy queries.
- **🧪 Comprehensive Test Suite**: 40+ unit and integration tests covering positive flows, boundary validation, failure isolation, and PDF byte verification.
- **🐳 Dockerized Out-of-the-Box**: Complete `Dockerfile` and `docker-compose.yml` with healthchecked PostgreSQL.

---

## 🏛️ Architecture & Workflow

### Core User Flow
```text
Client Application
       │
       │  1. POST /api/v1/jobs (Title, Event, Recipients List)
       ▼
 FastAPI Router
       │
       │  2. Strict Pydantic v2 Validation
       ▼
 Job Service
       │  3. Persist Job (PENDING) & Certificates (PENDING) in DB
       │  4. Return HTTP 202 Accepted { job_id: "uuid" }
       ▼
 Background Task Worker
       │
       ├─► [Recipient 1] ──► Generate PDF ──► SUCCESS (Increment completed)
       ├─► [Recipient 2] ──► Generate PDF ──► SUCCESS (Increment completed)
       ├─► [Recipient 3] ──► Bad Data/IO  ──► FAILED  (Isolate error, log, increment failed)
       └─► [Recipient 4] ──► Generate PDF ──► SUCCESS (Increment completed)
       │
       ▼  5. Final Job Status: COMPLETED_WITH_ERRORS
 Client Polling
       │
       ├─► GET /api/v1/jobs/{job_id} ────────► Progress: 75% | Status: COMPLETED_WITH_ERRORS
       └─► GET /api/v1/certificates/{cert_id} ─► Streams PDF (Content-Type: application/pdf)
```

---

## 💻 Tech Stack

| Category | Technology | Purpose |
|---|---|---|
| **Language** | Python 3.12+ | Modern syntax, robust typing, and high efficiency |
| **Framework** | FastAPI 0.115+ | High-performance ASGI framework with automatic OpenAPI docs |
| **Server** | Uvicorn 0.30+ | Lightning-fast ASGI web server |
| **Database** | PostgreSQL 16 | Relational persistence with UUID and Enum support |
| **ORM** | SQLAlchemy 2.0+ | Modern type-safe data access with QueuePool connection pooling |
| **Migrations** | Alembic 1.13+ | Automated, version-controlled database schema migrations |
| **Validation** | Pydantic v2 | High-speed schema validation and serialization |
| **PDF Rendering** | ReportLab 4.2+ | Programmatic, high-precision vector PDF generation |
| **Testing** | Pytest & HTTPX | Automated test runner and asynchronous HTTP client |
| **Containerization** | Docker & Compose | Multi-container environment orchestration |

---

## 📁 Project Structure

```text
bulk-certificate-generator-api/
├── app/
│   ├── __init__.py
│   ├── main.py                     # FastAPI application setup & lifecycle
│   ├── api/
│   │   ├── __init__.py
│   │   └── routes/
│   │       ├── health.py           # GET /health
│   │       ├── jobs.py             # POST /api/v1/jobs, GET /api/v1/jobs/{id}
│   │       └── certificates.py     # GET /api/v1/certificates/{id}
│   ├── core/
│   │   ├── config.py               # pydantic-settings configuration
│   │   ├── database.py             # SQLAlchemy engine & session factory
│   │   └── logging_config.py       # Formatted structured logging
│   ├── exceptions/
│   │   └── handlers.py             # Centralized HTTP exception handlers
│   ├── models/
│   │   ├── generation_job.py       # GenerationJob model & JobStatus enum
│   │   └── certificate.py          # Certificate model & CertificateStatus enum
│   ├── repositories/
│   │   ├── job_repository.py       # GenerationJob database CRUD
│   │   └── certificate_repository.py# Certificate database CRUD & bulk insert
│   ├── schemas/
│   │   ├── job.py                  # Pydantic schemas for Job request/response
│   │   └── certificate.py          # Pydantic schemas for Certificate responses
│   └── services/
│       ├── job_service.py          # Background bulk runner & failure isolation
│       ├── certificate_service.py  # Certificate retrieval logic
│       └── pdf_service.py          # PDF storage coordination
├── templates/
│   └── certificate_template.py     # ReportLab layout, styling & canvas builder
├── generated_certificates/         # Local PDF storage directory (.gitignore)
├── tests/
│   ├── conftest.py                 # Pytest fixtures & isolated in-memory DB
│   ├── test_create_job.py          # Job creation & 202 acceptance tests
│   ├── test_validation.py          # Pydantic boundary validation tests (15 cases)
│   ├── test_certificate_generation.py# PDF generation & byte validation tests
│   ├── test_job_status.py          # Status polling & percentage calculation tests
│   ├── test_failure_handling.py    # Failure isolation & error state tests
│   └── test_certificate_retrieval.py# PDF retrieval & 404/422 handling tests
├── postman/
│   └── Bulk-Certificate-Generator.postman_collection.json # Ready-to-import collection
├── alembic/
│   ├── env.py                      # Migration environment
│   └── versions/
│       └── 001_initial.py          # Initial schema migration
├── .env.example                    # Environment variable template
├── .gitignore                      # Git exclusion rules
├── Dockerfile                      # Production container image
├── docker-compose.yml              # Multi-container Compose manifest
├── pyproject.toml                  # Pytest & Coverage configuration
├── requirements.txt                # Pinned production dependencies
├── REQUIREMENTS_CHECKLIST.md       # Traceability matrix
├── INTERVIEW_PREPARATION.md        # 30 comprehensive interview Q&A
└── README.md                       # Complete documentation
```

---

## ⚙️ Prerequisites
Ensure you have the following installed:
- **Python**: `3.12.0` or higher
- **PostgreSQL**: `14+` (or use Docker)
- **Git**
- **Docker & Docker Compose** (optional, recommended for fast deployment)

---

## 🚀 Local Setup

### 1. Clone the Repository
```bash
git clone https://github.com/your-username/bulk-certificate-generator-api.git
cd bulk-certificate-generator-api
```

### 2. Create and Activate a Virtual Environment
```bash
# Windows (PowerShell)
python -m venv venv
.\venv\Scripts\Activate.ps1

# Linux / macOS
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

---

## 🌐 Environment Variables
Create a `.env` file in the project root:
```bash
# Windows
Copy-Item .env.example .env

# Linux / macOS
cp .env.example .env
```

Default `.env` configuration:
```env
DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/certificate_db
TEST_DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/certificate_db_test
CERTIFICATE_OUTPUT_DIR=generated_certificates
APP_ENV=development
DEBUG=false
```

---

## 🗄️ Database Setup & Migrations

Ensure PostgreSQL is running and the database exists:
```sql
CREATE DATABASE certificate_db;
```

Run Alembic migrations to create tables and indexes:
```bash
alembic upgrade head
```

---

## 🏃 Running Locally

Start the development server using Uvicorn:
```bash
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

The application will be live at:
- **API Base URL**: `http://localhost:8000`
- **Health Check**: `http://localhost:8000/health`
- **Interactive Swagger Docs**: `http://localhost:8000/docs`

---

## 🐳 Running with Docker

Run the complete stack (FastAPI + PostgreSQL) with a single command:
```bash
docker compose up --build
```

To run in the background (detached mode):
```bash
docker compose up -d
```

To stop containers:
```bash
docker compose down
```

---

## 📖 Interactive API Documentation (Swagger)

FastAPI automatically serves interactive documentation:
- **Swagger UI**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc**: [http://localhost:8000/redoc](http://localhost:8000/redoc)
- **Raw OpenAPI Schema**: [http://localhost:8000/openapi.json](http://localhost:8000/openapi.json)

---

## 📡 API Endpoints

| Method | Endpoint | Description | Status Code |
|---|---|---|---|
| `GET` | `/health` | Check API and database connectivity | `200 OK` / `503 Service Unavailable` |
| `POST` | `/api/v1/jobs` | Submit bulk certificate generation job | `202 Accepted` |
| `GET` | `/api/v1/jobs/{job_id}` | Poll generation job progress and recipient status | `200 OK` / `404 Not Found` |
| `GET` | `/api/v1/certificates/{certificate_id}` | Download generated certificate PDF | `200 OK` / `404 Not Found` / `422 Unprocessable` |

---

## 📤 Example Request & Response

### 1. Create Generation Job
**Request:**
```http
POST /api/v1/jobs
Content-Type: application/json

{
  "certificate_title": "Certificate of Completion",
  "event_name": "Python Backend Development Workshop",
  "organization_name": "Aero",
  "issue_date": "2026-10-07",
  "recipients": [
    {
      "name": "Gokul M",
      "email": "gokul@example.com"
    },
    {
      "name": "Rahul Kumar",
      "email": "rahul@example.com"
    }
  ]
}
```

**Response (`202 Accepted`):**
```json
{
  "job_id": "4b92b67d-94e8-466a-9f5b-6f81e3c84792",
  "status": "PENDING",
  "total": 2,
  "completed": 0,
  "failed": 0,
  "message": "Job accepted. Processing 2 certificates in the background."
}
```

---

### 2. Poll Job Status
**Request:**
```http
GET /api/v1/jobs/4b92b67d-94e8-466a-9f5b-6f81e3c84792
```

**Response (`200 OK`):**
```json
{
  "job_id": "4b92b67d-94e8-466a-9f5b-6f81e3c84792",
  "status": "COMPLETED",
  "total": 2,
  "completed": 2,
  "failed": 0,
  "progress_percentage": 100,
  "created_at": "2026-10-07T21:45:00.000000+00:00",
  "started_at": "2026-10-07T21:45:00.120000+00:00",
  "completed_at": "2026-10-07T21:45:00.480000+00:00",
  "certificates": [
    {
      "certificate_id": "8f8b86e1-95fa-4df3-a129-d5fc3ab9f2b1",
      "recipient_name": "Gokul M",
      "recipient_email": "gokul@example.com",
      "status": "COMPLETED",
      "download_url": "/api/v1/certificates/8f8b86e1-95fa-4df3-a129-d5fc3ab9f2b1",
      "error": null,
      "created_at": "2026-10-07T21:45:00.000000+00:00",
      "completed_at": "2026-10-07T21:45:00.310000+00:00"
    },
    {
      "certificate_id": "b1a2c3d4-e5f6-7a8b-9c0d-1e2f3a4b5c6d",
      "recipient_name": "Rahul Kumar",
      "recipient_email": "rahul@example.com",
      "status": "COMPLETED",
      "download_url": "/api/v1/certificates/b1a2c3d4-e5f6-7a8b-9c0d-1e2f3a4b5c6d",
      "error": null,
      "created_at": "2026-10-07T21:45:00.000000+00:00",
      "completed_at": "2026-10-07T21:45:00.470000+00:00"
    }
  ]
}
```

---

## 📥 Certificate Retrieval

When a certificate's status is `COMPLETED`, retrieve the PDF directly:
```bash
curl -O -J http://localhost:8000/api/v1/certificates/8f8b86e1-95fa-4df3-a129-d5fc3ab9f2b1
```

- **Headers returned**:
  - `Content-Type: application/pdf`
  - `Content-Disposition: attachment; filename="certificate_Gokul_M.pdf"`
- If the certificate ID does not exist: returns `404 Not Found`.
- If the certificate failed or is still processing: returns `422 Unprocessable Entity` with an explanatory message.

---

## ⚡ Bulk Processing Mechanism
- **Batch Acceptance**: The client submits up to 1,000 recipients in a single POST request.
- **Immediate Return**: The parent job and all initial certificate entries are persisted in a single bulk transaction. The endpoint dispatches `process_job_background` via FastAPI's `BackgroundTasks` and returns immediately.
- **Independent Session**: Background workers instantiate their own database session via `SessionLocal()`, ensuring the background thread does not encounter closed connection errors.

---

## 🛡️ Failure Handling & Isolation

Failure isolation is a core requirement of this system:

```text
Job: 100 Recipients
├── Recipients 1 to 26  ──► SUCCESS
├── Recipient 27        ──► ERROR (Isolated, logged, marked FAILED)
└── Recipients 28 to 100 ─► Continue uninterrupted!

Result:
- total: 100
- completed: 99
- failed: 1
- status: COMPLETED_WITH_ERRORS
```

### How it is implemented:
1. Each certificate generation is enclosed in an explicit `try...except` block in `app/services/job_service.py`.
2. Any failure (e.g. disk write failure, unexpected character) triggers `cert_repo.mark_failed(cert_id, error_str)` and increments `job.failed_count`.
3. The loop proceeds to the next recipient without interruption.
4. When finished, if `failed_count > 0` and `successful_count > 0`, the job status transitions to `COMPLETED_WITH_ERRORS`.

---

## ⚖️ Key Architectural Decisions

1. **FastAPI over Django / Flask**:
   - Built-in asynchronous support, native dependency injection, and automatic OpenAPI schema generation with zero extra boilerplate.
2. **PostgreSQL + SQLAlchemy 2.0**:
   - Native UUID support, strict ACID guarantees, and typed ORM definitions using `Mapped[...]`.
3. **In-Process BackgroundTasks vs. Celery/Redis**:
   - Avoids external messaging infrastructure (Redis/RabbitMQ) while fully satisfying asynchronous decoupling and remaining easy to run and debug during an interview.
4. **ReportLab Canvas Engine**:
   - Direct vector graphics generation without heavy headless browser runtimes (like Chromium/Puppeteer), maintaining a small memory footprint (~30MB vs 400MB+).

---

## 🧪 Testing & Coverage

The automated test suite runs on an isolated in-memory database and temporary file directory, ensuring zero impact on development or production databases.

### Run All Tests
```bash
pytest
```

### Run Tests with Coverage Report
```bash
pytest --cov=app --cov-report=term-missing
```

### Test Suites Included:
- `tests/test_create_job.py`: Job creation, 202 status, UUID generation, initial state.
- `tests/test_validation.py`: 15 boundary cases (missing fields, blank strings, invalid emails, date parsing).
- `tests/test_certificate_generation.py`: PDF creation, file existence, `%PDF-` header validation.
- `tests/test_job_status.py`: Progress calculations, 404 handling, certificate listings.
- `tests/test_failure_handling.py`: Simulated selective failures, `COMPLETED_WITH_ERRORS` verification.
- `tests/test_certificate_retrieval.py`: PDF downloads, content headers, 404/422 responses.

---

## 📋 Assumptions
- Certificates use standard landscape A4 format.
- Output files are written to the local storage directory configured via `CERTIFICATE_OUTPUT_DIR`.
- Email addresses are validated for RFC formatting; actual email delivery is handled by downstream notification services.

---

## 🔮 Future Improvements
1. **Distributed Queue**: Add Celery or ARQ with Redis for multi-node worker scaling.
2. **Cloud Storage**: Integrate Amazon S3 or Google Cloud Storage with signed download URLs.
3. **Webhooks**: Provide a `callback_url` parameter to notify client systems when jobs finish.
4. **Rate Limiting**: Add Redis-based token bucket rate limiting for job submission endpoints.
