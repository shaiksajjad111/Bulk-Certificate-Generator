
import pytest
from fastapi.testclient import TestClient

import main
from main import app
from database import Base, engine
from certificates import generate_certificate


@pytest.fixture()
def client():
    # Create a fresh database schema for each test.
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    with TestClient(app) as test_client:
        yield test_client

    Base.metadata.drop_all(bind=engine)


def test_home_endpoint(client):
    response = client.get("/")
    assert response.status_code == 200
    assert "running" in response.json()["message"]


def test_create_generation_job(client):
    response = client.post(
        "/api/jobs",
        json={
            "recipients": [
                {
                    "name": "Rahul Sharma",
                    "email": "rahul@example.com",
                    "course": "Python Basics",
                },
                {
                    "name": "Priya Kumar",
                    "email": "priya@example.com",
                    "course": "Web Development",
                },
            ]
        },
    )

    assert response.status_code == 202
    data = response.json()
    assert data["job_id"] > 0
    assert data["total"] == 2


def test_invalid_email_is_rejected(client):
    response = client.post(
        "/api/jobs",
        json={
            "recipients": [
                {
                    "name": "Rahul Sharma",
                    "email": "not-an-email",
                    "course": "Python Basics",
                }
            ]
        },
    )

    assert response.status_code == 422


def test_empty_recipient_list_is_rejected(client):
    response = client.post(
        "/api/jobs",
        json={"recipients": []},
    )

    assert response.status_code == 422


def test_job_status_and_progress(client):
    response = client.post(
        "/api/jobs",
        json={
            "recipients": [
                {
                    "name": "Test User",
                    "email": "test@example.com",
                    "course": "Testing",
                }
            ]
        },
    )

    job_id = response.json()["job_id"]

    # FastAPI's TestClient waits for its background tasks to finish.
    status_response = client.get(f"/api/jobs/{job_id}")

    assert status_response.status_code == 200
    data = status_response.json()
    assert data["status"] == "COMPLETED"
    assert data["total"] == 1
    assert data["successful"] == 1
    assert data["failed"] == 0
    assert data["progress_percent"] == 100


def test_individual_certificate_failure_does_not_stop_job(
    client, monkeypatch
):
    original_generator = main.generate_certificate

    def failing_generator(name, course, recipient_id):
        if name == "Failure Test":
            raise RuntimeError("Simulated PDF generation failure")

        return original_generator(name, course, recipient_id)

    monkeypatch.setattr(main, "generate_certificate", failing_generator)

    response = client.post(
        "/api/jobs",
        json={
            "recipients": [
                {
                    "name": "Success Test",
                    "email": "success@example.com",
                    "course": "Python Basics",
                },
                {
                    "name": "Failure Test",
                    "email": "failure@example.com",
                    "course": "Python Basics",
                },
            ]
        },
    )

    job_id = response.json()["job_id"]
    status_response = client.get(f"/api/jobs/{job_id}")
    data = status_response.json()

    assert data["successful"] == 1
    assert data["failed"] == 1
    assert data["status"] == "COMPLETED_WITH_ERRORS"


def test_generated_certificate_can_be_downloaded(client):
    response = client.post(
        "/api/jobs",
        json={
            "recipients": [
                {
                    "name": "Download Test",
                    "email": "download@example.com",
                    "course": "Python Basics",
                }
            ]
        },
    )

    job_id = response.json()["job_id"]

    recipients_response = client.get(
        f"/api/jobs/{job_id}/recipients"
    )
    assert recipients_response.status_code == 200

    recipient = recipients_response.json()["recipients"][0]
    recipient_id = recipient["id"]

    download_response = client.get(
        f"/api/certificates/{recipient_id}/download"
    )

    assert download_response.status_code == 200
    assert download_response.headers["content-type"] == "application/pdf"
    assert download_response.content.startswith(b"%PDF")


def test_missing_job_returns_404(client):
    response = client.get("/api/jobs/999999")
    assert response.status_code == 404
