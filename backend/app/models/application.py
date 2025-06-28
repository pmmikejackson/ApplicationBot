from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
import enum

class ApplicationStatus(str, enum.Enum):
    PENDING = "pending"
    SUBMITTED = "submitted"
    FAILED = "failed"
    WITHDRAWN = "withdrawn"

class ApplicationMethod(str, enum.Enum):
    AUTOMATED = "automated"
    MANUAL = "manual"
    SEMI_AUTOMATED = "semi_automated"

class Application(Base):
    __tablename__ = "applications"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("jobs.id"), nullable=False)
    
    # Application details
    status = Column(Enum(ApplicationStatus), default=ApplicationStatus.PENDING)
    method = Column(Enum(ApplicationMethod), default=ApplicationMethod.AUTOMATED)
    submission_id = Column(String(255))  # Platform-specific application ID
    
    # Documents used
    resume_path = Column(String(500))
    cover_letter_path = Column(String(500))
    portfolio_url = Column(String(500))
    
    # Form data
    salary_expectation = Column(String(100))
    availability_date = Column(String(100))
    work_authorization = Column(String(100))
    
    # Custom responses
    custom_responses = Column(Text)  # JSON field for custom question responses
    
    # Tracking
    submitted_at = Column(DateTime)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Error handling
    error_message = Column(Text)
    retry_count = Column(Integer, default=0)
    
    # Relationships
    job = relationship("Job", back_populates="applications")