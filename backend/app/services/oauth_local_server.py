import os
import json
import base64
import email
import threading
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler
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

class OAuth2LocalServerService:
    """OAuth2 service using local server for redirect handling"""
    
    def __init__(self):
        self.credentials = None
        self.service = None
        self.authorization_code = None
        self.flow = None
        self.server = None
        self.server_thread = None
        self.scopes = [
            'https://www.googleapis.com/auth/gmail.readonly',
            'https://www.googleapis.com/auth/gmail.modify'
        ]

    def setup_oauth_flow_with_server(self, credentials_file_path: str, port: int = 8080) -> str:
        """
        Set up OAuth2 flow with local server for redirect handling
        
        Args:
            credentials_file_path: Path to downloaded OAuth2 credentials JSON
            port: Port for local callback server
            
        Returns:
            Authorization URL for user to visit
        """
        try:
            redirect_uri = f'http://localhost:{port}'
            
            # Create OAuth flow
            self.flow = Flow.from_client_secrets_file(
                credentials_file_path,
                scopes=self.scopes,
                redirect_uri=redirect_uri
            )
            
            # Start local server to handle callback
            self._start_callback_server(port)
            
            # Generate authorization URL
            authorization_url, _ = self.flow.authorization_url(
                access_type='offline',
                include_granted_scopes='true',
                prompt='consent'
            )
            
            logger.info(f"OAuth2 authorization URL generated with local server on port {port}")
            return authorization_url
            
        except Exception as e:
            logger.error(f"Failed to setup OAuth flow with server: {e}")
            raise

    def _start_callback_server(self, port: int):
        """Start local HTTP server to handle OAuth callback"""
        oauth_service = self
        
        class CallbackHandler(BaseHTTPRequestHandler):
            def do_GET(self):
                # Parse the callback URL
                parsed_url = urllib.parse.urlparse(self.path)
                query_params = urllib.parse.parse_qs(parsed_url.query)
                
                if 'code' in query_params:
                    # Store authorization code
                    oauth_service.authorization_code = query_params['code'][0]
                    
                    # Send success response
                    self.send_response(200)
                    self.send_header('Content-type', 'text/html')
                    self.end_headers()
                    
                    success_html = """
                    <html>
                    <head><title>OAuth2 Success</title></head>
                    <body style="font-family: Arial; text-align: center; padding: 50px;">
                        <h1 style="color: green;">✅ Authorization Successful!</h1>
                        <p>You can close this window and return to ApplicationBot.</p>
                        <p>The OAuth2 setup will complete automatically.</p>
                    </body>
                    </html>
                    """
                    self.wfile.write(success_html.encode())
                    
                elif 'error' in query_params:
                    # Handle error
                    error = query_params['error'][0]
                    oauth_service.authorization_code = f"ERROR:{error}"
                    
                    self.send_response(400)
                    self.send_header('Content-type', 'text/html')
                    self.end_headers()
                    
                    error_html = f"""
                    <html>
                    <head><title>OAuth2 Error</title></head>
                    <body style="font-family: Arial; text-align: center; padding: 50px;">
                        <h1 style="color: red;">❌ Authorization Failed</h1>
                        <p>Error: {error}</p>
                        <p>Please try again or contact support.</p>
                    </body>
                    </html>
                    """
                    self.wfile.write(error_html.encode())
                
                # Signal server to shutdown after handling request
                threading.Thread(target=oauth_service._shutdown_server, daemon=True).start()
            
            def log_message(self, format, *args):
                # Suppress server logs
                pass
        
        # Start server in separate thread
        self.server = HTTPServer(('localhost', port), CallbackHandler)
        self.server_thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.server_thread.start()
        
        logger.info(f"OAuth callback server started on http://localhost:{port}")

    def _shutdown_server(self):
        """Shutdown the callback server after a delay"""
        import time
        time.sleep(2)  # Give time for response to be sent
        if self.server:
            self.server.shutdown()
            self.server.server_close()
            logger.info("OAuth callback server shutdown")

    def wait_for_authorization(self, timeout_seconds: int = 300) -> str:
        """
        Wait for user to complete authorization and return the code
        
        Args:
            timeout_seconds: How long to wait for authorization
            
        Returns:
            Authorization code or error message
        """
        import time
        
        start_time = time.time()
        while self.authorization_code is None:
            if time.time() - start_time > timeout_seconds:
                self._shutdown_server()
                return "TIMEOUT:User did not complete authorization in time"
            
            time.sleep(1)
        
        return self.authorization_code

    def complete_oauth_flow_with_code(self, authorization_code: str) -> Dict[str, Any]:
        """
        Complete OAuth2 flow with authorization code
        
        Args:
            authorization_code: Code received from OAuth callback
            
        Returns:
            Credentials dictionary to store
        """
        try:
            if not self.flow:
                raise ValueError("OAuth flow not initialized. Call setup_oauth_flow_with_server first.")
            
            if authorization_code.startswith("ERROR:"):
                raise ValueError(f"Authorization failed: {authorization_code[6:]}")
                
            if authorization_code.startswith("TIMEOUT:"):
                raise ValueError(f"Authorization timeout: {authorization_code[8:]}")
            
            # Exchange code for credentials
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
            
            logger.info("OAuth2 flow completed successfully with local server")
            return creds_data
            
        except Exception as e:
            logger.error(f"Failed to complete OAuth flow: {e}")
            raise

    def complete_oauth_flow_automated(self, credentials_file_path: str, port: int = 8080, timeout: int = 300) -> Dict[str, Any]:
        """
        Complete entire OAuth flow automatically using local server
        
        Args:
            credentials_file_path: Path to OAuth credentials JSON
            port: Port for callback server
            timeout: Timeout in seconds
            
        Returns:
            Credentials dictionary ready for storage
        """
        try:
            # Start OAuth flow with local server
            auth_url = self.setup_oauth_flow_with_server(credentials_file_path, port)
            
            # Return both the auth URL and indicate we're waiting
            return {
                'status': 'waiting_for_authorization',
                'authorization_url': auth_url,
                'message': 'Please visit the authorization URL and grant permissions',
                'port': port,
                'timeout': timeout
            }
            
        except Exception as e:
            logger.error(f"Failed to start automated OAuth flow: {e}")
            raise

    def check_authorization_status(self) -> Dict[str, Any]:
        """Check if authorization has been completed"""
        if self.authorization_code is None:
            return {
                'status': 'waiting',
                'message': 'Still waiting for user authorization'
            }
        
        if self.authorization_code.startswith("ERROR:"):
            return {
                'status': 'error',
                'message': f'Authorization failed: {self.authorization_code[6:]}'
            }
            
        if self.authorization_code.startswith("TIMEOUT:"):
            return {
                'status': 'timeout',
                'message': f'Authorization timeout: {self.authorization_code[8:]}'
            }
        
        # Complete the flow
        try:
            creds_data = self.complete_oauth_flow_with_code(self.authorization_code)
            return {
                'status': 'completed',
                'message': 'Authorization completed successfully',
                'credentials': creds_data
            }
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Failed to complete authorization: {str(e)}'
            }

    # All the existing methods from OAuth2EmailService for email processing
    def load_credentials(self, creds_data: Dict[str, Any]) -> bool:
        """Load credentials from stored data"""
        try:
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
            
            if self.credentials.expired and self.credentials.refresh_token:
                self.credentials.refresh(Request())
                logger.info("OAuth2 credentials refreshed")
            
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
        """Fetch job-related emails using Gmail API"""
        if not self.service:
            raise ValueError("Gmail service not initialized. Load credentials first.")
        
        jobs = []
        
        try:
            since_date = datetime.now() - timedelta(days=days_back)
            query_date = since_date.strftime('%Y/%m/%d')
            
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
                    query = f'from:{sender} after:{query_date}'
                    
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
            message = self.service.users().messages().get(
                userId='me',
                id=message_id,
                format='full'
            ).execute()
            
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
            
            if not self._is_job_email_by_subject_sender(subject, sender):
                return None
            
            email_content = self._extract_gmail_content(message['payload'])
            if not email_content:
                return None
            
            parser = EmailJobParserService()
            platform = self._determine_platform_from_sender(sender)
            jobs = parser._extract_jobs_from_content(email_content, platform)
            
            if jobs:
                job = jobs[0]
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
        
        job_senders = ['linkedin', 'indeed', 'builtin', 'ziprecruiter']
        sender_match = any(platform in sender_lower for platform in job_senders)
        
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
            return JobPlatform.LINKEDIN

    def test_connection(self) -> Dict[str, Any]:
        """Test Gmail API connection and permissions"""
        if not self.service:
            return {"success": False, "error": "Service not initialized"}
        
        try:
            profile = self.service.users().getProfile(userId='me').execute()
            
            return {
                "success": True,
                "email": profile.get('emailAddress'),
                "messages_total": profile.get('messagesTotal', 0),
                "threads_total": profile.get('threadsTotal', 0)
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}