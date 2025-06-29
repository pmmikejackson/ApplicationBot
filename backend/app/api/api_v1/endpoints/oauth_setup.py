from typing import Dict, Any
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
from app.services.oauth_local_server import OAuth2LocalServerService
from app.core.config import settings
import os
import json
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

# In-memory storage for OAuth flow (in production, use Redis or database)
oauth_flows = {}

class OAuthStartRequest(BaseModel):
    port: int = 8080

class OAuthCompleteRequest(BaseModel):
    authorization_code: str
    flow_id: str

class OAuthStatusResponse(BaseModel):
    configured: bool
    status: str
    email: str = None
    last_check: str = None
    next_steps: list = []

@router.post("/start-oauth-flow")
async def start_oauth_flow(
    credentials_file: UploadFile = File(...),
    port: int = Form(8080)
):
    """
    Start OAuth2 flow by uploading Google credentials file
    """
    try:
        # Validate file type
        if not credentials_file.filename.endswith('.json'):
            raise HTTPException(
                status_code=400,
                detail="Credentials file must be a JSON file"
            )
        
        # Read and validate credentials file
        content = await credentials_file.read()
        try:
            creds_data = json.loads(content)
            if 'installed' not in creds_data and 'web' not in creds_data:
                raise ValueError("Invalid credentials file format")
        except json.JSONDecodeError:
            raise HTTPException(
                status_code=400,
                detail="Invalid JSON file"
            )
        
        # Save credentials file temporarily
        temp_creds_path = "/tmp/oauth_credentials.json"
        with open(temp_creds_path, 'w') as f:
            f.write(content.decode('utf-8'))
        
        # Initialize OAuth service with local server
        oauth_service = OAuth2LocalServerService()
        
        # Start OAuth flow with local server
        auth_url = oauth_service.setup_oauth_flow_with_server(temp_creds_path, port)
        
        # Store flow for completion (use UUID in production)
        flow_id = "main_flow"
        oauth_flows[flow_id] = oauth_service
        
        # Clean up temp file
        os.remove(temp_creds_path)
        
        return {
            "success": True,
            "authorization_url": auth_url,
            "flow_id": flow_id,
            "port": port,
            "instructions": [
                "1. Click the authorization URL",
                "2. Sign in with mike@mikejacksonpm.com", 
                "3. Grant permissions for Gmail access",
                "4. Authorization will complete automatically",
                "5. Return to this page to see completion status"
            ]
        }
        
    except Exception as e:
        logger.error(f"Failed to start OAuth flow: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to start OAuth flow: {str(e)}"
        )

@router.post("/complete-oauth-flow")
async def complete_oauth_flow(request: OAuthCompleteRequest):
    """
    Complete OAuth2 flow with authorization code
    """
    try:
        # Get stored flow
        if request.flow_id not in oauth_flows:
            raise HTTPException(
                status_code=400,
                detail="OAuth flow not found or expired"
            )
        
        oauth_service = oauth_flows[request.flow_id]
        
        # Complete OAuth flow with authorization code
        creds_data = oauth_service.complete_oauth_flow_with_code(request.authorization_code)
        
        # Store credentials securely (in production, encrypt and store in database)
        creds_file_path = "/app/oauth_credentials.json"
        os.makedirs(os.path.dirname(creds_file_path), exist_ok=True)
        
        with open(creds_file_path, 'w') as f:
            json.dump(creds_data, f, indent=2)
        
        # Test the connection
        oauth_service.load_credentials(creds_data)
        test_result = oauth_service.test_connection()
        
        # Clean up flow
        del oauth_flows[request.flow_id]
        
        return {
            "success": True,
            "message": "OAuth2 setup completed successfully",
            "email": test_result.get("email"),
            "connection_test": test_result,
            "next_steps": [
                "OAuth2 authentication is now configured",
                "Email processing will start automatically",
                "Set up job alerts on LinkedIn, Indeed, etc.",
                "Check dashboard for automatic job discovery"
            ]
        }
        
    except Exception as e:
        logger.error(f"Failed to complete OAuth flow: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to complete OAuth flow: {str(e)}"
        )

