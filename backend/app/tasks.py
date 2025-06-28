from celery import Celery
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.core.celery import celery_app
from app.services.scraper_service import ScraperService
from app.services.communication_service import CommunicationService
from app.services.job_matching_service import JobMatchingService
from app.services.email_parser_service import EmailJobParserService
from app.services.oauth_email_service import OAuth2EmailService
from app.automation.application_automator import ApplicationAutomator
from app.core.config import settings
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
def process_job_emails_task(self):
    """Background task to process job emails automatically using OAuth2 or IMAP"""
    
    import os
    import json
    
    # Try OAuth2 first, fallback to IMAP
    oauth_creds_path = "/app/oauth_credentials.json"
    
    if os.path.exists(oauth_creds_path):
        return process_emails_with_oauth(oauth_creds_path)
    elif all([settings.IMAP_SERVER, settings.IMAP_USER, settings.IMAP_PASSWORD]) and settings.EMAIL_PARSING_ENABLED:
        return process_emails_with_imap()
    else:
        logger.info("No email configuration found (OAuth2 or IMAP)")
        return {"status": "not_configured", "message": "No email authentication configured"}

def process_emails_with_oauth(oauth_creds_path: str):
    """Process emails using OAuth2 authentication"""
    try:
        with open(oauth_creds_path, 'r') as f:
            creds_data = json.load(f)
        
        oauth_service = OAuth2EmailService()
        oauth_service.load_credentials(creds_data)
        
        # Test connection
        test_result = oauth_service.test_connection()
        if not test_result["success"]:
            logger.error(f"OAuth2 connection failed: {test_result.get('error')}")
            return {"status": "error", "message": f"OAuth2 connection failed: {test_result.get('error')}"}
        
        # Fetch and parse job emails (last 24 hours)
        jobs = oauth_service.fetch_job_emails(days_back=1)
        
        if not jobs:
            logger.info("No new job emails found via OAuth2")
            return {"status": "success", "jobs_found": 0, "jobs_saved": 0, "method": "oauth2"}
        
        jobs_saved = save_jobs_to_mock_store(jobs, "oauth2")
        
        result = {
            "status": "success",
            "jobs_found": len(jobs),
            "jobs_saved": jobs_saved,
            "duplicates_skipped": len(jobs) - jobs_saved,
            "processed_at": datetime.now().isoformat(),
            "method": "oauth2",
            "email": test_result.get("email")
        }
        
        logger.info(f"OAuth2 email processing completed: {result}")
        return result
        
    except Exception as e:
        logger.error(f"OAuth2 email processing failed: {e}")
        return {"status": "error", "message": str(e), "method": "oauth2"}

def process_emails_with_imap():
    """Process emails using IMAP authentication (legacy)"""
    try:
        parser = EmailJobParserService()
        
        # Connect to email server
        connected = parser.connect_to_email(
            settings.IMAP_SERVER,
            settings.IMAP_USER, 
            settings.IMAP_PASSWORD
        )
        
        if not connected:
            logger.error("Failed to connect to email server via IMAP")
            return {"status": "error", "message": "Failed to connect to email server via IMAP"}
        
        # Fetch and parse job emails (last 24 hours)
        jobs = parser.fetch_job_emails(days_back=1)
        parser.close_connection()
        
        if not jobs:
            logger.info("No new job emails found via IMAP")
            return {"status": "success", "jobs_found": 0, "jobs_saved": 0, "method": "imap"}
        
        jobs_saved = save_jobs_to_mock_store(jobs, "imap")
        
        result = {
            "status": "success",
            "jobs_found": len(jobs),
            "jobs_saved": jobs_saved,
            "duplicates_skipped": len(jobs) - jobs_saved,
            "processed_at": datetime.now().isoformat(),
            "method": "imap"
        }
        
        logger.info(f"IMAP email processing completed: {result}")
        return result
        
    except Exception as e:
        logger.error(f"IMAP email processing failed: {e}")
        return {"status": "error", "message": str(e), "method": "imap"}

def save_jobs_to_mock_store(jobs, source_method):
    """Save parsed jobs to mock data store"""
    from app.main import mock_data_store
    jobs_saved = 0
    
    for job_data in jobs:
        try:
            # Generate new ID
            new_id = max(mock_data_store["jobs"].keys(), default=0) + 1
            
            # Convert to mock data format
            mock_job = {
                "id": new_id,
                "title": job_data.get("title", "Unknown Position"),
                "company": job_data.get("company", "Unknown Company"),
                "location": job_data.get("location", "Location not specified"),
                "salary_min": job_data.get("salary_min"),
                "salary_max": job_data.get("salary_max"),
                "platform": job_data.get("platform", "email").value if hasattr(job_data.get("platform"), 'value') else str(job_data.get("platform", "email")).lower(),
                "status": "discovered",
                "priority": job_data.get("priority", "good_fit").value if hasattr(job_data.get("priority"), 'value') else str(job_data.get("priority", "good_fit")).lower(),
                "fit_score": job_data.get("fit_score", 7.0),
                "posted_date": job_data.get("posted_date", datetime.now()).isoformat() if hasattr(job_data.get("posted_date"), 'isoformat') else str(job_data.get("posted_date", datetime.now())),
                "discovered_at": datetime.now().isoformat(),
                "is_remote": job_data.get("is_remote", False),
                "application_url": job_data.get("application_url", ""),
                "source": source_method
            }
            
            # Check for duplicates by title and company
            duplicate = False
            for existing_job in mock_data_store["jobs"].values():
                if (existing_job["title"].lower() == mock_job["title"].lower() and 
                    existing_job["company"].lower() == mock_job["company"].lower()):
                    duplicate = True
                    break
            
            if not duplicate:
                mock_data_store["jobs"][new_id] = mock_job
                jobs_saved += 1
                logger.info(f"Saved job from {source_method}: {mock_job['title']} at {mock_job['company']}")
            else:
                logger.info(f"Skipped duplicate job: {mock_job['title']} at {mock_job['company']}")
                
        except Exception as e:
            logger.error(f"Failed to process job email: {e}")
            continue
    
    return jobs_saved

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