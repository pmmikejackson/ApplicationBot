from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from app.core.database import get_db
from app.models.communication import Communication, CommunicationType, CommunicationDirection, CommunicationStatus
from app.services.communication_service import CommunicationService
from pydantic import BaseModel
from datetime import datetime

router = APIRouter()

class CommunicationResponse(BaseModel):
    id: int
    job_id: int
    type: CommunicationType
    direction: CommunicationDirection
    status: CommunicationStatus
    subject: Optional[str]
    content: Optional[str]
    sender_email: Optional[str]
    recipient_email: Optional[str]
    scheduled_at: Optional[datetime]
    sent_at: Optional[datetime]
    created_at: datetime
    is_automated: Optional[bool]
    template_used: Optional[str]

    class Config:
        from_attributes = True

class FollowUpRequest(BaseModel):
    message: Optional[str] = None
    template_type: str = "follow_up"

class ScheduleFollowUpRequest(BaseModel):
    days_delay: int = 7
    template_type: str = "follow_up"

class ThankYouRequest(BaseModel):
    interviewer_email: str
    interviewer_name: str
    interview_date: datetime

@router.get("/", response_model=List[CommunicationResponse])
def get_communications(
    skip: int = 0,
    limit: int = 100,
    job_id: Optional[int] = None,
    type: Optional[CommunicationType] = None,
    status: Optional[CommunicationStatus] = None,
    db: Session = Depends(get_db)
):
    comm_service = CommunicationService(db)
    
    query = db.query(Communication)
    
    if job_id:
        query = query.filter(Communication.job_id == job_id)
    if type:
        query = query.filter(Communication.type == type)
    if status:
        query = query.filter(Communication.status == status)
        
    return query.order_by(Communication.created_at.desc()).offset(skip).limit(limit).all()

@router.get("/{communication_id}", response_model=CommunicationResponse)
def get_communication(communication_id: int, db: Session = Depends(get_db)):
    communication = db.query(Communication).filter(Communication.id == communication_id).first()
    if not communication:
        raise HTTPException(status_code=404, detail="Communication not found")
    return communication

@router.post("/follow-up/{job_id}")
def send_follow_up(
    job_id: int,
    request: FollowUpRequest,
    db: Session = Depends(get_db)
):
    from app.models.job import Job
    from app.models.application import Application
    
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
        
    application = db.query(Application).filter(Application.job_id == job_id).first()
    if not application:
        raise HTTPException(status_code=404, detail="No application found for this job")
    
    comm_service = CommunicationService(db)
    success = comm_service.send_follow_up_email(
        job, application, request.template_type, request.message
    )
    
    if success:
        return {"message": "Follow-up email sent successfully"}
    else:
        raise HTTPException(status_code=500, detail="Failed to send follow-up email")

@router.post("/schedule-follow-up/{job_id}")
def schedule_follow_up(
    job_id: int,
    request: ScheduleFollowUpRequest,
    db: Session = Depends(get_db)
):
    from app.models.job import Job
    from app.models.application import Application
    
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
        
    application = db.query(Application).filter(Application.job_id == job_id).first()
    if not application:
        raise HTTPException(status_code=404, detail="No application found for this job")
    
    comm_service = CommunicationService(db)
    communication = comm_service.schedule_follow_up(
        job, application, request.days_delay, request.template_type
    )
    
    return {
        "message": f"Follow-up scheduled for {request.days_delay} days",
        "communication_id": communication.id,
        "scheduled_at": communication.scheduled_at
    }

@router.post("/thank-you/{job_id}")
def send_thank_you(
    job_id: int,
    request: ThankYouRequest,
    db: Session = Depends(get_db)
):
    from app.models.job import Job
    
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    comm_service = CommunicationService(db)
    success = comm_service.send_thank_you_email(
        job,
        request.interviewer_email,
        request.interviewer_name,
        request.interview_date
    )
    
    if success:
        return {"message": "Thank you email sent successfully"}
    else:
        raise HTTPException(status_code=500, detail="Failed to send thank you email")

@router.post("/mark-received")
def mark_communication_received(
    job_id: int,
    sender_email: str,
    subject: str,
    content: str,
    db: Session = Depends(get_db)
):
    comm_service = CommunicationService(db)
    communication = comm_service.mark_communication_received(
        job_id, sender_email, subject, content
    )
    
    return {"message": "Communication recorded", "communication_id": communication.id}

@router.get("/job/{job_id}/history", response_model=List[CommunicationResponse])
def get_job_communication_history(job_id: int, db: Session = Depends(get_db)):
    comm_service = CommunicationService(db)
    return comm_service.get_communication_history(job_id)

@router.post("/process-scheduled")
def process_scheduled_communications(db: Session = Depends(get_db)):
    comm_service = CommunicationService(db)
    results = comm_service.process_scheduled_communications()
    return results