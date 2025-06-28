from typing import List
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from app.services.email_parser_service import EmailJobParserService
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

class EmailParseRequest(BaseModel):
    days_back: int = 7
    imap_server: str = "imap.gmail.com"  # Default for Gmail
    email_user: str
    email_password: str

class EmailParseResponse(BaseModel):
    success: bool
    jobs_found: int
    jobs: List[dict]
    message: str

@router.post("/parse-emails", response_model=EmailParseResponse)
async def parse_job_emails(request: EmailParseRequest):
    """Parse job opportunities from email inbox"""
    
    try:
        # Initialize email parser
        parser = EmailJobParserService()
        
        # Connect to email server
        connected = parser.connect_to_email(
            request.imap_server,
            request.email_user,
            request.email_password
        )
        
        if not connected:
            raise HTTPException(
                status_code=400,
                detail="Failed to connect to email server. Check credentials and server settings."
            )
        
        # Fetch and parse job emails
        jobs = parser.fetch_job_emails(days_back=request.days_back)
        
        # Close connection
        parser.close_connection()
        
        logger.info(f"Successfully parsed {len(jobs)} jobs from emails")
        
        return EmailParseResponse(
            success=True,
            jobs_found=len(jobs),
            jobs=jobs,
            message=f"Successfully found {len(jobs)} job opportunities from emails"
        )
        
    except Exception as e:
        logger.error(f"Email parsing failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Email parsing failed: {str(e)}"
        )

@router.get("/email-config-test")
async def test_email_configuration():
    """Test email configuration from environment variables"""
    
    # Try to get last processing status from Celery
    last_check = None
    try:
        from app.tasks import process_job_emails_task
        # In a real implementation, you'd check Redis for last task result
        # For now, we'll use a placeholder
        last_check = None
    except:
        pass
    
    config_status = {
        "imap_server_configured": bool(settings.IMAP_SERVER),
        "imap_user_configured": bool(settings.IMAP_USER),
        "imap_password_configured": bool(settings.IMAP_PASSWORD),
        "email_parsing_enabled": settings.EMAIL_PARSING_ENABLED,
        "imap_server": settings.IMAP_SERVER or "Not configured",
    }
    
    all_configured = all([
        settings.IMAP_SERVER,
        settings.IMAP_USER,
        settings.IMAP_PASSWORD,
        settings.EMAIL_PARSING_ENABLED
    ])
    
    return {
        "configured": all_configured,
        "status": "Automatic email processing active" if all_configured else "Configuration required",
        "last_check": last_check,
        "config": config_status,
        "processing_frequency": "Every 15 minutes" if all_configured else None,
        "next_steps": [
            "Set IMAP_SERVER in .env (e.g., imap.gmail.com)",
            "Set IMAP_USER in .env (your email address)",
            "Set IMAP_PASSWORD in .env (app password for Gmail)",
            "Set EMAIL_PARSING_ENABLED=true in .env"
        ] if not all_configured else ["Email processing is automatic - check dashboard for latest jobs"]
    }

@router.post("/parse-emails-from-config")
async def parse_emails_from_config(days_back: int = 7):
    """Parse emails using configuration from environment variables"""
    
    if not settings.EMAIL_PARSING_ENABLED:
        raise HTTPException(
            status_code=400,
            detail="Email parsing is not enabled. Set EMAIL_PARSING_ENABLED=true in .env"
        )
    
    if not all([settings.IMAP_SERVER, settings.IMAP_USER, settings.IMAP_PASSWORD]):
        raise HTTPException(
            status_code=400,
            detail="Email configuration incomplete. Check IMAP_SERVER, IMAP_USER, and IMAP_PASSWORD in .env"
        )
    
    try:
        # Initialize email parser
        parser = EmailJobParserService()
        
        # Connect using environment config
        connected = parser.connect_to_email(
            settings.IMAP_SERVER,
            settings.IMAP_USER,
            settings.IMAP_PASSWORD
        )
        
        if not connected:
            raise HTTPException(
                status_code=400,
                detail="Failed to connect to email server. Check credentials."
            )
        
        # Fetch and parse job emails
        jobs = parser.fetch_job_emails(days_back=days_back)
        
        # Close connection
        parser.close_connection()
        
        # TODO: Save jobs to database here
        # For now, just return the parsed jobs
        
        return EmailParseResponse(
            success=True,
            jobs_found=len(jobs),
            jobs=jobs,
            message=f"Successfully found {len(jobs)} job opportunities from emails"
        )
        
    except Exception as e:
        logger.error(f"Email parsing failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Email parsing failed: {str(e)}"
        )