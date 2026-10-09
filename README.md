
# Bulk Certificate Generator API

A Python backend API that generates PDF certificates for multiple recipients in one request.

## Features

- Bulk certificate generation
- Recipient input validation
- Background job processing
- Job status and progress tracking
- Individual certificate failure handling
- PDF certificate downloads
- SQLite database storage
- Automated tests

## Technology Stack

- Python 3.12
- FastAPI
- Uvicorn
- SQLAlchemy
- SQLite
- ReportLab
- Pytest and HTTPX

## Project Structure

- `main.py` — API endpoints and job processing
- `database.py` — database connection and sessions
- `models.py` — job and recipient database models
- `schemas.py` — request validation
- `certificates.py` — PDF certificate generation
- `tests/` — automated tests
- `generated/` — generated PDF certificates
- `certificates.db` — local SQLite database

## Setup

Create and activate a virtual environment:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Install dependencies:

```powershell
python -m pip install -r requirements.txt
```

## Run the Application

```powershell
python -m uvicorn main:app --reload
```

Open the interactive API documentation:

http://127.0.0.1:8000/docs

## API Endpoints

### Submit a generation job

`POST /api/jobs`

Example request:

```json
{
  "recipients": [
    {
      "name": "Rahul Sharma",
      "email": "rahul@example.com",
      "course": "Python Basics"
    },
    {
      "name": "Priya Kumar",
      "email": "priya@example.com",
      "course": "Web Development"
    }
  ]
}
```

The response includes the job ID and status URLs.

### Get job status

`GET /api/jobs/{job_id}`

Returns the job status, total recipients, successful generations,
failures, pending count, and progress percentage.

### Get recipient results

`GET /api/jobs/{job_id}/recipients`

Returns individual recipient statuses and available download URLs.

### Download a certificate

`GET /api/certificates/{recipient_id}/download`

Returns the generated PDF certificate.

## Run Tests

```powershell
python -m pytest tests/test_main.py -v
```

The tests cover job creation, validation, progress, individual
certificate failures, downloads, and missing jobs.

## Architecture and Design Decisions

FastAPI provides request validation and HTTP endpoints.
SQLAlchemy separates database operations from API logic.
SQLite provides simple local persistence without a separate server.
ReportLab generates PDF certificates from a predefined design.

Each recipient is processed independently so that a failure generating
one certificate does not prevent other recipients from being processed.

FastAPI BackgroundTasks provides lightweight background processing
for this assessment. A production system could use a task queue,
persistent job workers, and retry policies for larger workloads.

## Learning and Future Scope

This project helped me practise Python backend development, REST API
design, database modelling, validation, PDF generation, and automated
testing.

Future improvements include a more configurable certificate template,
CSV or Excel imports, authentication, a dedicated task queue,
production database support, and deployment.
