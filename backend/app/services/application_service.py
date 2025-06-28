from sqlalchemy.orm import Session
from sqlalchemy import and_, desc
from typing import List, Optional, Dict, Any
from app.models.application import Application, ApplicationStatus, ApplicationMethod
from app.models.job import Job
from app.automation.application_automator import ApplicationAutomator
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class ApplicationService:
    def __init__(self, db: Session):
        self.db = db

    def get_applications(
        self,
        skip: int = 0,
        limit: int = 100,
        status: Optional[ApplicationStatus] = None,
        job_id: Optional[int] = None
    ) -> List[Application]:
        query = self.db.query(Application)
        
        if status:
            query = query.filter(Application.status == status)
        if job_id:
            query = query.filter(Application.job_id == job_id)
            
        return query.order_by(desc(Application.created_at)).offset(skip).limit(limit).all()

    def get_application(self, application_id: int) -> Optional[Application]:
        return self.db.query(Application).filter(Application.id == application_id).first()

    def create_application(self, application_data: Dict[str, Any]) -> Application:
        application = Application(**application_data)
        self.db.add(application)
        self.db.commit()
        self.db.refresh(application)
        return application

    def update_application(self, application_id: int, application_data: Dict[str, Any]) -> Optional[Application]:
        application = self.get_application(application_id)
        if not application:
            return None
            
        for key, value in application_data.items():
            if hasattr(application, key):
                setattr(application, key, value)
                
        application.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(application)
        return application

    def delete_application(self, application_id: int) -> bool:
        application = self.get_application(application_id)
        if not application:
            return False
            
        self.db.delete(application)
        self.db.commit()
        return True

    def submit_application(
        self,
        job_id: int,
        application_data: Dict[str, Any],
        auto_apply: bool = False
    ) -> Dict[str, Any]:
        """Submit an application to a job"""
        
        # Get the job
        job = self.db.query(Job).filter(Job.id == job_id).first()
        if not job:
            raise ValueError("Job not found")

        # Check if application already exists
        existing_app = self.db.query(Application).filter(Application.job_id == job_id).first()
        if existing_app:
            raise ValueError("Application already exists for this job")

        try:
            # Create application record
            application = Application(
                job_id=job_id,
                status=ApplicationStatus.PENDING,
                method=ApplicationMethod.AUTOMATED if auto_apply else ApplicationMethod.MANUAL,
                resume_path=application_data.get("resume_path"),
                cover_letter_path=application_data.get("cover_letter_path"),
                portfolio_url=application_data.get("portfolio_url"),
                salary_expectation=application_data.get("salary_expectation"),
                availability_date=application_data.get("availability_date"),
                work_authorization=application_data.get("work_authorization"),
                custom_responses=application_data.get("custom_responses")
            )
            
            self.db.add(application)
            self.db.flush()  # Get the ID without committing

            if auto_apply:
                # Attempt automated application
                automator = ApplicationAutomator()
                result = automator.apply_to_job(job, application_data)

                if result["success"]:
                    application.status = ApplicationStatus.SUBMITTED
                    application.submitted_at = datetime.utcnow()
                    job.status = "applied"
                    job.applied_at = datetime.utcnow()
                else:
                    application.status = ApplicationStatus.FAILED
                    application.error_message = result.get("error_message")
                    
                    if result.get("requires_manual_action"):
                        application.method = ApplicationMethod.SEMI_AUTOMATED

            self.db.commit()
            self.db.refresh(application)

            return {
                "application_id": application.id,
                "status": application.status,
                "method": application.method,
                "success": application.status == ApplicationStatus.SUBMITTED,
                "error_message": application.error_message
            }

        except Exception as e:
            self.db.rollback()
            logger.error(f"Application submission failed: {e}")
            raise

    def retry_application(self, application_id: int) -> Optional[Dict[str, Any]]:
        """Retry a failed application"""
        
        application = self.get_application(application_id)
        if not application or application.status != ApplicationStatus.FAILED:
            return None

        job = self.db.query(Job).filter(Job.id == application.job_id).first()
        if not job:
            return None

        try:
            # Prepare application data
            application_data = {
                "resume_path": application.resume_path,
                "cover_letter_path": application.cover_letter_path,
                "portfolio_url": application.portfolio_url,
                "salary_expectation": application.salary_expectation,
                "availability_date": application.availability_date,
                "work_authorization": application.work_authorization
            }

            # Attempt resubmission
            automator = ApplicationAutomator()
            result = automator.apply_to_job(job, application_data)

            # Update application
            if result["success"]:
                application.status = ApplicationStatus.SUBMITTED
                application.submitted_at = datetime.utcnow()
                application.error_message = None
                job.status = "applied"
                job.applied_at = datetime.utcnow()
            else:
                application.retry_count = (application.retry_count or 0) + 1
                application.error_message = result.get("error_message")

            self.db.commit()
            self.db.refresh(application)

            return {
                "application_id": application.id,
                "status": application.status,
                "success": application.status == ApplicationStatus.SUBMITTED,
                "retry_count": application.retry_count,
                "error_message": application.error_message
            }

        except Exception as e:
            logger.error(f"Application retry failed: {e}")
            return None

    def get_application_statistics(self) -> Dict[str, Any]:
        """Get application statistics"""
        
        total_applications = self.db.query(Application).count()
        
        # Status breakdown
        status_stats = {}
        for status in ApplicationStatus:
            count = self.db.query(Application).filter(Application.status == status).count()
            status_stats[status.value] = count

        # Method breakdown
        method_stats = {}
        for method in ApplicationMethod:
            count = self.db.query(Application).filter(Application.method == method).count()
            method_stats[method.value] = count

        # Success rate
        submitted_count = status_stats.get("submitted", 0)
        success_rate = (submitted_count / total_applications * 100) if total_applications > 0 else 0

        # Recent activity (last 7 days)
        from datetime import timedelta
        week_ago = datetime.utcnow() - timedelta(days=7)
        recent_applications = self.db.query(Application).filter(
            Application.created_at >= week_ago
        ).count()

        return {
            "total_applications": total_applications,
            "status_breakdown": status_stats,
            "method_breakdown": method_stats,
            "success_rate": round(success_rate, 1),
            "recent_applications": recent_applications,
            "average_applications_per_day": round(recent_applications / 7, 1)
        }

    def get_applications_needing_followup(self) -> List[Application]:
        """Get applications that need follow-up (submitted > 7 days ago)"""
        
        from datetime import timedelta
        week_ago = datetime.utcnow() - timedelta(days=7)
        
        return self.db.query(Application).filter(
            Application.status == ApplicationStatus.SUBMITTED,
            Application.submitted_at <= week_ago
        ).all()

    def bulk_update_status(self, application_ids: List[int], new_status: ApplicationStatus) -> int:
        """Bulk update application status"""
        
        updated_count = self.db.query(Application).filter(
            Application.id.in_(application_ids)
        ).update(
            {Application.status: new_status, Application.updated_at: datetime.utcnow()},
            synchronize_session=False
        )
        
        self.db.commit()
        return updated_count