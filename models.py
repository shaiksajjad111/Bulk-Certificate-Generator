
from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    ForeignKey,
)
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from database import Base


class Job(Base):
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, index=True)
    status = Column(String, default="PENDING")
    total = Column(Integer, default=0)
    successful = Column(Integer, default=0)
    failed = Column(Integer, default=0)
    created_at = Column(DateTime, server_default=func.now())

    recipients = relationship(
        "Recipient",
        back_populates="job",
        cascade="all, delete-orphan",
    )


class Recipient(Base):
    __tablename__ = "recipients"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("jobs.id"))

    name = Column(String, nullable=False)
    email = Column(String, nullable=False)
    course = Column(String, nullable=False)

    status = Column(String, default="PENDING")
    certificate_path = Column(String, nullable=True)
    error = Column(String, nullable=True)

    job = relationship(
        "Job",
        back_populates="recipients",
    )
