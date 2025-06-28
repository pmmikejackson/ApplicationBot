from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import logging
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

app = FastAPI(title="ApplicationBot API")

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
            "application_url": "https://example.com/job1"
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
            "application_url": "https://example.com/job2"
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
        },
        2: {
            "id": 2,
            "job_id": 2,
            "status": "pending",
            "method": "manual",
            "submitted_at": None,
            "created_at": "2025-06-28T13:30:00Z",
        }
    }
}

@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    logger.info(f"Request: {request.method} {request.url}")
    response = await call_next(request)
    process_time = time.time() - start_time
    logger.info(f"Response: {response.status_code} - {process_time:.4f}s")
    return response

# CORS - Allow all origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,  # Set to False when using allow_origins=["*"]
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "ApplicationBot API is running"}

@app.get("/health")
async def health():
    return {"status": "healthy"}

@app.get("/api/v1/scrapers/status")
async def scrapers_status():
    """Get dynamic scraper status based on current data"""
    jobs = list(mock_data_store["jobs"].values())
    
    # Calculate real stats
    total_jobs = len(jobs)
    jobs_discovered_today = total_jobs  # For demo, assume all jobs were discovered today
    
    # Platform breakdown
    platform_breakdown = {}
    for job in jobs:
        platform = job["platform"]
        platform_breakdown[platform] = platform_breakdown.get(platform, 0) + 1
    
    # Status breakdown
    status_breakdown = {}
    for job in jobs:
        status = job["status"]
        status_breakdown[status] = status_breakdown.get(status, 0) + 1
    
    return {
        "total_jobs": total_jobs,
        "jobs_discovered_today": jobs_discovered_today,
        "platform_breakdown": platform_breakdown,
        "status_breakdown": status_breakdown,
        "last_scrape": "2025-06-28T15:30:00Z",
        "active_scrapers": 0
    }

from pydantic import BaseModel
from typing import List, Optional

class ScrapeRequest(BaseModel):
    keywords: List[str]
    location: str
    platforms: Optional[List[str]] = None
    remote_only: bool = False
    senior_level: bool = True
    salary_min: Optional[int] = None

@app.post("/api/v1/scrapers/scrape")
async def start_scraping_post(request: ScrapeRequest):
    """Start job scraping with test data"""
    return await start_scraping_logic(request)

@app.get("/api/v1/scrapers/scrape") 
async def start_scraping_get():
    """Start job scraping with test data"""
    return await start_scraping_logic()

async def start_scraping_logic(request: ScrapeRequest = None):
    """Start job scraping with test data"""
    if request:
        logger.info(f"Starting job scraping simulation with: {request.keywords} in {request.location}")
    else:
        logger.info("Starting job scraping simulation...")
    
    # Simulate scraping results
    mock_results = {
        "total_jobs_found": 25,
        "total_jobs_saved": 20,
        "platform_results": {
            "linkedin": {"found": 8, "saved": 7},
            "indeed": {"found": 10, "saved": 8},
            "builtin": {"found": 4, "saved": 3},
            "ziprecruiter": {"found": 3, "saved": 2}
        },
        "errors": []
    }
    
    logger.info(f"Scraping completed: {mock_results}")
    return mock_results

@app.get("/api/v1/jobs/")
async def get_jobs(status: str = "", platform: str = "", priority: str = ""):
    """Get jobs list with persistent mock data - handles query parameters"""
    logger.info(f"Getting jobs with filters: status={status}, platform={platform}, priority={priority}")
    
    jobs = list(mock_data_store["jobs"].values())
    
    # Apply filters if provided
    if status:
        jobs = [job for job in jobs if job["status"] == status]
    if platform:
        jobs = [job for job in jobs if job["platform"] == platform]
    if priority:
        jobs = [job for job in jobs if job["priority"] == priority]
    
    return jobs

