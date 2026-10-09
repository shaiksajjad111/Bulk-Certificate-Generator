
from pathlib import Path

from fastapi import FastAPI, BackgroundTasks, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from database import Base, engine, SessionLocal, get_db
from models import Job, Recipient
from schemas import GenerationRequest
from certificates import generate_certificate


# Create database tables if they do not exist.
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Bulk Certificate Generator API",
    description="Generate and retrieve certificates for multiple recipients.",
    version="1.0.0",
)


@app.get("/")
def home():
    return {
        "message": "Bulk Certificate Generator API is running",
        "docs": "/docs",
    }


def process_job(job_id: int):
    """Generate certificates independently for every recipient."""
    db = SessionLocal()

    try:
        job = db.query(Job).filter(Job.id == job_id).first()

        if job is None:
            return

        job.status = "PROCESSING"
        db.commit()

        recipients = (
            db.query(Recipient)
            .filter(Recipient.job_id == job_id)
            .all()
        )

        for recipient in recipients:
            try:
                # Generate the PDF for this recipient.
                path = generate_certificate(
                    name=recipient.name,
                    course=recipient.course,
                    recipient_id=recipient.id,
                )

                recipient.certificate_path = path
                recipient.status = "COMPLETED"
                recipient.error = None

            except Exception as exc:
                # Record this failure and continue with other recipients.
                recipient.status = "FAILED"
                recipient.error = str(exc)[:500]
                recipient.certificate_path = None

            # Save each result so progress can be checked during processing.
            db.commit()

        db.refresh(job)

        job.successful = (
            db.query(Recipient)
            .filter(
                Recipient.job_id == job_id,
                Recipient.status == "COMPLETED",
            )
            .count()
        )

        job.failed = (
            db.query(Recipient)
            .filter(
                Recipient.job_id == job_id,
                Recipient.status == "FAILED",
            )
            .count()
        )

        if job.failed == 0:
            job.status = "COMPLETED"
        elif job.successful == 0:
            job.status = "FAILED"
        else:
            job.status = "COMPLETED_WITH_ERRORS"

        db.commit()

    except Exception:
        db.rollback()

        job = db.query(Job).filter(Job.id == job_id).first()
        if job is not None:
            job.status = "FAILED"
            db.commit()

    finally:
        db.close()


@app.post("/api/jobs", status_code=202)
def create_generation_job(
    request: GenerationRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    # Create the job first.
    job = Job(
        status="PENDING",
        total=len(request.recipients),
        successful=0,
        failed=0,
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    # Save every recipient before starting the background task.
    for item in request.recipients:
        recipient = Recipient(
            job_id=job.id,
            name=item.name.strip(),
            email=str(item.email),
            course=item.course.strip(),
            status="PENDING",
        )
        db.add(recipient)

    db.commit()

    background_tasks.add_task(process_job, job.id)

    return {
        "job_id": job.id,
        "status": "PENDING",
        "total": job.total,
        "message": "Certificate generation job accepted.",
        "status_url": f"/api/jobs/{job.id}",
        "recipients_url": f"/api/jobs/{job.id}/recipients",
    }


@app.get("/api/jobs/{job_id}")
def get_job_status(
    job_id: int,
    db: Session = Depends(get_db),
):
    job = db.query(Job).filter(Job.id == job_id).first()

    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")

    return {
        "job_id": job.id,
        "status": job.status,
        "total": job.total,
        "successful": job.successful,
        "failed": job.failed,
        "pending": max(
            0, job.total - job.successful - job.failed
        ),
        "progress_percent": round(
            (job.successful + job.failed) / job.total * 100, 2
        ) if job.total else 0,
        "created_at": job.created_at,
    }


@app.get("/api/jobs/{job_id}/recipients")
def get_job_recipients(
    job_id: int,
    db: Session = Depends(get_db),
):
    job = db.query(Job).filter(Job.id == job_id).first()

    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")

    recipients = (
        db.query(Recipient)
        .filter(Recipient.job_id == job_id)
        .all()
    )

    return {
        "job_id": job.id,
        "recipients": [
            {
                "id": item.id,
                "name": item.name,
                "email": item.email,
                "course": item.course,
                "status": item.status,
                "error": item.error,
                "download_url": (
                    f"/api/certificates/{item.id}/download"
                    if item.status == "COMPLETED"
                    else None
                ),
            }
            for item in recipients
        ],
    }


@app.get("/api/certificates/{recipient_id}/download")
def download_certificate(
    recipient_id: int,
    db: Session = Depends(get_db),
):
    recipient = (
        db.query(Recipient)
        .filter(Recipient.id == recipient_id)
        .first()
    )

    if recipient is None:
        raise HTTPException(
            status_code=404,
            detail="Recipient not found",
        )

    if recipient.status != "COMPLETED" or not recipient.certificate_path:
        raise HTTPException(
            status_code=409,
            detail="Certificate is not available",
        )

    path = Path(recipient.certificate_path).resolve()
    output_dir = Path(__file__).resolve().parent / "generated"

    # Ensure the requested file is inside our generated directory.
    if not path.is_relative_to(output_dir.resolve()) or not path.is_file():
        raise HTTPException(
            status_code=404,
            detail="Certificate file not found",
        )

    return FileResponse(
        path=str(path),
        media_type="application/pdf",
        filename=path.name,
    )
