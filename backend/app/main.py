from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from app.api.api_v1.api import api_router
from app.core.config import settings
import logging
import time
from datetime import datetime
from typing import Dict, Any, List, Optional
from pydantic import BaseModel

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Create FastAPI application
app = FastAPI(
    title="ApplicationBot",
    description="Automated job application system with OAuth2 email integration",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# In-memory storage for mock data persistence
mock_data_store = {
    "jobs": {
        1: {
            "id": 1,
            "title": "Senior Product Manager",
            "company": "TechCorp",
            "location": "Remote",
            "salary_min": 120000,
            "salary_max": 150000,
            "platform": "linkedin",
            "status": "discovered",
            "priority": "good_fit",
            "fit_score": 8.5,
            "posted_date": "2025-06-28T10:00:00Z",
            "discovered_at": "2025-06-28T15:00:00Z",
            "is_remote": True,
            "is_hybrid": False,
            "application_url": "https://example.com/job1",
            "source": "manual"
        },
        2: {
            "id": 2,
            "title": "Director of Product",
            "company": "StartupXYZ",
            "location": "San Francisco, CA",
            "salary_min": 180000,
            "salary_max": 220000,
            "platform": "indeed",
            "status": "discovered",
            "priority": "must_apply",
            "fit_score": 9.2,
            "posted_date": "2025-06-27T14:00:00Z",
            "discovered_at": "2025-06-28T14:30:00Z",
            "is_remote": False,
            "is_hybrid": True,
            "application_url": "https://example.com/job2",
            "source": "manual"
        },
        3: {
            "id": 3,
            "title": "VP of Product Management",
            "company": "Enterprise Solutions Inc",
            "location": "New York, NY",
            "salary_min": 250000,
            "salary_max": 300000,
            "platform": "builtin",
            "status": "discovered",
            "priority": "stretch",
            "fit_score": 7.8,
            "posted_date": "2025-06-26T09:00:00Z",
            "discovered_at": "2025-06-28T12:45:00Z",
            "is_remote": False,
            "is_hybrid": False,
            "application_url": "https://builtin.com/jobs/54321",
            "source": "manual"
        }
    },
    "applications": {
        1: {
            "id": 1,
            "job_id": 1,
            "status": "submitted",
            "method": "automated",
            "submitted_at": "2025-06-28T14:00:00Z",
            "created_at": "2025-06-28T14:00:00Z",
            "error_message": None
        },
        2: {
            "id": 2,
            "job_id": 2,
            "status": "pending",
            "method": "manual",
            "submitted_at": None,
            "created_at": "2025-06-28T13:30:00Z",
            "error_message": None
        }
    }
}

# Request/response logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    logger.info(f"Request: {request.method} {request.url}")
    response = await call_next(request)
    process_time = time.time() - start_time
    logger.info(f"Response: {response.status_code} - {process_time:.4f}s")
    return response

# CORS middleware for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=False,  # Set to False when using allow_origins=["*"]
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include all API routes (OAuth2, email-parser, jobs, applications, etc.)
app.include_router(api_router, prefix="/api/v1")

# Root endpoint
@app.get("/")
async def root():
    return {
        "message": "ApplicationBot API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
        "features": [
            "Job discovery and management",
            "Application tracking with Kanban workflow", 
            "OAuth2 email parsing integration",
            "Automated background processing",
            "RESTful API with OpenAPI documentation"
        ]
    }

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0",
        "services": {
            "api": "running",
            "mock_data": "available",
            "oauth": "configured" if settings.EMAIL_PARSING_ENABLED else "not_configured"
        }
    }

# Legacy endpoints for backward compatibility (these will be handled by the API router now)
class ScrapeRequest(BaseModel):
    keywords: List[str]
    location: str
    platforms: Optional[List[str]] = None
    remote_only: bool = False
    senior_level: bool = True
    salary_min: Optional[int] = None

# Mock data access functions used by API endpoints
def get_mock_jobs():
    """Get all jobs from mock data store"""
    return list(mock_data_store["jobs"].values())

def get_mock_job(job_id: int):
    """Get specific job from mock data store"""
    return mock_data_store["jobs"].get(job_id)

def update_mock_job(job_id: int, updates: Dict[str, Any]):
    """Update job in mock data store"""
    if job_id in mock_data_store["jobs"]:
        mock_data_store["jobs"][job_id].update(updates)
        return mock_data_store["jobs"][job_id]
    return None

def get_mock_applications():
    """Get all applications from mock data store"""
    return list(mock_data_store["applications"].values())

def get_mock_application(app_id: int):
    """Get specific application from mock data store"""
    return mock_data_store["applications"].get(app_id)

def update_mock_application(app_id: int, updates: Dict[str, Any]):
    """Update application in mock data store"""
    if app_id in mock_data_store["applications"]:
        mock_data_store["applications"][app_id].update(updates)
        return mock_data_store["applications"][app_id]
    return None

# Startup event
@app.on_event("startup")
async def startup_event():
    """Application startup tasks"""
    logger.info("ApplicationBot API starting up...")
    logger.info(f"Mock data initialized with {len(mock_data_store['jobs'])} jobs and {len(mock_data_store['applications'])} applications")
    
    # Check OAuth2 configuration
    try:
        import os
        if os.path.exists("/app/oauth_credentials.json"):
            logger.info("OAuth2 credentials found - email processing available")
        elif all([settings.IMAP_SERVER, settings.IMAP_USER, settings.IMAP_PASSWORD]) and settings.EMAIL_PARSING_ENABLED:
            logger.info("IMAP credentials configured - email processing available")
        else:
            logger.info("No email authentication configured - manual job entry only")
    except Exception as e:
        logger.warning(f"Error checking email configuration: {e}")
    
    logger.info("ApplicationBot API startup complete")

# Shutdown event  
@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown tasks"""
    logger.info("ApplicationBot API shutting down...")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)