from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from app.models.job import Job, JobPlatform
from app.services.job_service import JobService
from app.scrapers import LinkedInScraper, IndeedScraper, BuiltInScraper, ZipRecruiterScraper
from app.core.config import settings
import asyncio
from concurrent.futures import ThreadPoolExecutor
import logging

logger = logging.getLogger(__name__)

class ScraperService:
    def __init__(self, db: Session):
        self.db = db
        self.job_service = JobService(db)
        self.scrapers = {
            JobPlatform.LINKEDIN: LinkedInScraper,
            JobPlatform.INDEED: IndeedScraper,
            JobPlatform.BUILTIN: BuiltInScraper,
            JobPlatform.ZIPRECRUITER: ZipRecruiterScraper,
        }

    async def scrape_all_platforms(
        self,
        keywords: List[str],
        location: str,
        platforms: Optional[List[JobPlatform]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Scrape jobs from all specified platforms concurrently"""
        
        if platforms is None:
            platforms = list(self.scrapers.keys())

        results = {
            "total_jobs_found": 0,
            "total_jobs_saved": 0,
            "platform_results": {},
            "errors": []
        }

        # Create executor for concurrent scraping
        with ThreadPoolExecutor(max_workers=settings.MAX_CONCURRENT_SCRAPERS) as executor:
            # Submit scraping tasks
            future_to_platform = {
                executor.submit(
                    self._scrape_platform,
                    platform,
                    keywords,
                    location,
                    **kwargs
                ): platform for platform in platforms
            }

            # Collect results
            for future in future_to_platform:
                platform = future_to_platform[future]
                try:
                    platform_result = future.result()
                    results["platform_results"][platform.value] = platform_result
                    results["total_jobs_found"] += platform_result["jobs_found"]
                    results["total_jobs_saved"] += platform_result["jobs_saved"]
                except Exception as e:
                    error_msg = f"Error scraping {platform.value}: {str(e)}"
                    logger.error(error_msg)
                    results["errors"].append(error_msg)
                    results["platform_results"][platform.value] = {
                        "jobs_found": 0,
                        "jobs_saved": 0,
                        "error": str(e)
                    }

        return results

    def _scrape_platform(
        self,
        platform: JobPlatform,
        keywords: List[str],
        location: str,
        **kwargs
    ) -> Dict[str, Any]:
        """Scrape jobs from a single platform"""
        
        scraper_class = self.scrapers[platform]
        jobs_found = 0
        jobs_saved = 0

        try:
            with scraper_class(headless=True) as scraper:
                # Login if credentials are provided
                username, password = self._get_platform_credentials(platform)
                if username and password:
                    login_success = scraper.login(username, password)
                    if not login_success:
                        logger.warning(f"Failed to login to {platform.value}")

                # Search for jobs
                jobs = scraper.search_jobs(keywords, location, **kwargs)
                jobs_found = len(jobs)

                # Process and save jobs
                for job_data in jobs:
                    try:
                        # Check for duplicates
                        existing_job = self.job_service.find_duplicate_jobs(
                            job_data["title"],
                            job_data["company"],
                            job_data["platform_id"]
                        )

                        if not existing_job:
                            # Get detailed job information
                            detailed_job = scraper.get_job_details(job_data["application_url"])
                            job_data.update(detailed_job)

                            # Save to database
                            self.job_service.create_job(job_data)
                            jobs_saved += 1
                        else:
                            logger.info(f"Duplicate job found: {job_data['title']} at {job_data['company']}")

                    except Exception as e:
                        logger.error(f"Error processing job: {e}")
                        continue

        except Exception as e:
            logger.error(f"Error scraping {platform.value}: {e}")
            raise

        return {
            "jobs_found": jobs_found,
            "jobs_saved": jobs_saved,
            "platform": platform.value
        }

    def _get_platform_credentials(self, platform: JobPlatform) -> tuple:
        """Get credentials for the specified platform"""
        credential_map = {
            JobPlatform.LINKEDIN: (settings.LINKEDIN_USERNAME, settings.LINKEDIN_PASSWORD),
            JobPlatform.INDEED: (settings.INDEED_USERNAME, settings.INDEED_PASSWORD),
            # BuiltIn and ZipRecruiter don't require login for basic scraping
        }
        return credential_map.get(platform, (None, None))

    def scrape_single_platform(
        self,
        platform: JobPlatform,
        keywords: List[str],
        location: str,
        **kwargs
    ) -> Dict[str, Any]:
        """Scrape jobs from a single platform (synchronous)"""
        return self._scrape_platform(platform, keywords, location, **kwargs)

    def get_scraping_status(self) -> Dict[str, Any]:
        """Get current scraping status and statistics"""
        
        # Get recent job statistics
        job_stats = self.job_service.get_job_statistics()
        
        # Calculate jobs discovered today
        from datetime import datetime, timedelta
        today = datetime.now().date()
        yesterday = today - timedelta(days=1)
        
        jobs_today = self.db.query(Job).filter(
            Job.discovered_at >= yesterday
        ).count()

        return {
            "total_jobs": job_stats["total_jobs"],
            "jobs_discovered_today": jobs_today,
            "platform_breakdown": job_stats["platform_breakdown"],
            "status_breakdown": job_stats["status_breakdown"],
            "last_updated": datetime.now().isoformat()
        }

    def test_platform_connection(self, platform: JobPlatform) -> Dict[str, Any]:
        """Test connection to a specific platform"""
        
        try:
            scraper_class = self.scrapers[platform]
            with scraper_class(headless=True) as scraper:
                # Try to access the platform
                scraper.driver.get(scraper.base_url)
                
                # Test login if credentials are available
                username, password = self._get_platform_credentials(platform)
                if username and password:
                    login_success = scraper.login(username, password)
                    return {
                        "platform": platform.value,
                        "status": "success" if login_success else "login_failed",
                        "message": "Login successful" if login_success else "Login failed"
                    }
                else:
                    return {
                        "platform": platform.value,
                        "status": "success",
                        "message": "Platform accessible (no login required)"
                    }

        except Exception as e:
            return {
                "platform": platform.value,
                "status": "error",
                "message": str(e)
            }