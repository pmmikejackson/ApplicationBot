from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib
from datetime import datetime, timedelta
from app.models.communication import Communication, CommunicationType, CommunicationDirection, CommunicationStatus
from app.models.job import Job
from app.models.application import Application
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

class CommunicationService:
    def __init__(self, db: Session):
        self.db = db

    def send_follow_up_email(
        self,
        job: Job,
        application: Application,
        template_type: str = "follow_up",
        custom_message: Optional[str] = None
    ) -> bool:
        """Send follow-up email after application submission"""
        
        try:
            # Get email template
            email_content = self._get_email_template(template_type, job, application)
            if custom_message:
                email_content = custom_message

            # Send email
            success = self._send_email(
                to_email=self._get_company_email(job),
                subject=f"Following up on {job.title} Application",
                content=email_content
            )

            # Log communication
            communication = Communication(
                job_id=job.id,
                type=CommunicationType.EMAIL,
                direction=CommunicationDirection.OUTBOUND,
                status=CommunicationStatus.SENT if success else CommunicationStatus.FAILED,
                subject=f"Following up on {job.title} Application",
                content=email_content,
                recipient_email=self._get_company_email(job),
                sender_email=settings.SMTP_USER,
                sent_at=datetime.utcnow() if success else None,
                is_automated=True,
                template_used=template_type
            )

            self.db.add(communication)
            self.db.commit()

            return success

        except Exception as e:
            logger.error(f"Follow-up email failed: {e}")
            return False

    def schedule_follow_up(
        self,
        job: Job,
        application: Application,
        days_delay: int = 7,
        template_type: str = "follow_up"
    ) -> Communication:
        """Schedule a follow-up email for later sending"""
        
        scheduled_time = datetime.utcnow() + timedelta(days=days_delay)
        email_content = self._get_email_template(template_type, job, application)

        communication = Communication(
            job_id=job.id,
            type=CommunicationType.EMAIL,
            direction=CommunicationDirection.OUTBOUND,
            status=CommunicationStatus.SCHEDULED,
            subject=f"Following up on {job.title} Application",
            content=email_content,
            recipient_email=self._get_company_email(job),
            sender_email=settings.SMTP_USER,
            scheduled_at=scheduled_time,
            is_automated=True,
            template_used=template_type
        )

        self.db.add(communication)
        self.db.commit()

        return communication

    def send_thank_you_email(
        self,
        job: Job,
        interviewer_email: str,
        interviewer_name: str,
        interview_date: datetime
    ) -> bool:
        """Send thank you email after interview"""
        
        try:
            email_content = self._get_thank_you_template(
                job, interviewer_name, interview_date
            )

            success = self._send_email(
                to_email=interviewer_email,
                subject=f"Thank you for the {job.title} interview",
                content=email_content
            )

            # Log communication
            communication = Communication(
                job_id=job.id,
                type=CommunicationType.EMAIL,
                direction=CommunicationDirection.OUTBOUND,
                status=CommunicationStatus.SENT if success else CommunicationStatus.FAILED,
                subject=f"Thank you for the {job.title} interview",
                content=email_content,
                recipient_email=interviewer_email,
                sender_email=settings.SMTP_USER,
                sent_at=datetime.utcnow() if success else None,
                is_automated=True,
                template_used="thank_you"
            )

            self.db.add(communication)
            self.db.commit()

            return success

        except Exception as e:
            logger.error(f"Thank you email failed: {e}")
            return False

    def process_scheduled_communications(self) -> Dict[str, int]:
        """Process all scheduled communications that are due"""
        
        now = datetime.utcnow()
        scheduled_comms = self.db.query(Communication).filter(
            Communication.status == CommunicationStatus.SCHEDULED,
            Communication.scheduled_at <= now
        ).all()

        results = {"sent": 0, "failed": 0}

        for comm in scheduled_comms:
            try:
                if comm.type == CommunicationType.EMAIL:
                    success = self._send_email(
                        to_email=comm.recipient_email,
                        subject=comm.subject,
                        content=comm.content
                    )

                    if success:
                        comm.status = CommunicationStatus.SENT
                        comm.sent_at = datetime.utcnow()
                        results["sent"] += 1
                    else:
                        comm.status = CommunicationStatus.FAILED
                        results["failed"] += 1

                    self.db.commit()

            except Exception as e:
                logger.error(f"Failed to send scheduled communication {comm.id}: {e}")
                comm.status = CommunicationStatus.FAILED
                self.db.commit()
                results["failed"] += 1

        return results

    def _send_email(self, to_email: str, subject: str, content: str) -> bool:
        """Send email using SMTP"""
        
        if not all([settings.SMTP_HOST, settings.SMTP_USER, settings.SMTP_PASSWORD]):
            logger.warning("SMTP settings not configured")
            return False

        try:
            # Create message
            msg = MIMEMultipart()
            msg['From'] = settings.SMTP_USER
            msg['To'] = to_email
            msg['Subject'] = subject

            # Attach content
            msg.attach(MIMEText(content, 'plain'))

            # Connect to server and send
            server = smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT)
            if settings.SMTP_TLS:
                server.starttls()
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            
            text = msg.as_string()
            server.sendmail(settings.SMTP_USER, to_email, text)
            server.quit()

            logger.info(f"Email sent successfully to {to_email}")
            return True

        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {e}")
            return False

    def _get_email_template(
        self,
        template_type: str,
        job: Job,
        application: Application
    ) -> str:
        """Get email template based on type"""
        
        templates = {
            "follow_up": self._get_follow_up_template(job, application),
            "check_in": self._get_check_in_template(job),
            "withdrawal": self._get_withdrawal_template(job),
            "status_inquiry": self._get_status_inquiry_template(job)
        }

        return templates.get(template_type, templates["follow_up"])

    def _get_follow_up_template(self, job: Job, application: Application) -> str:
        """Generate follow-up email template"""
        
        return f"""
Dear Hiring Manager,

I hope this email finds you well. I wanted to follow up on my application for the {job.title} position at {job.company}, which I submitted on {application.submitted_at.strftime('%B %d, %Y') if application.submitted_at else 'recently'}.

I remain very interested in this opportunity and believe my experience in product management would be a valuable addition to your team. I'm particularly excited about {job.company}'s innovative approach and would welcome the chance to contribute to your continued success.

If you need any additional information from me or would like to schedule a conversation, please don't hesitate to reach out. I look forward to hearing from you.

Best regards,
[Your Name]
        """.strip()

    def _get_check_in_template(self, job: Job) -> str:
        """Generate check-in email template"""
        
        return f"""
Dear Hiring Team,

I hope you're doing well. I wanted to check in regarding the {job.title} position at {job.company}. I submitted my application a few weeks ago and wanted to see if there are any updates on the hiring process.

I remain very enthusiastic about this opportunity and would be happy to provide any additional information you might need.

Thank you for your time and consideration.

Best regards,
[Your Name]
        """.strip()

    def _get_thank_you_template(
        self,
        job: Job,
        interviewer_name: str,
        interview_date: datetime
    ) -> str:
        """Generate thank you email template"""
        
        return f"""
Dear {interviewer_name},

Thank you for taking the time to speak with me about the {job.title} position at {job.company} on {interview_date.strftime('%B %d, %Y')}. I enjoyed our conversation and learning more about the team's goals and challenges.

Our discussion reinforced my enthusiasm for this role and my belief that my experience in product management would be a strong fit for your team. I'm particularly excited about the opportunity to contribute to [specific project or initiative discussed].

Please let me know if you need any additional information from me. I look forward to the next steps in the process.

Best regards,
[Your Name]
        """.strip()

    def _get_withdrawal_template(self, job: Job) -> str:
        """Generate application withdrawal template"""
        
        return f"""
Dear Hiring Manager,

I hope this email finds you well. I am writing to formally withdraw my application for the {job.title} position at {job.company}.

After careful consideration, I have decided to pursue a different opportunity that better aligns with my career goals at this time.

I appreciate the time and consideration you have given my application, and I have great respect for {job.company} and the work you do. I hope our paths may cross again in the future.

Thank you again for your time and consideration.

Best regards,
[Your Name]
        """.strip()

    def _get_status_inquiry_template(self, job: Job) -> str:
        """Generate status inquiry template"""
        
        return f"""
Dear Hiring Team,

I hope you're well. I'm writing to inquire about the status of my application for the {job.title} position at {job.company}.

I submitted my application several weeks ago and remain very interested in this opportunity. I understand that hiring processes can take time, and I wanted to respectfully check if there are any updates you can share.

If you need any additional information from me, please don't hesitate to ask. I appreciate your time and consideration.

Best regards,
[Your Name]
        """.strip()

    def _get_company_email(self, job: Job) -> str:
        """Extract or guess company email from job posting"""
        
        # This is a simplified implementation
        # In practice, you might want to parse the job description for contact info
        # or maintain a database of company HR emails
        
        company_domains = {
            "google": "jobs@google.com",
            "microsoft": "careers@microsoft.com",
            "amazon": "recruiting@amazon.com",
            "apple": "jobs@apple.com",
            "meta": "careers@meta.com",
            "netflix": "jobs@netflix.com"
        }

        company_lower = job.company.lower()
        for company, email in company_domains.items():
            if company in company_lower:
                return email

        # Fallback to generic format
        domain = company_lower.replace(" ", "").replace(",", "").replace(".", "")
        return f"careers@{domain}.com"

    def get_communication_history(self, job_id: int) -> List[Communication]:
        """Get all communications for a specific job"""
        
        return self.db.query(Communication).filter(
            Communication.job_id == job_id
        ).order_by(Communication.created_at.desc()).all()

    def mark_communication_received(
        self,
        job_id: int,
        sender_email: str,
        subject: str,
        content: str
    ) -> Communication:
        """Record received communication (email, call, etc.)"""
        
        communication = Communication(
            job_id=job_id,
            type=CommunicationType.EMAIL,
            direction=CommunicationDirection.INBOUND,
            status=CommunicationStatus.RECEIVED,
            subject=subject,
            content=content,
            sender_email=sender_email,
            recipient_email=settings.SMTP_USER,
            sent_at=datetime.utcnow(),
            is_automated=False
        )

        self.db.add(communication)
        self.db.commit()

        return communication