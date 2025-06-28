import os
import json
import base64
import email
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import logging
from app.core.config import settings
from app.services.email_parser_service import EmailJobParserService

logger = logging.getLogger(__name__)

class OAuth2EmailService:
    """OAuth2-based email service for Google Workspace/Gmail"""
    
    def __init__(self):
        self.credentials = None
        self.service = None
        self.scopes = [
            'https://www.googleapis.com/auth/gmail.readonly',
            'https://www.googleapis.com/auth/gmail.modify'
        ]
        
    def setup_oauth_flow(self, credentials_file_path: str, redirect_uri: str = 'urn:ietf:wg:oauth:2.0:oob') -> str:
        """
        Set up OAuth2 flow and return authorization URL
        
        Args:
            credentials_file_path: Path to downloaded OAuth2 credentials JSON
            redirect_uri: Redirect URI for OAuth flow
            
        Returns:
            Authorization URL for user to visit
        """
        try:
            self.flow = Flow.from_client_secrets_file(
                credentials_file_path,
                scopes=self.scopes,
                redirect_uri=redirect_uri
            )
            
            authorization_url, _ = self.flow.authorization_url(
                access_type='offline',
                include_granted_scopes='true',
                prompt='consent'
            )
            
            logger.info(f"OAuth2 authorization URL generated")
            return authorization_url
            
        except Exception as e:
            logger.error(f"Failed to setup OAuth flow: {e}")
            raise
    
    def complete_oauth_flow(self, authorization_code: str) -> Dict[str, Any]:
        """
        Complete OAuth2 flow with authorization code
        
        Args:
            authorization_code: Code received from OAuth consent
            
        Returns:
            Credentials dictionary to store
        """
        try:
            if not hasattr(self, 'flow'):
                raise ValueError("OAuth flow not initialized. Call setup_oauth_flow first.")
            
            self.flow.fetch_token(code=authorization_code)
            self.credentials = self.flow.credentials
            
            # Convert credentials to storable format
            creds_data = {
                'token': self.credentials.token,
                'refresh_token': self.credentials.refresh_token,
                'token_uri': self.credentials.token_uri,
                'client_id': self.credentials.client_id,
                'client_secret': self.credentials.client_secret,
                'scopes': self.credentials.scopes,
                'expiry': self.credentials.expiry.isoformat() if self.credentials.expiry else None
            }
            
            logger.info("OAuth2 flow completed successfully")
            return creds_data
            
        except Exception as e:
            logger.error(f"Failed to complete OAuth flow: {e}")
            raise
    
    def load_credentials(self, creds_data: Dict[str, Any]) -> bool:
        """
        Load credentials from stored data
        
        Args:
            creds_data: Previously stored credentials dictionary
            
        Returns:
            True if credentials loaded successfully
        """
        try:
            # Convert expiry back to datetime if present
            expiry = None
            if creds_data.get('expiry'):
                expiry = datetime.fromisoformat(creds_data['expiry'])
            
            self.credentials = Credentials(
                token=creds_data['token'],
                refresh_token=creds_data['refresh_token'],
                token_uri=creds_data['token_uri'],
                client_id=creds_data['client_id'],
                client_secret=creds_data['client_secret'],
                scopes=creds_data['scopes'],
                expiry=expiry
            )
            
            # Refresh token if expired
            if self.credentials.expired and self.credentials.refresh_token:
                self.credentials.refresh(Request())
                logger.info("OAuth2 credentials refreshed")
            
            # Build Gmail service
            self.service = build('gmail', 'v1', credentials=self.credentials)
            logger.info("Gmail service initialized with OAuth2")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load credentials: {e}")
            return False
    
    def get_credentials_for_storage(self) -> Dict[str, Any]:
        """Get current credentials in storable format"""
        if not self.credentials:
            return {}
        
        return {
            'token': self.credentials.token,
            'refresh_token': self.credentials.refresh_token,
            'token_uri': self.credentials.token_uri,
            'client_id': self.credentials.client_id,
            'client_secret': self.credentials.client_secret,
            'scopes': self.credentials.scopes,
            'expiry': self.credentials.expiry.isoformat() if self.credentials.expiry else None
        }
    
    def fetch_job_emails(self, days_back: int = 7) -> List[Dict[str, Any]]:
        """
        Fetch job-related emails using Gmail API
        
        Args:
            days_back: Number of days to look back for emails
            
        Returns:
            List of parsed job data
        """
        if not self.service:
            raise ValueError("Gmail service not initialized. Load credentials first.")
        
        jobs = []
        
        try:
            # Calculate date range
            since_date = datetime.now() - timedelta(days=days_back)
            query_date = since_date.strftime('%Y/%m/%d')
            
            # Search for emails from job platforms
            job_platform_senders = [
                'linkedin.com',
                'indeed.com', 
                'builtin.com',
                'ziprecruiter.com',
                'jobs-noreply@linkedin.com',
                'noreply@indeed.com',
                'jobs@builtin.com'
            ]
            
            for sender in job_platform_senders:
                try:
                    # Build search query
                    query = f'from:{sender} after:{query_date}'
                    
                    # Search for messages
                    results = self.service.users().messages().list(
                        userId='me',
                        q=query,
                        maxResults=50
                    ).execute()
                    
                    messages = results.get('messages', [])
                    logger.info(f"Found {len(messages)} emails from {sender}")
                    
                    for message in messages:
                        try:
                            job_data = self._parse_gmail_message(message['id'])
                            if job_data:
                                jobs.append(job_data)
                        except Exception as e:
                            logger.error(f"Error parsing message {message['id']}: {e}")
                            continue
                            
                except Exception as e:
                    logger.error(f"Error searching emails from {sender}: {e}")
                    continue
            
            logger.info(f"Successfully parsed {len(jobs)} jobs from Gmail API")
            return jobs
            
        except HttpError as e:
            logger.error(f"Gmail API error: {e}")
            raise
        except Exception as e:
            logger.error(f"Error fetching job emails: {e}")
            raise
    
    def _parse_gmail_message(self, message_id: str) -> Optional[Dict[str, Any]]:
        """Parse individual Gmail message for job information"""
        try:
            # Get message details
            message = self.service.users().messages().get(
                userId='me',
                id=message_id,
                format='full'
            ).execute()
            
            # Extract headers
            headers = message['payload'].get('headers', [])
            subject = ''
            sender = ''
            date_received = None
            
            for header in headers:
                if header['name'] == 'Subject':
                    subject = header['value']
                elif header['name'] == 'From':
                    sender = header['value']
                elif header['name'] == 'Date':
                    date_received = header['value']
            
            # Check if this is a job-related email
            if not self._is_job_email_by_subject_sender(subject, sender):
                return None
            
            # Extract email content
            email_content = self._extract_gmail_content(message['payload'])
            if not email_content:
                return None
            
            # Parse job information using existing parser logic
            parser = EmailJobParserService()
            
            # Determine platform from sender
            platform = self._determine_platform_from_sender(sender)
            
            # Extract jobs from content
            jobs = parser._extract_jobs_from_content(email_content, platform)
            
            if jobs:
                job = jobs[0]  # Take first job
                job.update({
                    'email_subject': subject,
                    'email_date': date_received,
                    'source': 'gmail_oauth',
                    'discovered_at': datetime.now(),
                    'message_id': message_id
                })
                return job
                
        except Exception as e:
            logger.error(f"Error parsing Gmail message {message_id}: {e}")
            
        return None
    
    def _extract_gmail_content(self, payload: Dict[str, Any]) -> str:
        """Extract readable content from Gmail message payload"""
        content = ""
        
        try:
            if 'parts' in payload:
                for part in payload['parts']:
                    if part['mimeType'] == 'text/html' or part['mimeType'] == 'text/plain':
                        if 'data' in part['body']:
                            data = part['body']['data']
                            content += base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
            else:
                if payload['mimeType'] == 'text/html' or payload['mimeType'] == 'text/plain':
                    if 'data' in payload['body']:
                        data = payload['body']['data']
                        content = base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
        except Exception as e:
            logger.error(f"Error extracting Gmail content: {e}")
        
        return content
    
    def _is_job_email_by_subject_sender(self, subject: str, sender: str) -> bool:
        """Check if email is job-related based on subject and sender"""
        if not subject or not sender:
            return False
        
        subject_lower = subject.lower()
        sender_lower = sender.lower()
        
        # Check sender patterns
        job_senders = ['linkedin', 'indeed', 'builtin', 'ziprecruiter']
        sender_match = any(platform in sender_lower for platform in job_senders)
        
        # Check subject patterns
        job_subjects = [
            'job alert', 'new jobs', 'recommended for you', 'job recommendations',
            'job matches', 'new opportunities', 'career opportunities'
        ]
        subject_match = any(pattern in subject_lower for pattern in job_subjects)
        
        return sender_match and subject_match
    
    def _determine_platform_from_sender(self, sender: str):
        """Determine job platform from email sender"""
        from app.models.job import JobPlatform
        
        sender_lower = sender.lower()
        
        if 'linkedin' in sender_lower:
            return JobPlatform.LINKEDIN
        elif 'indeed' in sender_lower:
            return JobPlatform.INDEED
        elif 'builtin' in sender_lower:
            return JobPlatform.BUILTIN
        elif 'ziprecruiter' in sender_lower:
            return JobPlatform.ZIPRECRUITER
        else:
            return JobPlatform.LINKEDIN  # Default
    
    def test_connection(self) -> Dict[str, Any]:
        """Test Gmail API connection and permissions"""
        if not self.service:
            return {"success": False, "error": "Service not initialized"}
        
        try:
            # Test by getting user profile
            profile = self.service.users().getProfile(userId='me').execute()
            
            return {
                "success": True,
                "email": profile.get('emailAddress'),
                "messages_total": profile.get('messagesTotal', 0),
                "threads_total": profile.get('threadsTotal', 0)
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}