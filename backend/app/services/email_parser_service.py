import imaplib
import email
import re
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from email.header import decode_header
from bs4 import BeautifulSoup
import logging
from app.core.config import settings
from app.models.job import Job, JobPlatform, JobPriority, JobStatus

logger = logging.getLogger(__name__)

class EmailJobParserService:
    """Service to parse job opportunities from platform emails"""
    
    def __init__(self):
        self.imap_server = None
        self.email_patterns = {
            JobPlatform.LINKEDIN: {
                'sender_patterns': ['linkedin.com', 'jobs-noreply@linkedin.com'],
                'subject_patterns': ['job alert', 'new jobs', 'recommended for you'],
                'job_title_patterns': [
                    r'<a[^>]*href="[^"]*jobs/view/\d+"[^>]*>([^<]+)</a>',
                    r'Job Title:\s*([^\n\r]+)',
                    r'<strong>([^<]+)</strong>\s*at\s*[^<]+'
                ],
                'company_patterns': [
                    r'at\s+<a[^>]*>([^<]+)</a>',
                    r'Company:\s*([^\n\r]+)',
                    r'<strong>[^<]+</strong>\s*at\s*([^<\n\r]+)'
                ],
                'location_patterns': [
                    r'Location:\s*([^\n\r]+)',
                    r'<span[^>]*location[^>]*>([^<]+)</span>'
                ],
                'url_patterns': [
                    r'href="(https://[^"]*linkedin\.com/jobs/view/\d+[^"]*)"'
                ]
            },
            JobPlatform.INDEED: {
                'sender_patterns': ['indeed.com', 'noreply@indeed.com'],
                'subject_patterns': ['job alert', 'new jobs matching', 'recommended jobs'],
                'job_title_patterns': [
                    r'<a[^>]*href="[^"]*"[^>]*><strong>([^<]+)</strong></a>',
                    r'Job:\s*([^\n\r]+)',
                    r'<h3[^>]*>([^<]+)</h3>'
                ],
                'company_patterns': [
                    r'<span[^>]*company[^>]*>([^<]+)</span>',
                    r'Company:\s*([^\n\r]+)'
                ],
                'location_patterns': [
                    r'<span[^>]*location[^>]*>([^<]+)</span>',
                    r'Location:\s*([^\n\r]+)'
                ],
                'url_patterns': [
                    r'href="(https://[^"]*indeed\.com/[^"]*)"'
                ]
            },
            JobPlatform.BUILTIN: {
                'sender_patterns': ['builtin.com', 'jobs@builtin.com'],
                'subject_patterns': ['job recommendations', 'new job matches'],
                'job_title_patterns': [
                    r'<a[^>]*>([^<]+)</a>\s*at',
                    r'Position:\s*([^\n\r]+)'
                ],
                'company_patterns': [
                    r'at\s+([^\n\r<]+)',
                    r'Company:\s*([^\n\r]+)'
                ],
                'location_patterns': [
                    r'Location:\s*([^\n\r]+)'
                ],
                'url_patterns': [
                    r'href="(https://[^"]*builtin\.com/[^"]*)"'
                ]
            }
        }

    def connect_to_email(self, email_server: str, email_user: str, email_password: str) -> bool:
        """Connect to email server using IMAP"""
        try:
            self.imap_server = imaplib.IMAP4_SSL(email_server)
            self.imap_server.login(email_user, email_password)
            self.imap_server.select("INBOX")
            logger.info(f"Successfully connected to email server: {email_server}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to email server: {e}")
            return False

    def fetch_job_emails(self, days_back: int = 7) -> List[Dict[str, Any]]:
        """Fetch job-related emails from the last N days"""
        if not self.imap_server:
            logger.error("Email server not connected")
            return []

        jobs = []
        try:
            # Calculate date range
            since_date = (datetime.now() - timedelta(days=days_back)).strftime("%d-%b-%Y")
            
            # Search for emails from job platforms
            for platform, patterns in self.email_patterns.items():
                for sender_pattern in patterns['sender_patterns']:
                    try:
                        # Search criteria
                        search_criteria = f'(FROM "{sender_pattern}" SINCE {since_date})'
                        _, message_numbers = self.imap_server.search(None, search_criteria)
                        
                        for num in message_numbers[0].split():
                            try:
                                job_data = self._parse_email_message(num, platform)
                                if job_data:
                                    jobs.append(job_data)
                            except Exception as e:
                                logger.error(f"Error parsing email {num}: {e}")
                                continue
                                
                    except Exception as e:
                        logger.error(f"Error searching emails from {sender_pattern}: {e}")
                        continue

        except Exception as e:
            logger.error(f"Error fetching job emails: {e}")

        logger.info(f"Parsed {len(jobs)} jobs from emails")
        return jobs

    def _parse_email_message(self, message_num: bytes, platform: JobPlatform) -> Optional[Dict[str, Any]]:
        """Parse individual email message for job information"""
        try:
            _, msg_data = self.imap_server.fetch(message_num, "(RFC822)")
            email_body = msg_data[0][1]
            email_message = email.message_from_bytes(email_body)
            
            # Get email metadata
            subject = self._decode_email_header(email_message["Subject"])
            sender = email_message["From"]
            date_received = email.utils.parsedate_to_datetime(email_message["Date"])
            
            # Check if this is a job-related email
            if not self._is_job_email(subject, sender, platform):
                return None
            
            # Extract email content
            email_content = self._extract_email_content(email_message)
            if not email_content:
                return None
            
            # Parse job information from content
            jobs = self._extract_jobs_from_content(email_content, platform)
            
            # Return the first job found (or combine if multiple)
            if jobs:
                job = jobs[0]  # Take first job for now
                job.update({
                    'email_subject': subject,
                    'email_date': date_received,
                    'source': 'email',
                    'discovered_at': datetime.now()
                })
                return job
                
        except Exception as e:
            logger.error(f"Error parsing email message: {e}")
            
        return None

    def _decode_email_header(self, header: str) -> str:
        """Decode email header properly"""
        if not header:
            return ""
        
        decoded_header = decode_header(header)
        header_text = ""
        
        for part, encoding in decoded_header:
            if isinstance(part, bytes):
                part = part.decode(encoding or 'utf-8', errors='ignore')
            header_text += part
            
        return header_text

    def _is_job_email(self, subject: str, sender: str, platform: JobPlatform) -> bool:
        """Check if email is job-related based on subject and sender"""
        patterns = self.email_patterns.get(platform, {})
        
        # Check sender
        sender_match = any(pattern in sender.lower() for pattern in patterns.get('sender_patterns', []))
        
        # Check subject
        subject_match = any(pattern in subject.lower() for pattern in patterns.get('subject_patterns', []))
        
        return sender_match and subject_match

    def _extract_email_content(self, email_message) -> str:
        """Extract readable content from email message"""
        content = ""
        
        if email_message.is_multipart():
            for part in email_message.walk():
                content_type = part.get_content_type()
                content_disposition = str(part.get("Content-Disposition"))
                
                if content_type == "text/html" and "attachment" not in content_disposition:
                    try:
                        body = part.get_payload(decode=True).decode('utf-8', errors='ignore')
                        # Parse HTML content
                        soup = BeautifulSoup(body, 'html.parser')
                        content = soup.get_text() + "\n" + body  # Keep both text and HTML
                        break
                    except:
                        continue
                elif content_type == "text/plain" and "attachment" not in content_disposition:
                    try:
                        content = part.get_payload(decode=True).decode('utf-8', errors='ignore')
                    except:
                        continue
        else:
            try:
                content = email_message.get_payload(decode=True).decode('utf-8', errors='ignore')
            except:
                pass
                
        return content

    def _extract_jobs_from_content(self, content: str, platform: JobPlatform) -> List[Dict[str, Any]]:
        """Extract job information from email content using regex patterns"""
        jobs = []
        patterns = self.email_patterns.get(platform, {})
        
        try:
            # Find all job titles
            job_titles = []
            for pattern in patterns.get('job_title_patterns', []):
                matches = re.findall(pattern, content, re.IGNORECASE | re.DOTALL)
                job_titles.extend([self._clean_text(match) for match in matches])
            
            # Find all companies
            companies = []
            for pattern in patterns.get('company_patterns', []):
                matches = re.findall(pattern, content, re.IGNORECASE | re.DOTALL)
                companies.extend([self._clean_text(match) for match in matches])
            
            # Find all locations
            locations = []
            for pattern in patterns.get('location_patterns', []):
                matches = re.findall(pattern, content, re.IGNORECASE | re.DOTALL)
                locations.extend([self._clean_text(match) for match in matches])
            
            # Find all URLs
            urls = []
            for pattern in patterns.get('url_patterns', []):
                matches = re.findall(pattern, content, re.IGNORECASE)
                urls.extend(matches)
            
            # Combine job information
            max_jobs = max(len(job_titles), len(companies), len(urls))
            
            for i in range(max_jobs):
                job_data = {
                    'title': job_titles[i] if i < len(job_titles) else 'Unknown Position',
                    'company': companies[i] if i < len(companies) else 'Unknown Company',
                    'location': locations[i] if i < len(locations) else 'Location not specified',
                    'application_url': urls[i] if i < len(urls) else '',
                    'platform': platform,
                    'platform_id': self._extract_platform_id(urls[i] if i < len(urls) else '', platform),
                    'status': JobStatus.DISCOVERED,
                    'priority': self._determine_priority(job_titles[i] if i < len(job_titles) else ''),
                    'fit_score': 7.0,  # Default score, can be improved with AI
                    'posted_date': datetime.now() - timedelta(hours=24),  # Assume recent
                    'is_remote': self._detect_remote(locations[i] if i < len(locations) else ''),
                }
                
                # Only add if we have meaningful data
                if job_data['title'] != 'Unknown Position' or job_data['company'] != 'Unknown Company':
                    jobs.append(job_data)
                    
        except Exception as e:
            logger.error(f"Error extracting jobs from content: {e}")
            
        return jobs

    def _clean_text(self, text: str) -> str:
        """Clean extracted text"""
        if not text:
            return ""
        
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', '', text)
        # Remove extra whitespace
        text = ' '.join(text.split())
        # Remove common email artifacts
        text = text.replace('&nbsp;', ' ').replace('&amp;', '&')
        
        return text.strip()

    def _extract_platform_id(self, url: str, platform: JobPlatform) -> str:
        """Extract platform-specific job ID from URL"""
        if not url:
            return ""
            
        if platform == JobPlatform.LINKEDIN:
            match = re.search(r'jobs/view/(\d+)', url)
            return match.group(1) if match else ""
        elif platform == JobPlatform.INDEED:
            match = re.search(r'jk=([^&]+)', url)
            return match.group(1) if match else ""
        elif platform == JobPlatform.BUILTIN:
            match = re.search(r'/job/([^/]+)', url)
            return match.group(1) if match else ""
            
        return url.split('/')[-1] if '/' in url else url

    def _determine_priority(self, title: str) -> JobPriority:
        """Determine job priority based on title keywords"""
        title_lower = title.lower()
        
        # High priority keywords
        if any(keyword in title_lower for keyword in ['director', 'vp', 'head of', 'chief', 'senior director']):
            return JobPriority.MUST_APPLY
        
        # Good fit keywords
        if any(keyword in title_lower for keyword in ['senior', 'lead', 'principal', 'manager']):
            return JobPriority.GOOD_FIT
        
        # Stretch keywords
        if any(keyword in title_lower for keyword in ['associate', 'coordinator', 'specialist']):
            return JobPriority.STRETCH
            
        return JobPriority.LOW_PRIORITY

    def _detect_remote(self, location: str) -> bool:
        """Detect if job is remote based on location text"""
        location_lower = location.lower()
        return any(keyword in location_lower for keyword in ['remote', 'work from home', 'anywhere', 'distributed'])

    def close_connection(self):
        """Close email connection"""
        if self.imap_server:
            try:
                self.imap_server.close()
                self.imap_server.logout()
            except:
                pass
            self.imap_server = None