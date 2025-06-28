from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "applicationbot",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["app.tasks"]
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    result_expires=3600,
    
    # Task routing
    task_routes={
        "app.tasks.scrape_jobs": {"queue": "scraping"},
        "app.tasks.apply_to_jobs": {"queue": "applications"},
        "app.tasks.send_communications": {"queue": "communications"},
        "app.tasks.update_job_scores": {"queue": "analysis"},
    },
    
    # Beat schedule for periodic tasks
    beat_schedule={
        "scrape-jobs-hourly": {
            "task": "app.tasks.scrape_jobs_task",
            "schedule": 3600.0,  # Every hour
        },
        "process-scheduled-communications": {
            "task": "app.tasks.process_scheduled_communications_task",
            "schedule": 600.0,  # Every 10 minutes
        },
        "auto-apply-jobs": {
            "task": "app.tasks.auto_apply_jobs_task",
            "schedule": 1800.0,  # Every 30 minutes
        },
        "update-job-scores-daily": {
            "task": "app.tasks.update_job_scores_task",
            "schedule": 86400.0,  # Daily
        },
    },
)