from typing import Dict, Any, List, Optional
import os
import json
import re
from datetime import datetime
from jinja2 import Template, Environment, FileSystemLoader
from docx import Document
from docx.shared import Inches
import openai
from app.core.config import settings
from app.models.job import Job
import logging

logger = logging.getLogger(__name__)

class DocumentCustomizationService:
    def __init__(self):
        self.templates_dir = "documents/templates"
        self.output_dir = "documents/generated"
        self.ensure_directories()
        
        if settings.OPENAI_API_KEY:
            openai.api_key = settings.OPENAI_API_KEY

    def ensure_directories(self):
        """Ensure template and output directories exist"""
        os.makedirs(self.templates_dir, exist_ok=True)
        os.makedirs(self.output_dir, exist_ok=True)

    def customize_resume(
        self,
        template_path: str,
        job: Job,
        user_profile: Dict[str, Any],
        output_format: str = "docx"
    ) -> str:
        """Customize resume for a specific job"""
        
        try:
            # Load user profile and job data
            context = self._prepare_resume_context(job, user_profile)
            
            # Determine template type and process accordingly
            if template_path.endswith('.docx'):
                output_path = self._customize_docx_resume(template_path, context, job)
            elif template_path.endswith('.json'):
                output_path = self._customize_json_resume(template_path, context, job, output_format)
            else:
                # Text-based template
                output_path = self._customize_text_resume(template_path, context, job)
                
            return output_path
            
        except Exception as e:
            logger.error(f"Resume customization failed: {e}")
            raise

    def _prepare_resume_context(self, job: Job, user_profile: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare context data for resume customization"""
        
        # Extract key skills and requirements from job description
        job_keywords = self._extract_job_keywords(job.description or "")
        
        # Prioritize user skills based on job requirements
        prioritized_skills = self._prioritize_skills(
            user_profile.get("skills", []),
            job_keywords
        )
        
        # Generate tailored summary
        tailored_summary = self._generate_tailored_summary(job, user_profile)
        
        context = {
            "personal_info": user_profile.get("personal_info", {}),
            "contact": user_profile.get("contact", {}),
            "summary": tailored_summary,
            "skills": prioritized_skills[:12],  # Top 12 relevant skills
            "experience": self._tailor_experience(user_profile.get("experience", []), job),
            "education": user_profile.get("education", []),
            "certifications": user_profile.get("certifications", []),
            "projects": self._select_relevant_projects(user_profile.get("projects", []), job),
            "job_title": job.title,
            "company": job.company,
            "job_keywords": job_keywords,
            "date_generated": datetime.now().strftime("%Y-%m-%d")
        }
        
        return context

    def _extract_job_keywords(self, job_description: str) -> List[str]:
        """Extract relevant keywords from job description"""
        
        # Common product management keywords
        pm_keywords = [
            "product management", "product manager", "roadmap", "strategy",
            "agile", "scrum", "kanban", "stakeholder", "user experience",
            "analytics", "data-driven", "metrics", "kpi", "a/b testing",
            "market research", "competitive analysis", "feature prioritization",
            "product launch", "go-to-market", "cross-functional", "leadership"
        ]
        
        # Technical keywords
        tech_keywords = [
            "sql", "python", "javascript", "api", "rest", "graphql",
            "aws", "azure", "gcp", "docker", "kubernetes", "microservices",
            "machine learning", "ai", "data science", "business intelligence"
        ]
        
        # Industry keywords
        industry_keywords = [
            "saas", "b2b", "b2c", "enterprise", "startup", "fintech",
            "healthcare", "e-commerce", "marketplace", "mobile", "web"
        ]
        
        all_keywords = pm_keywords + tech_keywords + industry_keywords
        
        # Find keywords present in job description
        found_keywords = []
        job_desc_lower = job_description.lower()
        
        for keyword in all_keywords:
            if keyword in job_desc_lower:
                found_keywords.append(keyword)
                
        return found_keywords

    def _prioritize_skills(self, user_skills: List[str], job_keywords: List[str]) -> List[str]:
        """Prioritize user skills based on job requirements"""
        
        # Score skills based on relevance to job
        skill_scores = {}
        
        for skill in user_skills:
            score = 0
            skill_lower = skill.lower()
            
            # High score if skill directly matches job keyword
            for keyword in job_keywords:
                if keyword in skill_lower or skill_lower in keyword:
                    score += 10
                    
            # Medium score for partial matches
            for keyword in job_keywords:
                if any(word in skill_lower for word in keyword.split()):
                    score += 5
                    
            skill_scores[skill] = score
            
        # Sort skills by score and return
        sorted_skills = sorted(skill_scores.items(), key=lambda x: x[1], reverse=True)
        return [skill for skill, score in sorted_skills]

    def _generate_tailored_summary(self, job: Job, user_profile: Dict[str, Any]) -> str:
        """Generate a tailored professional summary"""
        
        if not settings.OPENAI_API_KEY:
            # Fallback to template-based summary
            return self._template_based_summary(job, user_profile)
            
        try:
            prompt = f"""
            Create a professional summary for a resume targeting this job:
            
            Job Title: {job.title}
            Company: {job.company}
            Job Description: {(job.description or '')[:1000]}
            
            Candidate Profile:
            - Years of Experience: {user_profile.get('years_experience', 5)}
            - Key Skills: {', '.join(user_profile.get('skills', [])[:10])}
            - Industry Focus: {user_profile.get('industry_focus', 'Technology')}
            - Current Role: {user_profile.get('current_role', 'Product Manager')}
            
            Write a 2-3 sentence professional summary that:
            1. Highlights relevant experience and skills for this specific role
            2. Uses keywords from the job description
            3. Demonstrates value proposition for this company
            4. Sounds authentic and professional
            
            Keep it concise and impactful.
            """
            
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a professional resume writer specializing in product management roles."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=200,
                temperature=0.7
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.warning(f"AI summary generation failed, using template: {e}")
            return self._template_based_summary(job, user_profile)

    def _template_based_summary(self, job: Job, user_profile: Dict[str, Any]) -> str:
        """Generate summary using templates when AI is not available"""
        
        years_exp = user_profile.get('years_experience', 5)
        skills = user_profile.get('skills', [])[:3]
        
        if 'director' in job.title.lower() or 'vp' in job.title.lower():
            template = f"Strategic product leader with {years_exp}+ years of experience driving product innovation and cross-functional team leadership. Proven expertise in {', '.join(skills)} with a track record of delivering high-impact products that drive business growth."
        elif 'senior' in job.title.lower():
            template = f"Experienced Product Manager with {years_exp}+ years building and scaling products. Expert in {', '.join(skills)} with demonstrated success in agile development, stakeholder management, and data-driven decision making."
        else:
            template = f"Results-driven Product Manager with {years_exp} years of experience in product development and strategy. Skilled in {', '.join(skills)} with a passion for creating user-centric products that solve real business problems."
            
        return template

    def _tailor_experience(self, experiences: List[Dict], job: Job) -> List[Dict]:
        """Tailor experience descriptions based on job requirements"""
        
        job_keywords = self._extract_job_keywords(job.description or "")
        tailored_experiences = []
        
        for exp in experiences:
            tailored_exp = exp.copy()
            
            # Enhance bullet points with relevant keywords
            if 'achievements' in exp:
                enhanced_achievements = []
                for achievement in exp['achievements']:
                    enhanced = self._enhance_achievement(achievement, job_keywords)
                    enhanced_achievements.append(enhanced)
                tailored_exp['achievements'] = enhanced_achievements
                
            tailored_experiences.append(tailored_exp)
            
        return tailored_experiences

    def _enhance_achievement(self, achievement: str, job_keywords: List[str]) -> str:
        """Enhance achievement bullet point with relevant keywords"""
        
        # Simple keyword injection where appropriate
        enhanced = achievement
        
        # Add quantifiable metrics if missing
        if not any(char.isdigit() for char in achievement):
            if 'led' in achievement.lower():
                enhanced = enhanced.replace('led', 'led cross-functional team of 5-8')
            elif 'managed' in achievement.lower():
                enhanced = enhanced.replace('managed', 'managed portfolio of 3-5 products')
                
        return enhanced

    def _select_relevant_projects(self, projects: List[Dict], job: Job) -> List[Dict]:
        """Select most relevant projects for the job"""
        
        if len(projects) <= 3:
            return projects
            
        job_keywords = self._extract_job_keywords(job.description or "")
        
        # Score projects based on relevance
        project_scores = []
        for project in projects:
            score = 0
            project_text = f"{project.get('name', '')} {project.get('description', '')}".lower()
            
            for keyword in job_keywords:
                if keyword in project_text:
                    score += 1
                    
            project_scores.append((project, score))
            
        # Return top 3 most relevant projects
        sorted_projects = sorted(project_scores, key=lambda x: x[1], reverse=True)
        return [project for project, score in sorted_projects[:3]]

    def _customize_docx_resume(self, template_path: str, context: Dict[str, Any], job: Job) -> str:
        """Customize a Word document resume template"""
        
        # Load the document
        doc = Document(template_path)
        
        # Replace placeholders in paragraphs
        for paragraph in doc.paragraphs:
            self._replace_placeholders_in_paragraph(paragraph, context)
            
        # Replace placeholders in tables
        for table in doc.tables:
            for row in table.rows:
                for cell in row.cells:
                    for paragraph in cell.paragraphs:
                        self._replace_placeholders_in_paragraph(paragraph, context)
        
        # Generate output filename
        output_filename = f"resume_{job.company}_{job.id}_{datetime.now().strftime('%Y%m%d')}.docx"
        output_path = os.path.join(self.output_dir, output_filename)
        
        # Save customized document
        doc.save(output_path)
        
        return output_path

    def _replace_placeholders_in_paragraph(self, paragraph, context: Dict[str, Any]):
        """Replace template placeholders in a paragraph"""
        
        placeholders = {
            "{{name}}": f"{context['personal_info'].get('first_name', '')} {context['personal_info'].get('last_name', '')}",
            "{{email}}": context['contact'].get('email', ''),
            "{{phone}}": context['contact'].get('phone', ''),
            "{{linkedin}}": context['contact'].get('linkedin', ''),
            "{{summary}}": context['summary'],
            "{{skills}}": ', '.join(context['skills']),
            "{{date}}": context['date_generated']
        }
        
        for placeholder, replacement in placeholders.items():
            if placeholder in paragraph.text:
                paragraph.text = paragraph.text.replace(placeholder, replacement)

    def generate_cover_letter(
        self,
        template: str,
        job: Job,
        user_profile: Dict[str, Any]
    ) -> str:
        """Generate a customized cover letter"""
        
        try:
            if settings.OPENAI_API_KEY:
                return self._generate_ai_cover_letter(job, user_profile)
            else:
                return self._generate_template_cover_letter(template, job, user_profile)
                
        except Exception as e:
            logger.error(f"Cover letter generation failed: {e}")
            raise

    def _generate_ai_cover_letter(self, job: Job, user_profile: Dict[str, Any]) -> str:
        """Generate cover letter using AI"""
        
        prompt = f"""
        Write a professional cover letter for this job application:
        
        Job Title: {job.title}
        Company: {job.company}
        Job Description: {(job.description or '')[:1500]}
        
        Candidate Background:
        - Name: {user_profile.get('personal_info', {}).get('first_name', 'John')} {user_profile.get('personal_info', {}).get('last_name', 'Doe')}
        - Years of Experience: {user_profile.get('years_experience', 5)}
        - Current Role: {user_profile.get('current_role', 'Product Manager')}
        - Key Skills: {', '.join(user_profile.get('skills', [])[:8])}
        - Industry Experience: {user_profile.get('industry_focus', 'Technology')}
        
        Write a compelling cover letter that:
        1. Shows genuine interest in the specific role and company
        2. Highlights relevant experience and achievements
        3. Demonstrates knowledge of the company/industry
        4. Uses keywords from the job description
        5. Maintains a professional yet engaging tone
        6. Is 3-4 paragraphs long
        
        Format with proper business letter structure.
        """
        
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a professional career advisor and expert cover letter writer."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=600,
            temperature=0.7
        )
        
        return response.choices[0].message.content.strip()

    def _generate_template_cover_letter(
        self,
        template: str,
        job: Job,
        user_profile: Dict[str, Any]
    ) -> str:
        """Generate cover letter using Jinja2 template"""
        
        # Prepare template context
        context = {
            "job": {
                "title": job.title,
                "company": job.company,
                "location": job.location
            },
            "candidate": {
                "name": f"{user_profile.get('personal_info', {}).get('first_name', '')} {user_profile.get('personal_info', {}).get('last_name', '')}",
                "years_experience": user_profile.get('years_experience', 5),
                "current_role": user_profile.get('current_role', 'Product Manager'),
                "top_skills": user_profile.get('skills', [])[:5]
            },
            "date": datetime.now().strftime("%B %d, %Y")
        }
        
        # Render template
        template_obj = Template(template)
        return template_obj.render(**context)

    def create_default_templates(self):
        """Create default resume and cover letter templates"""
        
        # Create default resume template (JSON format)
        default_resume = {
            "personal_info": {
                "name": "{{name}}",
                "email": "{{email}}",
                "phone": "{{phone}}",
                "linkedin": "{{linkedin}}",
                "location": "{{location}}"
            },
            "summary": "{{summary}}",
            "skills": "{{skills}}",
            "experience": "{{experience}}",
            "education": "{{education}}",
            "projects": "{{projects}}"
        }
        
        resume_template_path = os.path.join(self.templates_dir, "default_resume.json")
        with open(resume_template_path, 'w') as f:
            json.dump(default_resume, f, indent=2)
            
        # Create default cover letter template
        cover_letter_template = """
Dear Hiring Manager,

I am writing to express my strong interest in the {{job.title}} position at {{job.company}}. With {{candidate.years_experience}} years of experience in product management and a proven track record of delivering successful products, I am excited about the opportunity to contribute to your team.

In my current role as {{candidate.current_role}}, I have developed expertise in {{candidate.top_skills|join(', ')}}. I am particularly drawn to {{job.company}} because of your innovative approach to product development and commitment to user-centric design. My experience in cross-functional leadership and data-driven decision making aligns well with the requirements outlined in your job posting.

I would welcome the opportunity to discuss how my skills and passion for product management can contribute to {{job.company}}'s continued success. Thank you for considering my application.

Sincerely,
{{candidate.name}}
        """
        
        cover_letter_path = os.path.join(self.templates_dir, "default_cover_letter.txt")
        with open(cover_letter_path, 'w') as f:
            f.write(cover_letter_template.strip())
            
        return {
            "resume_template": resume_template_path,
            "cover_letter_template": cover_letter_path
        }