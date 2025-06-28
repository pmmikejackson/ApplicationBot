from celery import Celery
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.core.celery import celery_app
from app.services.scraper_service import ScraperService
from app.services.communication_service import CommunicationService
from app.services.job_matching_service import JobMatchingService
from app.automation.application_automator import ApplicationAutomator
from app.models.job import Job, JobStatus, JobPriority
from app.models.application import Application, ApplicationStatus
from app.models.user import User
from app.models.communication import Communication
from typing import List, Dict, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

def get_db() -> Session:
    db = SessionLocal()
    try:
        return db
    finally:
        pass  # Don't close here, will be closed by task

@celery_app.task(bind=True)
def scrape_jobs_task(self, user_id: int = None):
    """Periodic task to scrape jobs from all platforms"""
    
    db = get_db()
    try:
        scraper_service = ScraperService(db)
        
        # Default search parameters - could be customized per user
        keywords = [
            "Director of Product Management",
            "Senior Product Manager", 
            "VP Product",
            "Head of Product"
        ]
        location = "Remote"
        
        # Run scraping
        results = scraper_service.scrape_all_platforms(
            keywords=keywords,
            location=location,
            remote_only=True,
            senior_level=True
        )
        
        logger.info(f"Scraping completed: {results['total_jobs_found']} found, {results['total_jobs_saved']} saved")
        
        # If specific user, update their job scores
        if user_id:
            update_job_scores_task.delay(user_id)
            
        return results
        
    except Exception as e:
        logger.error(f"Scraping task failed: {e}")
        raise self.retry(exc=e, countdown=300, max_retries=3)
    finally:
        db.close()

@celery_app.task(bind=True)
def update_job_scores_task(self, user_id: int):
    """Update job fit scores for a specific user"""
    
    db = get_db()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            logger.error(f"User {user_id} not found")
            return
            
        # Build user profile from database
        user_profile = {
            "target_titles": user.target_titles or [],
            "skills": user.skills or [],
            "years_experience": user.years_experience or 5,
            "salary_expectations": {
                "min": user.salary_min,
                "max": user.salary_max
            },
            "location_preferences": user.location_preferences or {},
            "remote_preference": user.remote_preference
        }
        
        matching_service = JobMatchingService(db)
        results = matching_service.update_all_job_scores(user_profile)
        
        logger.info(f"Updated job scores for user {user_id}: {results}")
        return results
        
    except Exception as e:
        logger.error(f"Job scoring task failed: {e}")
        raise self.retry(exc=e, countdown=60, max_retries=2)
    finally:
        db.close()

@celery_app.task(bind=True)
def auto_apply_jobs_task(self, user_id: int):
    """Automatically apply to high-priority jobs for a user"""
    
    db = get_db()
    try:
        user = db.query(User).filter(
            User.id == user_id,
            User.auto_apply_enabled == True
        ).first()
        
        if not user:
            logger.info(f"Auto-apply not enabled for user {user_id}")
            return
            
        # Get high-priority jobs that haven't been applied to
        high_priority_jobs = db.query(Job).filter(
            Job.priority == JobPriority.MUST_APPLY,
            Job.status == JobStatus.DISCOVERED,
            ~Job.applications.any()  # No existing applications
        ).limit(5).all()  # Limit to 5 per run to avoid overwhelming
        
        if not high_priority_jobs:
            logger.info(f"No high-priority jobs to apply to for user {user_id}")
            return
            
        automator = ApplicationAutomator()
        application_data = {
            "first_name": user.first_name,
            "last_name": user.last_name,
            "email": user.email,
            "phone": user.phone,
            "linkedin_url": user.linkedin_url,
            "portfolio_url": user.portfolio_url,
            "resume_template_path": user.resume_template_path,
            "cover_letter_template": user.cover_letter_template,
            "work_authorization": "Yes, I am authorized to work in the US",
            "salary_expectation": f"${user.salary_min}-${user.salary_max}" if user.salary_min else "Negotiable"
        }
        
        results = {"applied": 0, "failed": 0}
        
        for job in high_priority_jobs:
            try:
                # Apply to job
                result = automator.apply_to_job(job, application_data)
                
                # Create application record
                application = Application(
                    job_id=job.id,
                    status=ApplicationStatus.SUBMITTED if result["success"] else ApplicationStatus.FAILED,
                    method=result["method"],
                    error_message=result.get("error_message"),
                    submitted_at=datetime.utcnow() if result["success"] else None
                )
                
                db.add(application)
                
                # Update job status
                if result["success"]:
                    job.status = JobStatus.APPLIED
                    job.applied_at = datetime.utcnow()
                    results["applied"] += 1
                    
                    # Schedule follow-up email
                    schedule_follow_up_task.delay(job.id, user_id, 7)
                else:
                    results["failed"] += 1
                    
                db.commit()
                
            except Exception as e:
                logger.error(f"Failed to apply to job {job.id}: {e}")
                results["failed"] += 1
                
        logger.info(f"Auto-apply completed for user {user_id}: {results}")
        return results
        
    except Exception as e:
        logger.error(f"Auto-apply task failed: {e}")
        raise self.retry(exc=e, countdown=300, max_retries=2)
    finally:
        db.close()

