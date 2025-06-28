from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
from app.core.database import get_db
from app.models.job import JobPlatform
from app.services.scraper_service import ScraperService
from pydantic import BaseModel

router = APIRouter()

class ScrapeRequest(BaseModel):
    keywords: List[str]
    location: str
    platforms: Optional[List[JobPlatform]] = None
    remote_only: bool = False
    senior_level: bool = True
    salary_min: Optional[int] = None

class ScrapeResponse(BaseModel):
    total_jobs_found: int
    total_jobs_saved: int
    platform_results: dict
    errors: List[str]

@router.post("/scrape", response_model=ScrapeResponse)
async def scrape_jobs(
    scrape_request: ScrapeRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Scrape jobs from specified platforms"""
    scraper_service = ScraperService(db)
    
    try:
        results = await scraper_service.scrape_all_platforms(
            keywords=scrape_request.keywords,
            location=scrape_request.location,
            platforms=scrape_request.platforms,
            remote_only=scrape_request.remote_only,
            senior_level=scrape_request.senior_level,
            salary_min=scrape_request.salary_min
        )
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Scraping failed: {str(e)}")

@router.post("/scrape/{platform}")
def scrape_single_platform(
    platform: JobPlatform,
    scrape_request: ScrapeRequest,
    db: Session = Depends(get_db)
):
    """Scrape jobs from a single platform"""
    scraper_service = ScraperService(db)
    
    try:
        result = scraper_service.scrape_single_platform(
            platform=platform,
            keywords=scrape_request.keywords,
            location=scrape_request.location,
            remote_only=scrape_request.remote_only,
            senior_level=scrape_request.senior_level,
            salary_min=scrape_request.salary_min
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Scraping {platform.value} failed: {str(e)}")

@router.get("/status")
def get_scraping_status(db: Session = Depends(get_db)):
    """Get current scraping status and statistics"""
    scraper_service = ScraperService(db)
    return scraper_service.get_scraping_status()

@router.get("/test/{platform}")
def test_platform_connection(platform: JobPlatform, db: Session = Depends(get_db)):
    """Test connection to a specific platform"""
    scraper_service = ScraperService(db)
    return scraper_service.test_platform_connection(platform)

@router.get("/platforms")
def get_supported_platforms():
    """Get list of supported job platforms"""
    return {
        "platforms": [
            {
                "name": platform.value,
                "display_name": platform.value.replace('_', ' ').title(),
                "requires_login": platform in [JobPlatform.LINKEDIN, JobPlatform.INDEED]
            }
            for platform in JobPlatform
        ]
    }