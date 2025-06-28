from typing import Dict, Any, List, Optional
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from app.models.job import Job, JobPlatform
from app.models.application import Application, ApplicationStatus, ApplicationMethod
from app.scrapers import LinkedInScraper, IndeedScraper, BuiltInScraper, ZipRecruiterScraper
import logging
import time
import os

logger = logging.getLogger(__name__)

class ApplicationAutomator:
    def __init__(self):
        self.scrapers = {
            JobPlatform.LINKEDIN: LinkedInScraper,
            JobPlatform.INDEED: IndeedScraper,
            JobPlatform.BUILTIN: BuiltInScraper,
            JobPlatform.ZIPRECRUITER: ZipRecruiterScraper,
        }

    def apply_to_job(
        self,
        job: Job,
        application_data: Dict[str, Any],
        manual_review: bool = False
    ) -> Dict[str, Any]:
        """Apply to a job automatically"""
        
        result = {
            "success": False,
            "application_id": None,
            "method": ApplicationMethod.AUTOMATED,
            "error_message": None,
            "requires_manual_action": False
        }

        try:
            # Get appropriate scraper for the platform
            scraper_class = self.scrapers.get(job.platform)
            if not scraper_class:
                result["error_message"] = f"Unsupported platform: {job.platform}"
                return result

            # Prepare application data
            prepared_data = self._prepare_application_data(job, application_data)

            with scraper_class(headless=not manual_review) as scraper:
                # Login if required
                username, password = self._get_platform_credentials(job.platform)
                if username and password:
                    login_success = scraper.login(username, password)
                    if not login_success:
                        result["error_message"] = "Failed to login to platform"
                        return result

                # Navigate to job and attempt application
                success = scraper.apply_to_job(job.application_url, prepared_data)
                
                if success:
                    result["success"] = True
                    result["method"] = ApplicationMethod.AUTOMATED
                else:
                    # Check if manual intervention is needed
                    result["requires_manual_action"] = True
                    result["method"] = ApplicationMethod.SEMI_AUTOMATED
                    result["error_message"] = "Automated application failed, manual review required"

        except Exception as e:
            logger.error(f"Application automation failed for job {job.id}: {e}")
            result["error_message"] = str(e)

        return result

    def _prepare_application_data(self, job: Job, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare and customize application data for the specific job"""
        
        prepared_data = raw_data.copy()

        # Customize resume and cover letter paths based on job
        if "resume_template_path" in raw_data:
            prepared_data["resume_path"] = self._customize_resume(
                raw_data["resume_template_path"],
                job
            )

        if "cover_letter_template" in raw_data:
            prepared_data["cover_letter_text"] = self._customize_cover_letter(
                raw_data["cover_letter_template"],
                job
            )

        # Platform-specific customizations
        if job.platform == JobPlatform.LINKEDIN:
            prepared_data = self._customize_for_linkedin(prepared_data, job)
        elif job.platform == JobPlatform.INDEED:
            prepared_data = self._customize_for_indeed(prepared_data, job)

        return prepared_data

    def _customize_resume(self, template_path: str, job: Job) -> str:
        """Customize resume for the specific job"""
        # This would integrate with the document customization service
        # For now, return the template path
        return template_path

    def _customize_cover_letter(self, template: str, job: Job) -> str:
        """Generate customized cover letter"""
        # Replace placeholders in template
        customized = template.replace("{company}", job.company)
        customized = customized.replace("{position}", job.title)
        customized = customized.replace("{location}", job.location or "")
        
        return customized

    def _customize_for_linkedin(self, data: Dict[str, Any], job: Job) -> Dict[str, Any]:
        """LinkedIn-specific customizations"""
        # LinkedIn prefers shorter, more direct applications
        if "cover_letter_text" in data and len(data["cover_letter_text"]) > 500:
            data["cover_letter_text"] = data["cover_letter_text"][:500] + "..."
        
        return data

    def _customize_for_indeed(self, data: Dict[str, Any], job: Job) -> Dict[str, Any]:
        """Indeed-specific customizations"""
        # Indeed often has specific screening questions
        screening_answers = {
            "work_authorization": data.get("work_authorization", "Yes, I am authorized to work in the US"),
            "commute_distance": "Less than 25 miles" if not job.is_remote else "Remote work",
            "salary_expectation": data.get("salary_expectation", "Negotiable")
        }
        
        data.update(screening_answers)
        return data

    def _get_platform_credentials(self, platform: JobPlatform) -> tuple:
        """Get credentials for platform login"""
        from app.core.config import settings
        
        credential_map = {
            JobPlatform.LINKEDIN: (settings.LINKEDIN_USERNAME, settings.LINKEDIN_PASSWORD),
            JobPlatform.INDEED: (settings.INDEED_USERNAME, settings.INDEED_PASSWORD),
        }
        return credential_map.get(platform, (None, None))

    def detect_application_form_fields(self, job_url: str, platform: JobPlatform) -> List[Dict[str, Any]]:
        """Detect and analyze application form fields"""
        
        fields = []
        try:
            scraper_class = self.scrapers.get(platform)
            if not scraper_class:
                return fields

            with scraper_class(headless=True) as scraper:
                scraper.driver.get(job_url)
                time.sleep(3)

                # Find apply button and click to access form
                apply_button = scraper.safe_find_element(By.CSS_SELECTOR, self._get_apply_button_selector(platform))
                if apply_button:
                    apply_button.click()
                    time.sleep(3)

                    # Detect form fields
                    form_fields = scraper.driver.find_elements(By.CSS_SELECTOR, "input, select, textarea")
                    
                    for field in form_fields:
                        field_info = self._analyze_form_field(field)
                        if field_info:
                            fields.append(field_info)

        except Exception as e:
            logger.error(f"Form detection failed: {e}")

        return fields

    def _analyze_form_field(self, element) -> Optional[Dict[str, Any]]:
        """Analyze a form field to determine its purpose"""
        try:
            field_type = element.get_attribute("type") or element.tag_name
            field_name = element.get_attribute("name") or ""
            field_id = element.get_attribute("id") or ""
            placeholder = element.get_attribute("placeholder") or ""
            label_text = ""

            # Try to find associated label
            try:
                if field_id:
                    label = element.find_element(By.CSS_SELECTOR, f"label[for='{field_id}']")
                    label_text = label.text
            except:
                pass

            # Determine field purpose
            field_purpose = self._determine_field_purpose(field_name, field_id, placeholder, label_text)

            return {
                "type": field_type,
                "name": field_name,
                "id": field_id,
                "placeholder": placeholder,
                "label": label_text,
                "purpose": field_purpose,
                "required": element.get_attribute("required") == "true"
            }

        except Exception:
            return None

    def _determine_field_purpose(self, name: str, field_id: str, placeholder: str, label: str) -> str:
        """Determine the purpose of a form field"""
        
        text_to_analyze = f"{name} {field_id} {placeholder} {label}".lower()

        field_mapping = {
            "first_name": ["first", "fname", "firstname", "given"],
            "last_name": ["last", "lname", "lastname", "surname", "family"],
            "email": ["email", "e-mail"],
            "phone": ["phone", "telephone", "mobile", "cell"],
            "address": ["address", "street"],
            "city": ["city"],
            "state": ["state", "province"],
            "zip": ["zip", "postal", "postcode"],
            "linkedin": ["linkedin", "profile"],
            "portfolio": ["portfolio", "website", "url"],
            "resume": ["resume", "cv", "curriculum"],
            "cover_letter": ["cover", "letter", "motivation"],
            "salary": ["salary", "compensation", "pay", "wage"],
            "availability": ["start", "available", "notice"],
            "work_auth": ["authorization", "eligible", "visa", "permit"],
            "experience": ["experience", "years"],
            "education": ["education", "degree", "school", "university"]
        }

        for purpose, keywords in field_mapping.items():
            if any(keyword in text_to_analyze for keyword in keywords):
                return purpose

        return "unknown"

    def _get_apply_button_selector(self, platform: JobPlatform) -> str:
        """Get CSS selector for apply button based on platform"""
        selectors = {
            JobPlatform.LINKEDIN: ".jobs-apply-button",
            JobPlatform.INDEED: ".ia-IndeedApplyButton",
            JobPlatform.BUILTIN: ".apply-button",
            JobPlatform.ZIPRECRUITER: ".apply_button"
        }
        return selectors.get(platform, "button[class*='apply']")

    def validate_application_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate application data completeness"""
        
        required_fields = [
            "first_name", "last_name", "email", "phone",
            "resume_path", "work_authorization"
        ]

        recommended_fields = [
            "linkedin_url", "portfolio_url", "cover_letter_template",
            "salary_expectation", "availability_date"
        ]

        validation_result = {
            "is_valid": True,
            "missing_required": [],
            "missing_recommended": [],
            "warnings": []
        }

        # Check required fields
        for field in required_fields:
            if field not in data or not data[field]:
                validation_result["missing_required"].append(field)
                validation_result["is_valid"] = False

        # Check recommended fields
        for field in recommended_fields:
            if field not in data or not data[field]:
                validation_result["missing_recommended"].append(field)

        # Validate file paths
        if "resume_path" in data and data["resume_path"]:
            if not os.path.exists(data["resume_path"]):
                validation_result["warnings"].append("Resume file not found")
                validation_result["is_valid"] = False

        # Validate email format
        if "email" in data:
            import re
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(email_pattern, data["email"]):
                validation_result["warnings"].append("Invalid email format")

        return validation_result