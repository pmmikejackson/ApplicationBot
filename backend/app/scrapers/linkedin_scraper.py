from typing import List, Dict, Any
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from .base_scraper import BaseScraper
from app.models.job import JobPlatform
import re
from datetime import datetime, timedelta

class LinkedInScraper(BaseScraper):
    def __init__(self, headless: bool = True):
        super().__init__(JobPlatform.LINKEDIN, headless)
        self.base_url = "https://www.linkedin.com"
        self.jobs_url = "https://www.linkedin.com/jobs/search"

    def login(self, username: str, password: str) -> bool:
        try:
            self.driver.get(f"{self.base_url}/login")
            self.random_delay()

            # Enter username
            username_field = self.safe_find_element(By.ID, "username")
            if not username_field:
                return False
            username_field.send_keys(username)

            # Enter password
            password_field = self.safe_find_element(By.ID, "password")
            if not password_field:
                return False
            password_field.send_keys(password)

            # Click login button
            login_button = self.safe_find_element(By.XPATH, "//button[@type='submit']")
            if not login_button:
                return False
            login_button.click()

            self.random_delay()

            # Check if login was successful
            return "feed" in self.driver.current_url or "jobs" in self.driver.current_url

        except Exception as e:
            print(f"LinkedIn login failed: {e}")
            return False

    def search_jobs(self, keywords: List[str], location: str, **kwargs) -> List[Dict[str, Any]]:
        jobs = []
        try:
            # Build search URL
            keyword_str = " OR ".join(keywords)
            params = {
                "keywords": keyword_str,
                "location": location,
                "f_TPR": "r86400",  # Last 24 hours
                "f_WT": "2,3" if kwargs.get("remote_only") else None,  # Remote/hybrid
                "f_E": "3,4" if kwargs.get("senior_level") else None,  # Senior level
            }

            # Build URL
            url_params = "&".join([f"{k}={v}" for k, v in params.items() if v is not None])
            search_url = f"{self.jobs_url}?{url_params}"

            self.driver.get(search_url)
            self.random_delay()

            # Get job cards
            job_cards = self.driver.find_elements(By.CSS_SELECTOR, ".job-search-card")
            
            for card in job_cards[:20]:  # Limit to first 20 jobs
                try:
                    job_data = self._extract_job_from_card(card)
                    if job_data:
                        jobs.append(job_data)
                except Exception as e:
                    print(f"Error extracting job from card: {e}")
                    continue

        except Exception as e:
            print(f"LinkedIn job search failed: {e}")

        return jobs

    def _extract_job_from_card(self, card) -> Dict[str, Any]:
        try:
            # Job title and link
            title_element = card.find_element(By.CSS_SELECTOR, ".base-search-card__title a")
            title = self.safe_get_text(title_element)
            job_url = self.safe_get_attribute(title_element, "href")

            # Company
            company_element = card.find_element(By.CSS_SELECTOR, ".base-search-card__subtitle a")
            company = self.safe_get_text(company_element)

            # Location
            location_element = card.find_element(By.CSS_SELECTOR, ".job-search-card__location")
            location = self.safe_get_text(location_element)

            # Posted date
            posted_element = card.find_element(By.CSS_SELECTOR, "time")
            posted_date = self._parse_posted_date(self.safe_get_text(posted_element))

            # Extract platform ID from URL
            platform_id = self._extract_job_id_from_url(job_url)

            return {
                "title": title,
                "company": company,
                "location": location,
                "application_url": job_url,
                "platform": JobPlatform.LINKEDIN,
                "platform_id": platform_id,
                "posted_date": posted_date,
                "is_remote": "remote" in location.lower(),
                "is_hybrid": "hybrid" in location.lower(),
            }

        except NoSuchElementException:
            return None

    def get_job_details(self, job_url: str) -> Dict[str, Any]:
        try:
            self.driver.get(job_url)
            self.random_delay()

            # Job description
            description_element = self.safe_find_element(By.CSS_SELECTOR, ".show-more-less-html__markup")
            description = self.safe_get_text(description_element)

            # Salary (if available)
            salary_element = self.safe_find_element(By.CSS_SELECTOR, ".salary")
            salary_text = self.safe_get_text(salary_element)
            salary_min, salary_max = self._parse_salary(salary_text)

            # Company details
            company_element = self.safe_find_element(By.CSS_SELECTOR, ".job-details-jobs-unified-top-card__company-name")
            company = self.safe_get_text(company_element)

            return {
                "description": description,
                "salary_min": salary_min,
                "salary_max": salary_max,
                "company": company,
            }

        except Exception as e:
            print(f"Error getting LinkedIn job details: {e}")
            return {}

    def apply_to_job(self, job_url: str, application_data: Dict[str, Any]) -> bool:
        try:
            self.driver.get(job_url)
            self.random_delay()

            # Look for "Easy Apply" button
            apply_button = self.safe_find_element(By.CSS_SELECTOR, ".jobs-apply-button")
            if not apply_button or "Easy Apply" not in apply_button.text:
                return False

            apply_button.click()
            self.random_delay()

            # Handle multi-step application process
            return self._handle_application_flow(application_data)

        except Exception as e:
            print(f"LinkedIn application failed: {e}")
            return False

    def _handle_application_flow(self, application_data: Dict[str, Any]) -> bool:
        max_steps = 5
        current_step = 0

        while current_step < max_steps:
            try:
                # Check if we're on a form page
                if self.safe_find_element(By.CSS_SELECTOR, ".jobs-easy-apply-content"):
                    # Fill form fields
                    self._fill_application_form(application_data)
                    
                    # Look for Next or Submit button
                    next_button = self.safe_find_element(By.CSS_SELECTOR, "button[aria-label='Continue to next step']")
                    submit_button = self.safe_find_element(By.CSS_SELECTOR, "button[aria-label='Submit application']")
                    
                    if submit_button:
                        submit_button.click()
                        self.random_delay()
                        return True
                    elif next_button:
                        next_button.click()
                        self.random_delay()
                        current_step += 1
                    else:
                        break
                else:
                    break

            except Exception as e:
                print(f"Error in application step {current_step}: {e}")
                break

        return False

    def _fill_application_form(self, application_data: Dict[str, Any]):
        # Fill common form fields
        fields_mapping = {
            "phone": ["phone", "phoneNumber", "mobile"],
            "email": ["email", "emailAddress"],
            "first_name": ["firstName", "fname", "first_name"],
            "last_name": ["lastName", "lname", "last_name"],
        }

        for data_key, field_names in fields_mapping.items():
            if data_key in application_data:
                for field_name in field_names:
                    field = self.safe_find_element(By.NAME, field_name)
                    if field:
                        field.clear()
                        field.send_keys(application_data[data_key])
                        break

        # Handle file uploads
        if "resume_path" in application_data:
            file_input = self.safe_find_element(By.CSS_SELECTOR, "input[type='file']")
            if file_input:
                file_input.send_keys(application_data["resume_path"])

    def _parse_posted_date(self, date_text: str) -> datetime:
        now = datetime.now()
        
        if "minute" in date_text:
            minutes = int(re.search(r'\d+', date_text).group())
            return now - timedelta(minutes=minutes)
        elif "hour" in date_text:
            hours = int(re.search(r'\d+', date_text).group())
            return now - timedelta(hours=hours)
        elif "day" in date_text:
            days = int(re.search(r'\d+', date_text).group())
            return now - timedelta(days=days)
        elif "week" in date_text:
            weeks = int(re.search(r'\d+', date_text).group())
            return now - timedelta(weeks=weeks)
        else:
            return now

    def _parse_salary(self, salary_text: str) -> tuple:
        if not salary_text:
            return None, None
            
        # Extract numbers from salary text
        numbers = re.findall(r'[\d,]+', salary_text.replace(',', ''))
        if len(numbers) >= 2:
            return int(numbers[0]), int(numbers[1])
        elif len(numbers) == 1:
            salary = int(numbers[0])
            return salary, salary
        else:
            return None, None

    def _extract_job_id_from_url(self, url: str) -> str:
        match = re.search(r'jobs/view/(\d+)', url)
        return match.group(1) if match else url.split('/')[-1]