@router.get("/oauth-status", response_model=OAuthStatusResponse)
async def get_oauth_status():
    """
    Get current OAuth2 configuration status
    """
    try:
        creds_file_path = "/app/oauth_credentials.json"
        
        if not os.path.exists(creds_file_path):
            return OAuthStatusResponse(
                configured=False,
                status="OAuth2 credentials not configured",
                next_steps=[
                    "1. Download OAuth2 credentials from Google Cloud Console",
                    "2. Upload credentials file to start OAuth flow",
                    "3. Complete authorization process",
                    "4. Grant Gmail access permissions"
                ]
            )
        
        # Load and test credentials
        with open(creds_file_path, 'r') as f:
            creds_data = json.load(f)
        
        oauth_service = OAuth2LocalServerService()
        oauth_service.load_credentials(creds_data)
        test_result = oauth_service.test_connection()
        
        if test_result["success"]:
            return OAuthStatusResponse(
                configured=True,
                status="OAuth2 authentication active",
                email=test_result.get("email"),
                last_check=None,  # TODO: Get from Celery task results
                next_steps=[
                    "OAuth2 is configured and working",
                    "Email processing runs automatically every 15 minutes",
                    "Set up job alerts on platforms to receive emails"
                ]
            )
        else:
            return OAuthStatusResponse(
                configured=False,
                status=f"OAuth2 connection failed: {test_result.get('error')}",
                next_steps=[
                    "OAuth2 credentials may be expired",
                    "Re-run OAuth setup to refresh credentials"
                ]
            )
        
    except Exception as e:
        logger.error(f"Error checking OAuth status: {e}")
        return OAuthStatusResponse(
            configured=False,
            status=f"Error checking OAuth status: {str(e)}",
            next_steps=[
                "Check server logs for detailed error information",
                "Re-run OAuth setup if credentials are corrupted"
            ]
        )

@router.get("/check-authorization-status/{flow_id}")
async def check_authorization_status(flow_id: str):
    """
    Check if user has completed OAuth2 authorization
    """
    try:
        if flow_id not in oauth_flows:
            raise HTTPException(
                status_code=400,
                detail="OAuth flow not found or expired"
            )
        
        oauth_service = oauth_flows[flow_id]
        status = oauth_service.check_authorization_status()
        
        if status['status'] == 'completed':
            # Store credentials and clean up
            creds_data = status['credentials']
            creds_file_path = "/app/oauth_credentials.json"
            os.makedirs(os.path.dirname(creds_file_path), exist_ok=True)
            
            with open(creds_file_path, 'w') as f:
                json.dump(creds_data, f, indent=2)
            
            # Test the connection
            test_result = oauth_service.test_connection()
            
            # Clean up flow
            del oauth_flows[flow_id]
            
            return {
                "status": "completed",
                "success": True,
                "message": "OAuth2 setup completed successfully",
                "email": test_result.get("email"),
                "connection_test": test_result
            }
        
        return status
        
    except Exception as e:
        logger.error(f"Error checking authorization status: {e}")
        return {
            "status": "error",
            "message": f"Error checking authorization status: {str(e)}"
        }

@router.post("/test-oauth-connection")
async def test_oauth_connection():
    """
    Test current OAuth2 connection
    """
    try:
        creds_file_path = "/app/oauth_credentials.json"
        
        if not os.path.exists(creds_file_path):
            raise HTTPException(
                status_code=400,
                detail="OAuth2 not configured. Run setup first."
            )
        
        with open(creds_file_path, 'r') as f:
            creds_data = json.load(f)
        
        oauth_service = OAuth2LocalServerService()
        oauth_service.load_credentials(creds_data)
        
        # Test connection and fetch recent emails
        test_result = oauth_service.test_connection()
        
        if test_result["success"]:
            # Try to fetch a few recent emails as additional test
            try:
                recent_jobs = oauth_service.fetch_job_emails(days_back=3)
                return {
                    "success": True,
                    "connection_test": test_result,
                    "recent_emails_found": len(recent_jobs),
                    "sample_jobs": recent_jobs[:3] if recent_jobs else []
                }
            except Exception as e:
                return {
                    "success": True,
                    "connection_test": test_result,
                    "email_fetch_error": str(e),
                    "note": "Connection works but email fetching failed"
                }
        else:
            raise HTTPException(
                status_code=400,
                detail=f"OAuth2 connection test failed: {test_result.get('error')}"
            )
        
    except Exception as e:
        logger.error(f"OAuth connection test failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"OAuth connection test failed: {str(e)}"
        )