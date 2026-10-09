<div align="center">

# 🎓 Bulk Certificate Generator API

### *High-Throughput Asynchronous PDF Generation Engine with Resilient Failure Isolation*

[![Python Version](https://img.shields.io/badge/Python-3.12%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115%2B-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-336791?style=for-the-badge&logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0-D71F00?style=for-the-badge&logo=sqlalchemy&logoColor=white)](https://www.sqlalchemy.org/)
[![Pydantic](https://img.shields.io/badge/Pydantic-v2-E92063?style=for-the-badge&logo=pydantic&logoColor=white)](https://docs.pydantic.dev/)
[![Docker](https://img.shields.io/badge/Docker-Enabled-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://www.docker.com/)
[![Pytest Tests](https://img.shields.io/badge/Tests-52%20Passed-2EA44F?style=for-the-badge&logo=pytest&logoColor=white)](https://pytest.org/)
[![Coverage](https://img.shields.io/badge/Coverage-92%25-brightgreen?style=for-the-badge&logo=codecov&logoColor=white)](https://pytest.org/)
[![License](https://img.shields.io/badge/License-MIT-blue?style=for-the-badge)](LICENSE)

<br/>

**[Explore Swagger UI](http://localhost:8000/docs) • [View Endpoints](#-api-endpoints) • [Quickstart Guide](#-quick-start) • [Interview Guide](INTERVIEW_PREPARATION.md) • [Checklist](REQUIREMENTS_CHECKLIST.md)**

---

</div>

## 📌 Executive Summary

The **Bulk Certificate Generator API** is an enterprise-grade backend service built with **FastAPI**, **PostgreSQL**, **SQLAlchemy 2.0**, and **ReportLab**. Designed for universities, edtech platforms, and corporate training programs, it issues verified, publication-grade PDF certificates at scale without freezing client HTTP connections.

It replaces slow, blocking scripts with an asynchronous **HTTP 202 Job Pattern** and enforces **Failure Isolation**: a corrupt record or localized rendering error on one recipient will **never** interrupt or cancel the generation of valid certificates in the batch.

---

## 🌟 Key Highlights & Engineering Features

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                                ARCHITECTURAL HIGHLIGHTS                                │
├─────────────────────────┬─────────────────────────────┬────────────────────────────────┤
│ 🚀 202 Asynchronous Job │ 🛡️ Failure Isolation       │ 📜 ReportLab Vector Canvas    │
│ Instant UUID response   │ Bad records isolated;       │ Millimeter-precise landscape   │
│ non-blocking workers    │ valid siblings proceed 100% │ dual-border certificate design │
├─────────────────────────┼─────────────────────────────┼────────────────────────────────┤
│ 🧪 92% Test Coverage    │ 🔒 Strict Security          │ 🐳 Full Containerization       │
│ 52 automated tests with │ Parameterized SQL & UUID    │ Multi-container Docker Compose │
│ in-memory SQLite harness│ filenames prevent exploits  │ with healthy PostgreSQL probe  │
└─────────────────────────┴─────────────────────────────┴────────────────────────────────┘
```

- **⚡ Asynchronous Bulk Dispatch**: Submit up to 1,000 recipients in a single payload; receive an instant `HTTP 202 Accepted` response with a job UUID.
- **🛡️ Individual Failure Isolation**: Unhandled exceptions during single-certificate rendering are trapped, logged, and tracked without halting the queue.
- **📈 Granular Progress Tracking**: Query real-time completion percentages, success/failure metrics, and per-recipient status arrays.
- **🎨 Publication-Grade PDF Template**: Rendered using ReportLab with double navy-gold borders, corner ornaments, and dynamic typography.
- **🛡️ Zero-Trust Security**:
  - **SQL Injection Immune**: 100% parameterized SQLAlchemy 2.0 ORM queries.
  - **Path Traversal Immune**: Internal UUID-based storage keys (`certificate_<uuid>.pdf`).
  - **Sanitized Errors**: Clean JSON payloads prevent stack trace exposure.
- **📦 Production-Ready Tooling**: Includes Alembic database migrations, Postman collections, Docker Compose, and structured logging.

---

## 📐 System Architecture & Workflow

```mermaid
sequenceDiagram
    autonumber
    actor Client as API Client / Frontend
    participant API as FastAPI Router
    participant Service as Job Service
    participant DB as PostgreSQL Database
    participant Worker as Background Task Runner
    participant PDF as ReportLab PDF Engine
    participant FS as Local File Storage

    Client->>API: POST /api/v1/jobs (Title, Event, Recipients List)
    API->>API: Validate schema via Pydantic v2
    API->>Service: create_job(request)
    Service->>DB: Bulk-insert Job (PENDING) & Certificates (PENDING)
    Service-->>API: JobCreatedResponse (UUID, initial counts)
    API-->>Client: HTTP 202 Accepted (job_id: uuid)
    
    par Background Generation
        API->>Worker: Schedule process_job_background(job_id)
        Worker->>DB: Mark Job -> PROCESSING
        loop For Each Recipient
            Worker->>PDF: generate_certificate_pdf(...)
            alt Success
                PDF->>FS: Save certificate_<uuid>.pdf
                Worker->>DB: Mark Certificate -> COMPLETED, increment successful_count
            else Fault / Failure
                Worker->>DB: Mark Certificate -> FAILED (save error), increment failed_count
            end
        end
        Worker->>DB: Update final Job status (COMPLETED / COMPLETED_WITH_ERRORS)
    end

    Client->>API: GET /api/v1/jobs/{job_id} (Polling)
    API->>DB: Fetch job status & certificate array
    DB-->>API: Return progress metrics
    API-->>Client: HTTP 200 OK (progress_percentage, status)

    Client->>API: GET /api/v1/certificates/{certificate_id}
    API->>FS: Stream PDF file
    FS-->>Client: HTTP 200 OK (Content-Type: application/pdf)
```

---

## 🔄 State Machine Lifecycle

```
             ┌─────────────────────────┐
             │         PENDING         │
             └────────────┬────────────┘
                          │ (Worker starts)
                          ▼
             ┌─────────────────────────┐
             │       PROCESSING        │
             └────────────┬────────────┘
                          │
         ┌────────────────┼────────────────┐
         │ (0 failures)   │ (mixed)        │ (all failed)
         ▼                ▼                ▼
┌─────────────────┐ ┌───────────────┐ ┌─────────┐
│    COMPLETED    │ │COMPLETED_WITH_│ │ FAILED  │
│                 │ │    ERRORS     │ │         │
└─────────────────┘ └───────────────┘ └─────────┘
```

---

## 🎨 Predefined Certificate Template Design

The certificate is rendered programmatically using ReportLab in A4 Landscape mode:

```text
+---------------------------------------------------------------------------------+
| ############################################################################### |
| #  +-----------------------------------------------------------------------+  # |
| #  |                                                                       |  # |
| #  |                          ORGANIZATION NAME                            |  # |
| #  |                           PROUDLY PRESENTS                            |  # |
| #  |                 ═════════════════════════════════════                 |  # |
| #  |                      CERTIFICATE OF COMPLETION                        |  # |
| #  |                 ═════════════════════════════════════                 |  # |
| #  |                                                                       |  # |
| #  |                 This certificate is proudly awarded to                |  # |
| #  |                                                                       |  # |
| #  |                            RECIPIENT NAME                             |  # |
| #  |                                                                       |  # |
| #  |             in recognition of successful completion of                |  # |
| #  |                                                                       |  # |
| #  |                    Python Backend Development Workshop                |  # |
| #  |                             ─────────                                 |  # |
| #  |                        Issued on: 2026-10-07                          |  # |
| #  |                                                                       |  # |
| #  +-----------------------------------------------------------------------+  # |
| ############################################################################### |
+---------------------------------------------------------------------------------+
```

### Visual Specifications
- **Dimensions**: Standard A4 Landscape ($297 \times 210\,\text{mm}$).
- **Color Palette**:
  - `Deep Navy` (`#1A237E`): Outer 4pt structural border, primary headings, recipient name.
  - `Metallic Gold` (`#C9A84C`): Inner 1.5pt accent border, corner ornament squares, dividing bars.
  - `Charcoal Grey` (`#2C3E50`): Body descriptions and timestamps.
  - `Canvas Background` (`#F8F9FA`): Soft parchment off-white.

---

## 🗄️ Database Schema & Indexes

```
  ┌────────────────────────────────────────────────────────┐
  │                    generation_jobs                     │
  ├────────────────────────────────────────────────────────┤
  │ PK  id                 UUID                            │
  │     status             ENUM (JobStatus) [INDEX]        │
  │     certificate_title  VARCHAR(255)                    │
  │     event_name         VARCHAR(255)                    │
  │     organization_name  VARCHAR(255)                    │
  │     issue_date         VARCHAR(20)                     │
  │     total_recipients   INTEGER                         │
  │     successful_count   INTEGER                         │
  │     failed_count       INTEGER                         │
  │     created_at         TIMESTAMPTZ                     │
  │     started_at         TIMESTAMPTZ (NULLABLE)          │
  │     completed_at       TIMESTAMPTZ (NULLABLE)          │
  └───────────────────────────┬────────────────────────────┘
                              │ 1
                              │
                              │ *
  ┌───────────────────────────▼────────────────────────────┐
  │                      certificates                      │
  ├────────────────────────────────────────────────────────┤
  │ PK  id                 UUID                            │
  │ FK  job_id             UUID (ON DELETE CASCADE) [INDEX]│
  │     recipient_name     VARCHAR(255)                    │
  │     recipient_email    VARCHAR(255)                    │
  │     status             ENUM (CertificateStatus)        │
  │     file_path          VARCHAR(500) (NULLABLE)         │
  │     error_message      TEXT (NULLABLE)                 │
  │     created_at         TIMESTAMPTZ                     │
  │     completed_at       TIMESTAMPTZ (NULLABLE)          │
  ├────────────────────────────────────────────────────────┤
  │ INDEX ix_certificates_job_id_status (job_id, status)   │
  └────────────────────────────────────────────────────────┘
```

---

## ⚡ Quick Start

### Option 1: Run with Docker Compose (Fastest)

```bash
# Clone the repository
git clone https://github.com/gokul27108/bulk-certificate-generator-api-.git
cd bulk-certificate-generator-api-

# Spin up PostgreSQL + FastAPI with a single command
docker compose up --build
```
The API is now live at `http://localhost:8000` with Swagger UI at `http://localhost:8000/docs`!

---

### Option 2: Local Setup (Native Python)

#### 1. Prerequisites
- Python 3.12+
- PostgreSQL 14+ (or SQLite for testing)

#### 2. Virtual Environment Setup
```bash
# Windows (PowerShell)
python -m venv venv
.\venv\Scripts\Activate.ps1

# Linux / macOS
python3 -m venv venv
source venv/bin/activate
```

#### 3. Install Dependencies
```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

#### 4. Environment Variables
```bash
# Copy template
cp .env.example .env
```
*Configure `.env` if using a local PostgreSQL database:*
```env
DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/certificate_db
TEST_DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/certificate_db_test
CERTIFICATE_OUTPUT_DIR=generated_certificates
APP_ENV=development
DEBUG=false
```

#### 5. Apply Database Migrations
```bash
alembic upgrade head
```

#### 6. Start the Application
```bash
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

---

## 📡 API Endpoints

| Method | Endpoint | Description | Status Code |
|---|---|---|---|
| `GET` | `/health` | Health probe & DB connectivity check | `200 OK` / `503 Degraded` |
| `POST` | `/api/v1/jobs` | Submit bulk certificate generation job | `202 Accepted` |
| `GET` | `/api/v1/jobs/{job_id}` | Poll generation job progress and recipient status | `200 OK` / `404 Not Found` |
| `GET` | `/api/v1/certificates/{certificate_id}` | Stream/download generated certificate PDF | `200 OK` / `404 Not Found` / `422 Unprocessable` |
| `GET` | `/docs` | Interactive Swagger UI documentation | `200 OK` |
| `GET` | `/redoc` | Interactive ReDoc documentation | `200 OK` |

---

## 💻 Sample API Usage (cURL)

### 1. Submit a Generation Job
```bash
curl -X POST "http://localhost:8000/api/v1/jobs" \
  -H "Content-Type: application/json" \
  -d '{
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
  }'
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

### 2. Check Job Progress
```bash
curl -X GET "http://localhost:8000/api/v1/jobs/4b92b67d-94e8-466a-9f5b-6f81e3c84792"
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

### 3. Download Generated Certificate
```bash
curl -O -J "http://localhost:8000/api/v1/certificates/8f8b86e1-95fa-4df3-a129-d5fc3ab9f2b1"
```
- Saved to: `certificate_Gokul_M.pdf`
- Validated with `%PDF-` binary magic bytes.

---

## 🧪 Testing & Code Coverage

Tests run against an isolated in-memory SQLite database, guaranteeing zero side effects on production data.

### Run All 52 Automated Tests
```bash
pytest
```

### Run Tests with Coverage Report
```bash
pytest --cov=app --cov-report=term-missing
```

### Coverage Summary (92% Total Coverage)
```text
=============================== tests coverage ================================
Name                                         Stmts   Miss  Cover   Missing
--------------------------------------------------------------------------
app\api\routes\certificates.py                  25      2    92%   68-73
app\api\routes\health.py                        12      0   100%
app\api\routes\jobs.py                          22      0   100%
app\core\config.py                              16      0   100%
app\core\database.py                            26     11    58%   57-61, 70-76
app\core\logging_config.py                      17      0   100%
app\exceptions\handlers.py                      40      4    90%   94-95, 103-104
app\main.py                                     31      0   100%
app\models\certificate.py                       27      1    96%   101
app\models\generation_job.py                    36      2    94%   117, 123
app\repositories\certificate_repository.py      48      0   100%
app\repositories\job_repository.py              59      8    86%   66-73
app\schemas\certificate.py                      22      0   100%
app\schemas\job.py                              51      0   100%
app\services\certificate_service.py             21      4    81%   44, 47, 51-56
app\services\job_service.py                     68      9    87%   108-115, 133-134
app\services\pdf_service.py                     19      1    95%   71
--------------------------------------------------------------------------
TOTAL                                          540     42    92%
============================= 52 passed in 49.73s =============================
```

---

## 📬 Postman Collection

Import the included Postman collection for rapid interactive testing:
1. Open Postman.
2. Click **Import** $\to$ Choose `postman/Bulk-Certificate-Generator.postman_collection.json`.
3. Collection variables `baseUrl`, `jobId`, and `certificateId` are automatically parsed and populated across requests!

---

## 📂 Project Structure

```text
bulk-certificate-generator-api/
├── app/
│   ├── main.py                     # Application startup, lifespan, and route wiring
│   ├── api/routes/                 # Endpoints: jobs.py, certificates.py, health.py
│   ├── core/                       # config.py, database.py, logging_config.py
│   ├── exceptions/                 # handlers.py (Centralized HTTP error handling)
│   ├── models/                     # generation_job.py, certificate.py (SQLAlchemy 2.x)
│   ├── repositories/               # job_repository.py, certificate_repository.py
│   ├── schemas/                    # job.py, certificate.py (Pydantic v2 validation)
│   └── services/                   # job_service.py, certificate_service.py, pdf_service.py
├── templates/
│   └── certificate_template.py     # ReportLab layout, borders, and styles
├── generated_certificates/         # Local PDF storage directory (.gitignore)
├── tests/                          # 52 automated tests covering all 6 mandatory areas
├── postman/                        # Postman Collection v2.1
├── alembic/                        # Database migrations
├── Dockerfile                      # Production container image
├── docker-compose.yml              # PostgreSQL + FastAPI Compose setup
├── REQUIREMENTS_CHECKLIST.md       # Traceability matrix mapping all requirements
├── INTERVIEW_PREPARATION.md        # Comprehensive 30-question technical interview guide
└── README.md                       # Documentation
```

---

## 👨‍💻 Author & Repository

- **Author**: Gokul M
- **Repository**: [https://github.com/gokul27108/bulk-certificate-generator-api-](https://github.com/gokul27108/bulk-certificate-generator-api-)
