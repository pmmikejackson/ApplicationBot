from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.core.database import get_db
from app.models.job import Job, JobStatus, JobPlatform, JobPriority
from app.services.job_service import JobService
from pydantic import BaseModel
from datetime import datetime

router = APIRouter()

class JobResponse(BaseModel):
    id: int
    title: str
    company: str
    location: Optional[str]
    salary_min: Optional[int]
    salary_max: Optional[int]
    description: Optional[str]
    application_url: str
    platform: JobPlatform
    fit_score: float
    priority: JobPriority
    status: JobStatus
    posted_date: Optional[datetime]
    discovered_at: datetime
    is_remote: bool
    is_hybrid: bool

    class Config:
        from_attributes = True

class JobUpdate(BaseModel):
    status: Optional[JobStatus] = None
    priority: Optional[JobPriority] = None
    fit_score: Optional[float] = None

@router.get("/", response_model=List[JobResponse])
def get_jobs(
    skip: int = 0,
    limit: int = 100,
    status: Optional[JobStatus] = None,
    platform: Optional[JobPlatform] = None,
    priority: Optional[JobPriority] = None,
    min_fit_score: Optional[float] = None,
    db: Session = Depends(get_db)
):
    job_service = JobService(db)
    return job_service.get_jobs(
        skip=skip,
        limit=limit,
        status=status,
        platform=platform,
        priority=priority,
        min_fit_score=min_fit_score
    )

@router.get("/{job_id}", response_model=JobResponse)
def get_job(job_id: int, db: Session = Depends(get_db)):
    job_service = JobService(db)
    job = job_service.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job

@router.put("/{job_id}", response_model=JobResponse)
def update_job(job_id: int, job_update: JobUpdate, db: Session = Depends(get_db)):
    job_service = JobService(db)
    job = job_service.update_job(job_id, job_update.dict(exclude_unset=True))
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job

@router.delete("/{job_id}")
def delete_job(job_id: int, db: Session = Depends(get_db)):
    job_service = JobService(db)
    success = job_service.delete_job(job_id)
    if not success:
        raise HTTPException(status_code=404, detail="Job not found")
    return {"message": "Job deleted successfully"}

@router.get("/stats/summary")
def get_job_stats(db: Session = Depends(get_db)):
    job_service = JobService(db)
    return job_service.get_job_statistics()