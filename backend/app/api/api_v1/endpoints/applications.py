from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from app.core.database import get_db
from app.models.application import Application, ApplicationStatus, ApplicationMethod
from app.services.application_service import ApplicationService
from pydantic import BaseModel
from datetime import datetime

router = APIRouter()

class ApplicationResponse(BaseModel):
    id: int
    job_id: int
    status: ApplicationStatus
    method: ApplicationMethod
    submission_id: Optional[str]
    resume_path: Optional[str]
    cover_letter_path: Optional[str]
    portfolio_url: Optional[str]
    salary_expectation: Optional[str]
    availability_date: Optional[str]
    work_authorization: Optional[str]
    submitted_at: Optional[datetime]
    created_at: datetime
    error_message: Optional[str]
    retry_count: Optional[int]

    class Config:
        from_attributes = True

class ApplicationCreate(BaseModel):
    job_id: int
    resume_path: Optional[str] = None
    cover_letter_path: Optional[str] = None
    portfolio_url: Optional[str] = None
    salary_expectation: Optional[str] = None
    availability_date: Optional[str] = None
    work_authorization: Optional[str] = None
    custom_responses: Optional[str] = None

class ApplicationUpdate(BaseModel):
    status: Optional[ApplicationStatus] = None
    submission_id: Optional[str] = None
    error_message: Optional[str] = None

@router.get("/", response_model=List[ApplicationResponse])
def get_applications(
    skip: int = 0,
    limit: int = 100,
    status: Optional[ApplicationStatus] = None,
    job_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    app_service = ApplicationService(db)
    return app_service.get_applications(
        skip=skip,
        limit=limit,
        status=status,
        job_id=job_id
    )

@router.get("/{application_id}", response_model=ApplicationResponse)
def get_application(application_id: int, db: Session = Depends(get_db)):
    app_service = ApplicationService(db)
    application = app_service.get_application(application_id)
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    return application

@router.post("/", response_model=ApplicationResponse)
def create_application(
    application_data: ApplicationCreate,
    db: Session = Depends(get_db)
):
    app_service = ApplicationService(db)
    return app_service.create_application(application_data.dict())

@router.put("/{application_id}", response_model=ApplicationResponse)
def update_application(
    application_id: int,
    application_update: ApplicationUpdate,
    db: Session = Depends(get_db)
):
    app_service = ApplicationService(db)
    application = app_service.update_application(
        application_id,
        application_update.dict(exclude_unset=True)
    )
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    return application

@router.delete("/{application_id}")
def delete_application(application_id: int, db: Session = Depends(get_db)):
    app_service = ApplicationService(db)
    success = app_service.delete_application(application_id)
    if not success:
        raise HTTPException(status_code=404, detail="Application not found")
    return {"message": "Application deleted successfully"}

@router.post("/{application_id}/retry")
def retry_application(application_id: int, db: Session = Depends(get_db)):
    app_service = ApplicationService(db)
    result = app_service.retry_application(application_id)
    if not result:
        raise HTTPException(status_code=404, detail="Application not found")
    return result

@router.get("/stats/summary")
def get_application_stats(db: Session = Depends(get_db)):
    app_service = ApplicationService(db)
    return app_service.get_application_statistics()