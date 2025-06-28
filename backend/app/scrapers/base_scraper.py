from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time
import random
from app.core.config import settings
from app.models.job import JobPlatform

class BaseScraper(ABC):
    def __init__(self, platform: JobPlatform, headless: bool = True):
        self.platform = platform
        self.headless = headless
        self.driver = None
        self.wait = None
        self.setup_driver()

    def setup_driver(self):
        chrome_options = Options()
        if self.headless:
            chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36")
        
        self.driver = webdriver.Chrome(options=chrome_options)
        self.wait = WebDriverWait(self.driver, 10)

    def random_delay(self):
        delay = random.uniform(settings.SCRAPING_DELAY_MIN, settings.SCRAPING_DELAY_MAX)
        time.sleep(delay)

    def safe_find_element(self, by: By, value: str, timeout: int = 10) -> Optional[Any]:
        try:
            element = WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((by, value))
            )
            return element
        except TimeoutException:
            return None

    def safe_get_text(self, element) -> str:
        try:
            return element.text.strip() if element else ""
        except:
            return ""

    def safe_get_attribute(self, element, attribute: str) -> str:
        try:
            return element.get_attribute(attribute) if element else ""
        except:
            return ""

    @abstractmethod
    def login(self, username: str, password: str) -> bool:
        pass

    @abstractmethod
    def search_jobs(self, keywords: List[str], location: str, **kwargs) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def get_job_details(self, job_url: str) -> Dict[str, Any]:
        pass

    @abstractmethod
    def apply_to_job(self, job_url: str, application_data: Dict[str, Any]) -> bool:
        pass

    def cleanup(self):
        if self.driver:
            self.driver.quit()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cleanup()