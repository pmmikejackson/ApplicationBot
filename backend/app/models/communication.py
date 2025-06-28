from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
import enum

class CommunicationType(str, enum.Enum):
    EMAIL = "email"
    PHONE = "phone"
    MESSAGE = "message"
    INTERVIEW = "interview"

class CommunicationDirection(str, enum.Enum):
    INBOUND = "inbound"
    OUTBOUND = "outbound"

class CommunicationStatus(str, enum.Enum):
    SENT = "sent"
    RECEIVED = "received"
    SCHEDULED = "scheduled"
    FAILED = "failed"

class Communication(Base):
    __tablename__ = "communications"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("jobs.id"), nullable=False)
    
    # Communication details
    type = Column(Enum(CommunicationType), nullable=False)
    direction = Column(Enum(CommunicationDirection), nullable=False)
    status = Column(Enum(CommunicationStatus), default=CommunicationStatus.SENT)
    
    # Content
    subject = Column(String(500))
    content = Column(Text)
    sender_email = Column(String(255))
    recipient_email = Column(String(255))
    
    # Scheduling
    scheduled_at = Column(DateTime)
    sent_at = Column(DateTime)
    
    # Metadata
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Automation
    is_automated = Column(Boolean, default=True)
    template_used = Column(String(255))
    
    # Relationships
    job = relationship("Job", back_populates="communications")