@celery_app.task(bind=True)
def process_scheduled_communications_task(self):
    """Process all scheduled communications that are due"""
    
    db = get_db()
    try:
        comm_service = CommunicationService(db)
        results = comm_service.process_scheduled_communications()
        
        logger.info(f"Processed scheduled communications: {results}")
        return results
        
    except Exception as e:
        logger.error(f"Communication processing task failed: {e}")
        raise self.retry(exc=e, countdown=60, max_retries=3)
    finally:
        db.close()

@celery_app.task(bind=True)
def schedule_follow_up_task(self, job_id: int, user_id: int, days_delay: int = 7):
    """Schedule a follow-up email for a job application"""
    
    db = get_db()
    try:
        job = db.query(Job).filter(Job.id == job_id).first()
        application = db.query(Application).filter(
            Application.job_id == job_id
        ).first()
        
        if not job or not application:
            logger.error(f"Job {job_id} or application not found")
            return
            
        comm_service = CommunicationService(db)
        communication = comm_service.schedule_follow_up(
            job, application, days_delay
        )
        
        logger.info(f"Scheduled follow-up for job {job_id} in {days_delay} days")
        return {"communication_id": communication.id}
        
    except Exception as e:
        logger.error(f"Follow-up scheduling failed: {e}")
        raise self.retry(exc=e, countdown=60, max_retries=2)
    finally:
        db.close()

@celery_app.task(bind=True)
def send_email_task(self, to_email: str, subject: str, content: str, job_id: int = None):
    """Send email task"""
    
    db = get_db()
    try:
        comm_service = CommunicationService(db)
        success = comm_service._send_email(to_email, subject, content)
        
        if success:
            logger.info(f"Email sent successfully to {to_email}")
        else:
            logger.error(f"Failed to send email to {to_email}")
            
        return {"success": success}
        
    except Exception as e:
        logger.error(f"Email sending task failed: {e}")
        raise self.retry(exc=e, countdown=60, max_retries=3)
    finally:
        db.close()

@celery_app.task(bind=True)
def analyze_job_with_ai_task(self, job_id: int, user_id: int):
    """Analyze job with AI in background"""
    
    db = get_db()
    try:
        job = db.query(Job).filter(Job.id == job_id).first()
        user = db.query(User).filter(User.id == user_id).first()
        
        if not job or not user:
            logger.error(f"Job {job_id} or user {user_id} not found")
            return
            
        # Build user profile
        user_profile = {
            "target_titles": user.target_titles or [],
            "skills": user.skills or [],
            "years_experience": user.years_experience or 5,
            "salary_expectations": {
                "min": user.salary_min,
                "max": user.salary_max
            }
        }
        
        matching_service = JobMatchingService(db)
        analysis = matching_service.analyze_job_with_ai(job, user_profile)
        
        logger.info(f"AI analysis completed for job {job_id}")
        return analysis
        
    except Exception as e:
        logger.error(f"AI analysis task failed: {e}")
        raise self.retry(exc=e, countdown=120, max_retries=2)
    finally:
        db.close()

@celery_app.task(bind=True)
def cleanup_old_data_task(self):
    """Clean up old data (failed applications, old communications, etc.)"""
    
    db = get_db()
    try:
        from datetime import datetime, timedelta
        
        # Remove old failed applications (older than 30 days)
        cutoff_date = datetime.utcnow() - timedelta(days=30)
        
        old_failed_apps = db.query(Application).filter(
            Application.status == ApplicationStatus.FAILED,
            Application.created_at < cutoff_date
        ).count()
        
        db.query(Application).filter(
            Application.status == ApplicationStatus.FAILED,
            Application.created_at < cutoff_date
        ).delete()
        
        # Remove old communications (older than 90 days)
        comm_cutoff = datetime.utcnow() - timedelta(days=90)
        old_comms = db.query(Communication).filter(
            Communication.created_at < comm_cutoff
        ).count()
        
        db.query(Communication).filter(
            Communication.created_at < comm_cutoff
        ).delete()
        
        db.commit()
        
        logger.info(f"Cleanup completed: {old_failed_apps} failed applications, {old_comms} old communications removed")
        return {"failed_applications_removed": old_failed_apps, "communications_removed": old_comms}
        
    except Exception as e:
        logger.error(f"Cleanup task failed: {e}")
        raise self.retry(exc=e, countdown=300, max_retries=2)
    finally:
        db.close()