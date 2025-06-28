from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc
from typing import List, Optional, Dict, Any
from app.models.job import Job, JobStatus, JobPlatform, JobPriority
from app.models.application import Application
from datetime import datetime

class JobService:
    def __init__(self, db: Session):
        self.db = db

    def get_jobs(
        self,
        skip: int = 0,
        limit: int = 100,
        status: Optional[JobStatus] = None,
        platform: Optional[JobPlatform] = None,
        priority: Optional[JobPriority] = None,
        min_fit_score: Optional[float] = None
    ) -> List[Job]:
        query = self.db.query(Job)
        
        if status:
            query = query.filter(Job.status == status)
        if platform:
            query = query.filter(Job.platform == platform)
        if priority:
            query = query.filter(Job.priority == priority)
        if min_fit_score is not None:
            query = query.filter(Job.fit_score >= min_fit_score)
            
        return query.order_by(desc(Job.fit_score), desc(Job.discovered_at)).offset(skip).limit(limit).all()

    def get_job(self, job_id: int) -> Optional[Job]:
        return self.db.query(Job).filter(Job.id == job_id).first()

    def create_job(self, job_data: Dict[str, Any]) -> Job:
        job = Job(**job_data)
        self.db.add(job)
        self.db.commit()
        self.db.refresh(job)
        return job

    def update_job(self, job_id: int, job_data: Dict[str, Any]) -> Optional[Job]:
        job = self.get_job(job_id)
        if not job:
            return None
            
        for key, value in job_data.items():
            if hasattr(job, key):
                setattr(job, key, value)
                
        job.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(job)
        return job

    def delete_job(self, job_id: int) -> bool:
        job = self.get_job(job_id)
        if not job:
            return False
            
        self.db.delete(job)
        self.db.commit()
        return True

    def get_job_statistics(self) -> Dict[str, Any]:
        total_jobs = self.db.query(Job).count()
        applied_jobs = self.db.query(Job).filter(Job.status == "applied").count()
        high_priority_jobs = self.db.query(Job).filter(Job.priority == "must_apply").count()
        
        # Platform breakdown
        platform_stats = {}
        for platform in JobPlatform:
            count = self.db.query(Job).filter(Job.platform == platform).count()
            platform_stats[platform.value] = count
            
        # Status breakdown
        status_stats = {}
        for status in JobStatus:
            count = self.db.query(Job).filter(Job.status == status).count()
            status_stats[status.value] = count
            
        return {
            "total_jobs": total_jobs,
            "applied_jobs": applied_jobs,
            "high_priority_jobs": high_priority_jobs,
            "platform_breakdown": platform_stats,
            "status_breakdown": status_stats,
            "average_fit_score": self.db.query(Job).with_entities(Job.fit_score).filter(Job.fit_score > 0).scalar() or 0
        }

    def find_duplicate_jobs(self, title: str, company: str, platform_id: str) -> Optional[Job]:
        return self.db.query(Job).filter(
            and_(
                Job.title.ilike(f"%{title}%"),
                Job.company.ilike(f"%{company}%")
            )
        ).first() or self.db.query(Job).filter(Job.platform_id == platform_id).first()