from sqlalchemy import Column, Integer, String, Text, DateTime, Float, Boolean, Enum, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
import enum

class JobStatus(str, enum.Enum):
    DISCOVERED = "discovered"
    FILTERED = "filtered"
    APPLIED = "applied"
    UNDER_REVIEW = "under_review"
    INTERVIEW_SCHEDULED = "interview_scheduled"
    REJECTED = "rejected"
    OFFER_RECEIVED = "offer_received"
    WITHDRAWN = "withdrawn"

class JobPlatform(str, enum.Enum):
    LINKEDIN = "linkedin"
    INDEED = "indeed"
    BUILTIN = "builtin"
    ZIPRECRUITER = "ziprecruiter"

class JobPriority(str, enum.Enum):
    MUST_APPLY = "must_apply"
    GOOD_FIT = "good_fit"
    STRETCH = "stretch"
    LOW_PRIORITY = "low_priority"

class Job(Base):
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False, index=True)
    company = Column(String(255), nullable=False, index=True)
    location = Column(String(255))
    salary_min = Column(Integer)
    salary_max = Column(Integer)
    description = Column(Text)
    requirements = Column(Text)
    application_url = Column(String(500), nullable=False)
    platform = Column(Enum(JobPlatform), nullable=False)
    platform_id = Column(String(100), unique=True, index=True)
    
    # Scoring and matching
    fit_score = Column(Float, default=0.0)
    priority = Column(Enum(JobPriority), default=JobPriority.LOW_PRIORITY)
    
    # Status tracking
    status = Column(Enum(JobStatus), default=JobStatus.DISCOVERED)
    applied_at = Column(DateTime)
    response_deadline = Column(DateTime)
    
    # Metadata
    posted_date = Column(DateTime)
    discovered_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Remote work
    is_remote = Column(Boolean, default=False)
    is_hybrid = Column(Boolean, default=False)
    
    # Relationships
    applications = relationship("Application", back_populates="job")
    communications = relationship("Communication", back_populates="job")