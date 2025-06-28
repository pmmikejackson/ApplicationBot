from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, JSON
from sqlalchemy.sql import func
from app.core.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    
    # Profile information
    first_name = Column(String(100))
    last_name = Column(String(100))
    phone = Column(String(20))
    linkedin_url = Column(String(500))
    portfolio_url = Column(String(500))
    
    # Job search preferences
    target_titles = Column(JSON)  # List of target job titles
    skills = Column(JSON)  # List of skills
    years_experience = Column(Integer, default=0)
    salary_min = Column(Integer)
    salary_max = Column(Integer)
    location_preferences = Column(JSON)  # Location preferences
    remote_preference = Column(Boolean, default=True)
    
    # Document templates
    resume_template_path = Column(String(500))
    cover_letter_template = Column(Text)
    
    # Platform credentials (encrypted)
    linkedin_username = Column(String(255))
    linkedin_password = Column(String(255))  # Encrypted
    indeed_username = Column(String(255))
    indeed_password = Column(String(255))  # Encrypted
    
    # Settings
    auto_apply_enabled = Column(Boolean, default=False)
    notification_preferences = Column(JSON)
    
    # Metadata
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    last_login = Column(DateTime)