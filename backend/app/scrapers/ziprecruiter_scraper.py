from typing import List, Dict, Any
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from .base_scraper import BaseScraper
from app.models.job import JobPlatform
import re
from datetime import datetime, timedelta
from urllib.parse import urlencode

class ZipRecruiterScraper(BaseScraper):
    def __init__(self, headless: bool = True):
        super().__init__(JobPlatform.ZIPRECRUITER, headless)
        self.base_url = "https://www.ziprecruiter.com"

    def login(self, username: str, password: str) -> bool:
        try:
            self.driver.get(f"{self.base_url}/login")
            self.random_delay()

            # Enter email
            email_field = self.safe_find_element(By.CSS_SELECTOR, "input[type='email']")
            if not email_field:
                email_field = self.safe_find_element(By.NAME, "email")
            if not email_field:
                return False
            email_field.send_keys(username)

            # Enter password
            password_field = self.safe_find_element(By.CSS_SELECTOR, "input[type='password']")
            if not password_field:
                password_field = self.safe_find_element(By.NAME, "password")
            if not password_field:
                return False
            password_field.send_keys(password)

            # Click login button
            login_button = self.safe_find_element(By.CSS_SELECTOR, "button[type='submit']")
            if login_button:
                login_button.click()
                self.random_delay()

            # Check if login was successful
            return "dashboard" in self.driver.current_url or "jobs" in self.driver.current_url

        except Exception as e:
            print(f"ZipRecruiter login failed: {e}")
            return False

    def search_jobs(self, keywords: List[str], location: str, **kwargs) -> List[Dict[str, Any]]:
        jobs = []
        try:
            # Build search parameters
            params = {
                'search': ' OR '.join(keywords),
                'location': location,
                'days': '1',  # Last 24 hours
                'radius': '25'
            }

            if kwargs.get("remote_only"):
                params['refine_by_location_type'] = 'remote'

            if kwargs.get("salary_min"):
                params['refine_by_salary'] = f"{kwargs['salary_min']}+"

            # Build URL
            search_url = f"{self.base_url}/jobs?" + urlencode(params)
            self.driver.get(search_url)
            self.random_delay()

            # Get job cards
            job_cards = self.driver.find_elements(By.CSS_SELECTOR, ".job_content")
            
            for card in job_cards[:20]:  # Limit to first 20 jobs
                try:
                    job_data = self._extract_job_from_card(card)
                    if job_data:
                        jobs.append(job_data)
                except Exception as e:
                    print(f"Error extracting job from card: {e}")
                    continue

        except Exception as e:
            print(f"ZipRecruiter job search failed: {e}")

        return jobs

    def _extract_job_from_card(self, card) -> Dict[str, Any]:
        try:
            # Job title and link
            title_element = card.find_element(By.CSS_SELECTOR, ".job_link")
            title = self.safe_get_text(title_element)
            job_url = self.safe_get_attribute(title_element, "href")
            
            # Make URL absolute
            if job_url.startswith('/'):
                job_url = self.base_url + job_url

            # Company
            company_element = card.find_element(By.CSS_SELECTOR, ".company_name")
            company = self.safe_get_text(company_element)

            # Location
            location_element = card.find_element(By.CSS_SELECTOR, ".location")
            location = self.safe_get_text(location_element)

            # Salary (if available)
            salary_element = card.find_element(By.CSS_SELECTOR, ".salary")
            salary_text = self.safe_get_text(salary_element)
            salary_min, salary_max = self._parse_salary(salary_text)

            # Posted date
            date_element = card.find_element(By.CSS_SELECTOR, ".time")
            posted_date = self._parse_posted_date(self.safe_get_text(date_element))

            # Extract platform ID from URL
            platform_id = self._extract_job_id_from_url(job_url)

            # Job description snippet
            description_element = card.find_element(By.CSS_SELECTOR, ".job_snippet")
            description_snippet = self.safe_get_text(description_element)

            return {
                "title": title,
                "company": company,
                "location": location,
                "application_url": job_url,
                "platform": JobPlatform.ZIPRECRUITER,
                "platform_id": platform_id,
                "posted_date": posted_date,
                "salary_min": salary_min,
                "salary_max": salary_max,
                "description": description_snippet,  # Initial snippet
                "is_remote": "remote" in location.lower(),
                "is_hybrid": "hybrid" in location.lower(),
            }

        except NoSuchElementException:
            return None

    def get_job_details(self, job_url: str) -> Dict[str, Any]:
        try:
            self.driver.get(job_url)
            self.random_delay()

            # Full job description
            description_element = self.safe_find_element(By.CSS_SELECTOR, ".jobDescriptionSection")
            if not description_element:
                description_element = self.safe_find_element(By.CSS_SELECTOR, ".job_description")
            description = self.safe_get_text(description_element)

            # Company name (more detailed)
            company_element = self.safe_find_element(By.CSS_SELECTOR, ".hiring_company_text")
            company = self.safe_get_text(company_element)

            # Job type/schedule
            job_type_element = self.safe_find_element(By.CSS_SELECTOR, ".job_type")
            job_type = self.safe_get_text(job_type_element)

            # Benefits (if available)
            benefits_element = self.safe_find_element(By.CSS_SELECTOR, ".benefits")
            benefits = self.safe_get_text(benefits_element)

            return {
                "description": description,
                "company": company,
                "job_type": job_type,
                "benefits": benefits,
            }

        except Exception as e:
            print(f"Error getting ZipRecruiter job details: {e}")
            return {}

    def apply_to_job(self, job_url: str, application_data: Dict[str, Any]) -> bool:
        try:
            self.driver.get(job_url)
            self.random_delay()

            # Look for apply button
            apply_button = self.safe_find_element(By.CSS_SELECTOR, ".apply_button")
            if not apply_button:
                apply_button = self.safe_find_element(By.CSS_SELECTOR, "button[data-action='apply']")
            
            if not apply_button:
                return False

            apply_button.click()
            self.random_delay()

            # Handle ZipRecruiter application form
            return self._handle_application_form(application_data)

        except Exception as e:
            print(f"ZipRecruiter application failed: {e}")
            return False

    def _handle_application_form(self, application_data: Dict[str, Any]) -> bool:
        try:
            # ZipRecruiter often has a multi-step application process
            
            # Step 1: Basic information
            fields_mapping = {
                "phone": ["phone", "phoneNumber"],
                "email": ["email"],
                "first_name": ["firstName", "fname"],
                "last_name": ["lastName", "lname"],
                "city": ["city"],
                "state": ["state"],
                "zip_code": ["zipCode", "zip"]
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
                    self.random_delay()

            # Look for continue button
            continue_button = self.safe_find_element(By.CSS_SELECTOR, ".continue_button")
            if not continue_button:
                continue_button = self.safe_find_element(By.CSS_SELECTOR, "button[type='submit']")
            
            if continue_button:
                continue_button.click()
                self.random_delay()

                # Step 2: Additional questions (if any)
                return self._handle_additional_questions(application_data)

            return False

        except Exception as e:
            print(f"Error in ZipRecruiter application form: {e}")
            return False

    def _handle_additional_questions(self, application_data: Dict[str, Any]) -> bool:
        try:
            # Check for additional questions page
            questions_container = self.safe_find_element(By.CSS_SELECTOR, ".questions_container")
            if questions_container:
                # Handle common screening questions
                self._answer_screening_questions(application_data)

            # Final submit
            submit_button = self.safe_find_element(By.CSS_SELECTOR, ".submit_application")
            if not submit_button:
                submit_button = self.safe_find_element(By.CSS_SELECTOR, "button[type='submit']")
            
            if submit_button:
                submit_button.click()
                self.random_delay()
                return True

            return False

        except Exception as e:
            print(f"Error handling additional questions: {e}")
            return False

    def _answer_screening_questions(self, application_data: Dict[str, Any]):
        # Handle common screening questions
        common_questions = {
            "work authorization": application_data.get("work_authorization", "Yes"),
            "willing to relocate": application_data.get("willing_to_relocate", "No"),
            "salary expectation": application_data.get("salary_expectation", ""),
            "years of experience": application_data.get("years_experience", "5+"),
            "available start date": application_data.get("start_date", "Immediately")
        }

        # Find and answer questions
        question_elements = self.driver.find_elements(By.CSS_SELECTOR, ".question")
        for question in question_elements:
            question_text = self.safe_get_text(question).lower()
            
            for key, answer in common_questions.items():
                if key in question_text:
                    # Try to find input field
                    input_field = question.find_element(By.CSS_SELECTOR, "input, select, textarea")
                    if input_field:
                        if input_field.tag_name == "select":
                            # Handle dropdown
                            from selenium.webdriver.support.ui import Select
                            select = Select(input_field)
                            try:
                                select.select_by_visible_text(answer)
                            except:
                                select.select_by_index(1)  # Default to first option
                        else:
                            # Handle text input
                            input_field.clear()
                            input_field.send_keys(answer)
                    break

    def _parse_posted_date(self, date_text: str) -> datetime:
        now = datetime.now()
        
        if "just posted" in date_text.lower() or "today" in date_text.lower():
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
        if not salary_text or salary_text.lower() == "competitive":
            return None, None
            
        # Clean up salary text
        salary_text = salary_text.replace('$', '').replace(',', '').replace('/year', '').replace('annually', '')
        
        # Look for range (e.g., "50000 - 70000")
        range_match = re.search(r'(\d+)\s*-\s*(\d+)', salary_text)
        if range_match:
            return int(range_match.group(1)), int(range_match.group(2))
        
        # Look for "up to" format
        up_to_match = re.search(r'up to (\d+)', salary_text)
        if up_to_match:
            max_salary = int(up_to_match.group(1))
            return None, max_salary
        
        # Look for single number
        single_match = re.search(r'\d+', salary_text)
        if single_match:
            salary = int(single_match.group())
            return salary, salary
        
        return None, None

    def _extract_job_id_from_url(self, url: str) -> str:
        match = re.search(r'/jobs/([a-zA-Z0-9\-]+)', url)
        if match:
            return match.group(1)
        
        # Fallback to last segment
        return url.split('/')[-1]