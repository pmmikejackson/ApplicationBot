from typing import List, Dict, Any
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from .base_scraper import BaseScraper
from app.models.job import JobPlatform
import re
from datetime import datetime, timedelta
from urllib.parse import urlencode

class IndeedScraper(BaseScraper):
    def __init__(self, headless: bool = True):
        super().__init__(JobPlatform.INDEED, headless)
        self.base_url = "https://www.indeed.com"

    def login(self, username: str, password: str) -> bool:
        try:
            self.driver.get(f"{self.base_url}/account/login")
            self.random_delay()

            # Enter email
            email_field = self.safe_find_element(By.ID, "ifl-InputFormField-3")
            if not email_field:
                email_field = self.safe_find_element(By.CSS_SELECTOR, "input[type='email']")
            if not email_field:
                return False
            email_field.send_keys(username)

            # Continue button
            continue_button = self.safe_find_element(By.CSS_SELECTOR, "button[type='submit']")
            if continue_button:
                continue_button.click()
                self.random_delay()

            # Enter password
            password_field = self.safe_find_element(By.ID, "ifl-InputFormField-7")
            if not password_field:
                password_field = self.safe_find_element(By.CSS_SELECTOR, "input[type='password']")
            if not password_field:
                return False
            password_field.send_keys(password)

            # Sign in button
            signin_button = self.safe_find_element(By.CSS_SELECTOR, "button[type='submit']")
            if signin_button:
                signin_button.click()
                self.random_delay()

            # Check if login was successful
            return "account" in self.driver.current_url or self.driver.current_url == f"{self.base_url}/"

        except Exception as e:
            print(f"Indeed login failed: {e}")
            return False

    def search_jobs(self, keywords: List[str], location: str, **kwargs) -> List[Dict[str, Any]]:
        jobs = []
        try:
            # Build search parameters
            params = {
                'q': ' OR '.join(keywords),
                'l': location,
                'fromage': '1',  # Last 24 hours
                'radius': '25',
                'sort': 'date'
            }

            if kwargs.get("remote_only"):
                params['remotejob'] = '032b3046-06a3-4876-8dfd-474eb5e7ed11'

            if kwargs.get("salary_min"):
                params['salary'] = f"${kwargs['salary_min']}%2B"

            # Build URL
            search_url = f"{self.base_url}/jobs?" + urlencode(params)
            self.driver.get(search_url)
            self.random_delay()

            # Get job cards
            job_cards = self.driver.find_elements(By.CSS_SELECTOR, ".job_seen_beacon")
            
            for card in job_cards[:20]:  # Limit to first 20 jobs
                try:
                    job_data = self._extract_job_from_card(card)
                    if job_data:
                        jobs.append(job_data)
                except Exception as e:
                    print(f"Error extracting job from card: {e}")
                    continue

        except Exception as e:
            print(f"Indeed job search failed: {e}")

        return jobs

    def _extract_job_from_card(self, card) -> Dict[str, Any]:
        try:
            # Job title and link
            title_element = card.find_element(By.CSS_SELECTOR, "h2.jobTitle a")
            title = self.safe_get_text(title_element)
            job_url = self.safe_get_attribute(title_element, "href")
            
            # Make URL absolute
            if job_url.startswith('/'):
                job_url = self.base_url + job_url

            # Company
            company_element = card.find_element(By.CSS_SELECTOR, ".companyName")
            company = self.safe_get_text(company_element)

            # Location
            location_element = card.find_element(By.CSS_SELECTOR, ".companyLocation")
            location = self.safe_get_text(location_element)

            # Salary (if available)
            salary_element = card.find_element(By.CSS_SELECTOR, ".salary-snippet")
            salary_text = self.safe_get_text(salary_element)
            salary_min, salary_max = self._parse_salary(salary_text)

            # Posted date
            date_element = card.find_element(By.CSS_SELECTOR, ".date")
            posted_date = self._parse_posted_date(self.safe_get_text(date_element))

            # Extract platform ID from URL
            platform_id = self._extract_job_id_from_url(job_url)

            return {
                "title": title,
                "company": company,
                "location": location,
                "application_url": job_url,
                "platform": JobPlatform.INDEED,
                "platform_id": platform_id,
                "posted_date": posted_date,
                "salary_min": salary_min,
                "salary_max": salary_max,
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
            description_element = self.safe_find_element(By.CSS_SELECTOR, ".jobsearch-jobDescriptionText")
            description = self.safe_get_text(description_element)

            # Additional job details
            details = {}
            
            # Try to get more salary info
            salary_element = self.safe_find_element(By.CSS_SELECTOR, ".icl-u-lg-mr--sm")
            if salary_element:
                salary_text = self.safe_get_text(salary_element)
                salary_min, salary_max = self._parse_salary(salary_text)
                details.update({
                    "salary_min": salary_min,
                    "salary_max": salary_max,
                })

            # Job type
            job_type_element = self.safe_find_element(By.CSS_SELECTOR, ".jobsearch-jobMetadataHeader-iconLabel")
            if job_type_element:
                job_type = self.safe_get_text(job_type_element)
                details["job_type"] = job_type

            details["description"] = description
            return details

        except Exception as e:
            print(f"Error getting Indeed job details: {e}")
            return {}

    def apply_to_job(self, job_url: str, application_data: Dict[str, Any]) -> bool:
        try:
            self.driver.get(job_url)
            self.random_delay()

            # Look for apply button
            apply_button = self.safe_find_element(By.CSS_SELECTOR, ".ia-IndeedApplyButton")
            if not apply_button:
                apply_button = self.safe_find_element(By.CSS_SELECTOR, "button[data-jk]")
            
            if not apply_button:
                return False

            apply_button.click()
            self.random_delay()

            # Handle Indeed application form
            return self._handle_application_form(application_data)

        except Exception as e:
            print(f"Indeed application failed: {e}")
            return False

    def _handle_application_form(self, application_data: Dict[str, Any]) -> bool:
        try:
            # Fill personal information
            fields_mapping = {
                "phone": ["phone", "phoneNumber"],
                "email": ["email", "emailAddress"],
                "first_name": ["firstName", "fname"],
                "last_name": ["lastName", "lname"],
            }

            for data_key, field_names in fields_mapping.items():
                if data_key in application_data:
                    for field_name in field_names:
                        field = self.safe_find_element(By.NAME, field_name)
                        if field:
                            field.clear()
                            field.send_keys(application_data[data_key])
                            break

            # Handle resume upload
            if "resume_path" in application_data:
                file_input = self.safe_find_element(By.CSS_SELECTOR, "input[type='file']")
                if file_input:
                    file_input.send_keys(application_data["resume_path"])

            # Submit application
            submit_button = self.safe_find_element(By.CSS_SELECTOR, "button[type='submit']")
            if not submit_button:
                submit_button = self.safe_find_element(By.CSS_SELECTOR, ".ia-continueButton")
            
            if submit_button:
                submit_button.click()
                self.random_delay()
                return True

            return False

        except Exception as e:
            print(f"Error in Indeed application form: {e}")
            return False

    def _parse_posted_date(self, date_text: str) -> datetime:
        now = datetime.now()
        
        if "Just posted" in date_text:
            return now
        elif "minute" in date_text:
            minutes = int(re.search(r'\d+', date_text).group())
            return now - timedelta(minutes=minutes)
        elif "hour" in date_text:
            hours = int(re.search(r'\d+', date_text).group())
            return now - timedelta(hours=hours)
        elif "day" in date_text:
            days = int(re.search(r'\d+', date_text).group())
            return now - timedelta(days=days)
        else:
            return now

    def _parse_salary(self, salary_text: str) -> tuple:
        if not salary_text:
            return None, None
            
        # Remove common prefixes/suffixes
        salary_text = salary_text.replace('$', '').replace(',', '').replace('a year', '').replace('an hour', '')
        
        # Look for range (e.g., "50000 - 70000")
        range_match = re.search(r'(\d+)\s*-\s*(\d+)', salary_text)
        if range_match:
            return int(range_match.group(1)), int(range_match.group(2))
        
        # Look for single number
        single_match = re.search(r'\d+', salary_text)
        if single_match:
            salary = int(single_match.group())
            return salary, salary
        
        return None, None

    def _extract_job_id_from_url(self, url: str) -> str:
        match = re.search(r'jk=([a-zA-Z0-9]+)', url)
        if match:
            return match.group(1)
        match = re.search(r'viewjob\?jk=([a-zA-Z0-9]+)', url)
        return match.group(1) if match else url.split('/')[-1]