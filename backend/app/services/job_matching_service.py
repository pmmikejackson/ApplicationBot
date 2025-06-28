from typing import Dict, List, Any, Optional
from sqlalchemy.orm import Session
from app.models.job import Job, JobPriority
from app.services.job_service import JobService
import re
import openai
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

class JobMatchingService:
    def __init__(self, db: Session):
        self.db = db
        self.job_service = JobService(db)
        if settings.OPENAI_API_KEY:
            openai.api_key = settings.OPENAI_API_KEY

    def calculate_job_fit_score(self, job: Job, user_profile: Dict[str, Any]) -> float:
        """Calculate a fit score (0-10) for a job based on user profile"""
        
        score_components = {
            "title_match": self._calculate_title_match(job.title, user_profile.get("target_titles", [])),
            "experience_match": self._calculate_experience_match(job.description, user_profile.get("years_experience", 0)),
            "skills_match": self._calculate_skills_match(job.description, user_profile.get("skills", [])),
            "location_match": self._calculate_location_match(job, user_profile.get("location_preferences", {})),
            "salary_match": self._calculate_salary_match(job, user_profile.get("salary_expectations", {})),
            "remote_match": self._calculate_remote_match(job, user_profile.get("remote_preference", False)),
            "company_size_match": self._calculate_company_size_match(job.description, user_profile.get("company_size_preference"))
        }

        # Weighted average of score components
        weights = {
            "title_match": 0.25,
            "experience_match": 0.20,
            "skills_match": 0.20,
            "location_match": 0.15,
            "salary_match": 0.10,
            "remote_match": 0.05,
            "company_size_match": 0.05
        }

        total_score = sum(score_components[component] * weights[component] 
                         for component in score_components)

        return min(10.0, max(0.0, total_score))

    def _calculate_title_match(self, job_title: str, target_titles: List[str]) -> float:
        """Score based on how well the job title matches target titles"""
        if not target_titles:
            return 5.0  # Neutral score if no preferences specified

        job_title_lower = job_title.lower()
        
        # Exact matches get highest score
        for target in target_titles:
            if target.lower() in job_title_lower:
                return 10.0

        # Partial matches based on keywords
        title_keywords = {
            "director": ["director", "head", "vp", "vice president"],
            "senior": ["senior", "sr", "lead", "principal"],
            "product": ["product", "pm"],
            "manager": ["manager", "mgr"],
            "management": ["management", "mgmt"]
        }

        score = 0.0
        for target in target_titles:
            target_lower = target.lower()
            for keyword_category, keywords in title_keywords.items():
                if any(kw in target_lower for kw in keywords):
                    if any(kw in job_title_lower for kw in keywords):
                        score += 2.0

        return min(10.0, score)

    def _calculate_experience_match(self, job_description: str, user_experience: int) -> float:
        """Score based on experience requirements vs user experience"""
        if not job_description:
            return 7.0  # Neutral score if no description

        # Extract experience requirements from job description
        experience_patterns = [
            r'(\d+)\+?\s*years?\s*(?:of\s*)?experience',
            r'(\d+)\+?\s*years?\s*(?:of\s*)?(?:relevant\s*)?experience',
            r'minimum\s*(?:of\s*)?(\d+)\s*years?',
            r'at least\s*(\d+)\s*years?'
        ]

        required_experience = None
        for pattern in experience_patterns:
            match = re.search(pattern, job_description.lower())
            if match:
                required_experience = int(match.group(1))
                break

        if required_experience is None:
            return 7.0  # Neutral if can't determine requirement

        # Score based on how user experience compares to requirement
        if user_experience >= required_experience:
            # User meets or exceeds requirement
            if user_experience <= required_experience + 2:
                return 10.0  # Perfect match
            else:
                return max(7.0, 10.0 - (user_experience - required_experience) * 0.5)  # Slightly overqualified
        else:
            # User has less experience than required
            gap = required_experience - user_experience
            if gap <= 1:
                return 8.0  # Close enough
            elif gap <= 2:
                return 6.0  # Stretch opportunity
            else:
                return max(2.0, 6.0 - gap)  # Significant gap

    def _calculate_skills_match(self, job_description: str, user_skills: List[str]) -> float:
        """Score based on skill overlap between job and user"""
        if not job_description or not user_skills:
            return 5.0

        job_desc_lower = job_description.lower()
        matched_skills = 0
        total_user_skills = len(user_skills)

        for skill in user_skills:
            if skill.lower() in job_desc_lower:
                matched_skills += 1

        if total_user_skills == 0:
            return 5.0

        match_percentage = matched_skills / total_user_skills
        return match_percentage * 10.0

    def _calculate_location_match(self, job: Job, location_preferences: Dict[str, Any]) -> float:
        """Score based on location preferences"""
        if not location_preferences:
            return 7.0

        # Remote work preference
        if location_preferences.get("remote_only", False):
            if job.is_remote:
                return 10.0
            elif job.is_hybrid:
                return 7.0
            else:
                return 2.0

        # Hybrid preference
        if location_preferences.get("hybrid_preferred", False):
            if job.is_hybrid:
                return 10.0
            elif job.is_remote:
                return 8.0
            else:
                return 5.0

        # Specific location preferences
        preferred_locations = location_preferences.get("cities", [])
        if preferred_locations and job.location:
            job_location_lower = job.location.lower()
            for city in preferred_locations:
                if city.lower() in job_location_lower:
                    return 9.0

        return 5.0  # Neutral if no strong preference match

    def _calculate_salary_match(self, job: Job, salary_expectations: Dict[str, Any]) -> float:
        """Score based on salary expectations"""
        if not salary_expectations or (not job.salary_min and not job.salary_max):
            return 7.0

        min_expected = salary_expectations.get("min", 0)
        max_expected = salary_expectations.get("max", float('inf'))

        # Use job's salary range or single value
        job_min = job.salary_min or job.salary_max or 0
        job_max = job.salary_max or job.salary_min or 0

        if job_min >= min_expected and job_max <= max_expected:
            return 10.0  # Within expected range
        elif job_max >= min_expected:
            return 8.0  # Partially meets expectations
        elif job_min > 0 and job_min < min_expected:
            # Below expectations
            gap_percentage = (min_expected - job_min) / min_expected
            return max(3.0, 7.0 - gap_percentage * 5.0)
        else:
            return 7.0  # Unknown salary

    def _calculate_remote_match(self, job: Job, remote_preference: bool) -> float:
        """Score based on remote work preference"""
        if remote_preference:
            if job.is_remote:
                return 10.0
            elif job.is_hybrid:
                return 7.0
            else:
                return 3.0
        else:
            # Prefer in-office
            if not job.is_remote and not job.is_hybrid:
                return 10.0
            elif job.is_hybrid:
                return 7.0
            else:
                return 5.0

    def _calculate_company_size_match(self, job_description: str, size_preference: Optional[str]) -> float:
        """Score based on company size preference"""
        if not size_preference or not job_description:
            return 7.0

        job_desc_lower = job_description.lower()
        
        size_indicators = {
            "startup": ["startup", "early stage", "series a", "series b", "founding team"],
            "small": ["small company", "50-100", "under 100"],
            "medium": ["mid-size", "growing company", "100-500", "scale-up"],
            "large": ["fortune 500", "enterprise", "1000+", "multinational", "global company"],
            "enterprise": ["enterprise", "fortune 100", "5000+", "multinational corporation"]
        }

        if size_preference in size_indicators:
            indicators = size_indicators[size_preference]
            for indicator in indicators:
                if indicator in job_desc_lower:
                    return 9.0

        return 5.0  # Neutral if can't determine

    def determine_job_priority(self, job: Job, fit_score: float) -> JobPriority:
        """Determine job priority based on fit score and other factors"""
        
        # High priority criteria
        if fit_score >= 8.5:
            return JobPriority.MUST_APPLY
        elif fit_score >= 7.0:
            return JobPriority.GOOD_FIT
        elif fit_score >= 5.0:
            return JobPriority.STRETCH
        else:
            return JobPriority.LOW_PRIORITY

    def analyze_job_with_ai(self, job: Job, user_profile: Dict[str, Any]) -> Dict[str, Any]:
        """Use AI to provide detailed job analysis"""
        if not settings.OPENAI_API_KEY:
            return {"error": "OpenAI API key not configured"}

        try:
            prompt = self._create_analysis_prompt(job, user_profile)
            
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a career advisor helping evaluate job opportunities for a product management professional."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=500,
                temperature=0.3
            )

            analysis = response.choices[0].message.content
            return {"analysis": analysis}

        except Exception as e:
            logger.error(f"AI analysis failed: {e}")
            return {"error": "AI analysis failed"}

    def _create_analysis_prompt(self, job: Job, user_profile: Dict[str, Any]) -> str:
        """Create prompt for AI job analysis"""
        return f"""
        Please analyze this job opportunity for a product management professional:

        Job Title: {job.title}
        Company: {job.company}
        Location: {job.location}
        Salary: ${job.salary_min}-${job.salary_max if job.salary_max != job.salary_min else 'Not specified'}
        Remote: {'Yes' if job.is_remote else 'Hybrid' if job.is_hybrid else 'No'}

        Job Description (excerpt): {job.description[:1000] if job.description else 'Not available'}

        Candidate Profile:
        - Target Roles: {', '.join(user_profile.get('target_titles', []))}
        - Experience: {user_profile.get('years_experience', 'Not specified')} years
        - Key Skills: {', '.join(user_profile.get('skills', []))}
        - Salary Range: ${user_profile.get('salary_expectations', {}).get('min', 'Not specified')}-${user_profile.get('salary_expectations', {}).get('max', 'Not specified')}

        Please provide:
        1. How well this role matches the candidate's profile (1-10 scale)
        2. Key strengths of this opportunity
        3. Potential concerns or gaps
        4. Whether to apply (Must Apply/Good Fit/Stretch/Pass)
        5. Brief reasoning

        Keep response concise and actionable.
        """

    def update_all_job_scores(self, user_profile: Dict[str, Any]) -> Dict[str, Any]:
        """Update fit scores for all jobs in the database"""
        jobs = self.db.query(Job).all()
        updated_count = 0
        priority_changes = {"must_apply": 0, "good_fit": 0, "stretch": 0, "low_priority": 0}

        for job in jobs:
            # Calculate new fit score
            new_score = self.calculate_job_fit_score(job, user_profile)
            new_priority = self.determine_job_priority(job, new_score)

            # Update job
            job.fit_score = new_score
            old_priority = job.priority
            job.priority = new_priority

            # Track priority changes
            if old_priority != new_priority:
                priority_changes[new_priority.value] += 1

            updated_count += 1

        self.db.commit()

        return {
            "updated_jobs": updated_count,
            "priority_distribution": priority_changes,
            "message": f"Updated fit scores for {updated_count} jobs"
        }