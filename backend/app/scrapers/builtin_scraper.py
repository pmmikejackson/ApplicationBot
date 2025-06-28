from typing import List, Dict, Any
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from .base_scraper import BaseScraper
from app.models.job import JobPlatform
import re
from datetime import datetime, timedelta
from urllib.parse import urlencode

class BuiltInScraper(BaseScraper):
    def __init__(self, headless: bool = True):
        super().__init__(JobPlatform.BUILTIN, headless)
        self.base_url = "https://builtin.com"

    def login(self, username: str, password: str) -> bool:
        try:
            self.driver.get(f"{self.base_url}/login")
            self.random_delay()

            # Enter email
            email_field = self.safe_find_element(By.CSS_SELECTOR, "input[type='email']")
            if not email_field:
                return False
            email_field.send_keys(username)

            # Enter password
            password_field = self.safe_find_element(By.CSS_SELECTOR, "input[type='password']")
            if not password_field:
                return False
            password_field.send_keys(password)

            # Click login button
            login_button = self.safe_find_element(By.CSS_SELECTOR, "button[type='submit']")
            if login_button:
                login_button.click()
                self.random_delay()

            # Check if login was successful
            return "dashboard" in self.driver.current_url or self.driver.current_url == f"{self.base_url}/"

        except Exception as e:
            print(f"BuiltIn login failed: {e}")
            return False

    def search_jobs(self, keywords: List[str], location: str, **kwargs) -> List[Dict[str, Any]]:
        jobs = []
        try:
            # BuiltIn has different regional sites
            locations_map = {
                "remote": "remote",
                "san francisco": "san-francisco",
                "new york": "new-york",
                "chicago": "chicago",
                "boston": "boston",
                "los angeles": "los-angeles",
                "austin": "austin",
                "seattle": "seattle",
                "denver": "denver"
            }

            location_slug = locations_map.get(location.lower(), "remote")
            
            # Build search URL for each keyword
            for keyword in keywords:
                search_url = f"{self.base_url}/{location_slug}/jobs?f%5B%5D=job-category-product&q={keyword.replace(' ', '%20')}"
                
                self.driver.get(search_url)
                self.random_delay()

                # Get job cards
                job_cards = self.driver.find_elements(By.CSS_SELECTOR, ".job-item")
                
                for card in job_cards[:10]:  # Limit per keyword
                    try:
                        job_data = self._extract_job_from_card(card)
                        if job_data:
                            jobs.append(job_data)
                    except Exception as e:
                        print(f"Error extracting job from card: {e}")
                        continue

        except Exception as e:
            print(f"BuiltIn job search failed: {e}")

        return jobs

    def _extract_job_from_card(self, card) -> Dict[str, Any]:
        try:
            # Job title and link
            title_element = card.find_element(By.CSS_SELECTOR, ".job-title a")
            title = self.safe_get_text(title_element)
            job_url = self.safe_get_attribute(title_element, "href")
            
            # Make URL absolute
            if job_url.startswith('/'):
                job_url = self.base_url + job_url

            # Company
            company_element = card.find_element(By.CSS_SELECTOR, ".company-name")
            company = self.safe_get_text(company_element)

            # Location
            location_element = card.find_element(By.CSS_SELECTOR, ".job-location")
            location = self.safe_get_text(location_element)

            # Salary (if available)
            salary_element = card.find_element(By.CSS_SELECTOR, ".salary")
            salary_text = self.safe_get_text(salary_element)
            salary_min, salary_max = self._parse_salary(salary_text)

            # Posted date
            date_element = card.find_element(By.CSS_SELECTOR, ".job-date")
            posted_date = self._parse_posted_date(self.safe_get_text(date_element))

            # Extract platform ID from URL
            platform_id = self._extract_job_id_from_url(job_url)

            return {
                "title": title,
                "company": company,
                "location": location,
                "application_url": job_url,
                "platform": JobPlatform.BUILTIN,
                "platform_id": platform_id,
                "posted_date": posted_date,
                "salary_min": salary_min,
                "salary_max": salary_max,
                "is_remote": "remote" in location.lower() or "anywhere" in location.lower(),
                "is_hybrid": "hybrid" in location.lower(),
            }

        except NoSuchElementException:
            return None

    def get_job_details(self, job_url: str) -> Dict[str, Any]:
        try:
            self.driver.get(job_url)
            self.random_delay()

            # Job description
            description_element = self.safe_find_element(By.CSS_SELECTOR, ".job-description")
            description = self.safe_get_text(description_element)

            # Company info
            company_element = self.safe_find_element(By.CSS_SELECTOR, ".company-header h1")
            company = self.safe_get_text(company_element)

            # Job requirements (often in a separate section)
            requirements_element = self.safe_find_element(By.CSS_SELECTOR, ".job-requirements")
            requirements = self.safe_get_text(requirements_element)

            return {
                "description": description,
                "requirements": requirements,
                "company": company,
            }

        except Exception as e:
            print(f"Error getting BuiltIn job details: {e}")
            return {}

    def apply_to_job(self, job_url: str, application_data: Dict[str, Any]) -> bool:
        try:
            self.driver.get(job_url)
            self.random_delay()

            # Look for apply button
            apply_button = self.safe_find_element(By.CSS_SELECTOR, ".apply-button")
            if not apply_button:
                apply_button = self.safe_find_element(By.CSS_SELECTOR, "a[href*='apply']")
            
            if not apply_button:
                return False

            # Check if it's an external application
            apply_url = self.safe_get_attribute(apply_button, "href")
            if "builtin.com" not in apply_url:
                # External application - open in new tab and return False
                # (indicating manual application needed)
                return False

            apply_button.click()
            self.random_delay()

            # Handle BuiltIn application form (similar to other platforms)
            return self._handle_application_form(application_data)

        except Exception as e:
            print(f"BuiltIn application failed: {e}")
            return False

    def _handle_application_form(self, application_data: Dict[str, Any]) -> bool:
        try:
            # Fill standard fields
            fields_mapping = {
                "phone": ["phone", "phoneNumber"],
                "email": ["email"],
                "first_name": ["firstName", "first_name"],
                "last_name": ["lastName", "last_name"],
                "linkedin_url": ["linkedin", "linkedinUrl"],
                "portfolio_url": ["portfolio", "portfolioUrl", "website"]
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
            if submit_button:
                submit_button.click()
                self.random_delay()
                return True

            return False

        except Exception as e:
            print(f"Error in BuiltIn application form: {e}")
            return False

    def _parse_posted_date(self, date_text: str) -> datetime:
        now = datetime.now()
        
        if "today" in date_text.lower():
            return now
        elif "yesterday" in date_text.lower():
            return now - timedelta(days=1)
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
            
        # Remove common text and clean up
        salary_text = salary_text.replace('$', '').replace(',', '').replace('K', '000')
        
        # Look for range (e.g., "80K - 120K", "80000-120000")
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
        # BuiltIn URLs typically have format: /company/job-title/job-id
        match = re.search(r'/jobs/(\d+)', url)
        if match:
            return match.group(1)
        
        # Fallback to last segment of URL
        return url.split('/')[-1]