@app.put("/api/v1/jobs/{job_id}")
async def update_job(job_id: int, job_update: dict):
    """Update a specific job with persistence and sync applications"""
    logger.info(f"Updating job {job_id} with data: {job_update}")
    
    if job_id not in mock_data_store["jobs"]:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Update the job in our persistent store
    job = mock_data_store["jobs"][job_id]
    job.update(job_update)
    
    # Sync application status based on job status
    if "status" in job_update:
        job_status = job_update["status"]
        
        # Check if application exists for this job
        existing_app = None
        for app_id, app in mock_data_store["applications"].items():
            if app["job_id"] == job_id:
                existing_app = app
                break
        
        if job_status == "applied" and not existing_app:
            # Create new application when job is marked as applied
            new_app_id = max(mock_data_store["applications"].keys(), default=0) + 1
            new_application = {
                "id": new_app_id,
                "job_id": job_id,
                "status": "submitted",
                "method": "automated",
                "submitted_at": "2025-06-28T15:30:00Z",
                "created_at": "2025-06-28T15:30:00Z"
            }
            mock_data_store["applications"][new_app_id] = new_application
            logger.info(f"Created new application {new_app_id} for job {job_id}")
        
        elif existing_app:
            # Update existing application status
            if job_status == "applied":
                existing_app["status"] = "submitted"
                if not existing_app.get("submitted_at"):
                    existing_app["submitted_at"] = "2025-06-28T15:30:00Z"
            elif job_status == "under_review":
                existing_app["status"] = "under_review"
            elif job_status == "interview_scheduled":
                existing_app["status"] = "interview_scheduled"
            elif job_status == "rejected":
                existing_app["status"] = "rejected"
            elif job_status == "discovered":
                existing_app["status"] = "pending"
    
    return job

@app.get("/api/v1/jobs/{job_id}")
async def get_job(job_id: int):
    """Get a specific job by ID with persistence"""
    logger.info(f"Getting job {job_id}")
    
    if job_id not in mock_data_store["jobs"]:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return mock_data_store["jobs"][job_id]

@app.get("/api/v1/applications/")
async def get_applications():
    """Get applications list with persistent data"""
    logger.info("Getting applications list")
    
    applications = []
    for app in mock_data_store["applications"].values():
        # Add job details to each application
        app_with_job = app.copy()
        if app["job_id"] in mock_data_store["jobs"]:
            job = mock_data_store["jobs"][app["job_id"]]
            app_with_job["job"] = {
                "id": job["id"],
                "title": job["title"],
                "company": job["company"],
                "location": job["location"]
            }
        applications.append(app_with_job)
    
    return applications

@app.put("/api/v1/applications/{application_id}")
async def update_application(application_id: int, update_data: dict):
    """Update an application status with persistence"""
    logger.info(f"Updating application {application_id} with data: {update_data}")
    
    if application_id not in mock_data_store["applications"]:
        raise HTTPException(status_code=404, detail="Application not found")
    
    # Update the application in our persistent store
    app = mock_data_store["applications"][application_id]
    app.update(update_data)
    
    # Add submitted_at timestamp if status changed to submitted
    if update_data.get("status") == "submitted" and not app.get("submitted_at"):
        app["submitted_at"] = "2025-06-28T15:30:00Z"
    
    # Return with job details
    app_with_job = app.copy()
    if app["job_id"] in mock_data_store["jobs"]:
        job = mock_data_store["jobs"][app["job_id"]]
        app_with_job["job"] = {
            "id": job["id"],
            "title": job["title"],
            "company": job["company"],
            "location": job["location"]
        }
    
    return app_with_job

@app.post("/api/v1/applications/{application_id}/follow-up")
async def send_follow_up(application_id: int):
    """Send follow-up email for an application"""
    logger.info(f"Sending follow-up email for application {application_id}")
    
    # In a real implementation, this would send an actual email
    return {
        "success": True,
        "message": "Follow-up email sent successfully",
        "sent_at": "2025-06-28T15:30:00Z"
    }

@app.get("/api/v1/jobs/stats/summary")
async def jobs_stats():
    """Get dynamic job statistics based on current data"""
    jobs = list(mock_data_store["jobs"].values())
    
    # Calculate real stats
    total_jobs = len(jobs)
    applied_jobs = len([j for j in jobs if j["status"] == "applied"])
    high_priority_jobs = len([j for j in jobs if j["priority"] == "must_apply"])
    
    # Platform breakdown
    platform_breakdown = {}
    for job in jobs:
        platform = job["platform"]
        platform_breakdown[platform] = platform_breakdown.get(platform, 0) + 1
    
    # Status breakdown
    status_breakdown = {}
    for job in jobs:
        status = job["status"]
        status_breakdown[status] = status_breakdown.get(status, 0) + 1
    
    # Priority breakdown
    priority_breakdown = {}
    for job in jobs:
        priority = job["priority"]
        priority_breakdown[priority] = priority_breakdown.get(priority, 0) + 1
    
    return {
        "total_jobs": total_jobs,
        "applied_jobs": applied_jobs,
        "high_priority_jobs": high_priority_jobs,
        "platform_breakdown": platform_breakdown,
        "status_breakdown": status_breakdown,
        "priority_breakdown": priority_breakdown
    }