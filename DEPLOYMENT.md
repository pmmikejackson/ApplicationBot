# ApplicationBot Deployment Guide

## Quick Start

1. **Clone and Setup**
   ```bash
   git clone <repository-url>
   cd ApplicationBot
   chmod +x setup.sh
   ./setup.sh
   ```

2. **Configure Environment**
   Edit `.env` file with your settings:
   ```bash
   cp .env.example .env
   nano .env
   ```

3. **Start the Application**
   ```bash
   docker-compose up -d
   ```

4. **Access the Dashboard**
   - Frontend: http://localhost:3000
   - API Docs: http://localhost:8000/docs
   - Admin: http://localhost:8000/admin

## Environment Configuration

### Required Settings
```env
# Database
POSTGRES_PASSWORD=your-secure-password
SECRET_KEY=your-secret-key-change-this

# Email (for notifications and follow-ups)
SMTP_HOST=smtp.gmail.com
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
```

### Optional Settings
```env
# AI Features
OPENAI_API_KEY=sk-your-openai-key

# Platform Credentials (for automated applications)
LINKEDIN_USERNAME=your-linkedin-email
LINKEDIN_PASSWORD=your-linkedin-password
INDEED_USERNAME=your-indeed-email
INDEED_PASSWORD=your-indeed-password
```

## Database Setup

### Initialize Database
```bash
# Enter backend container
docker-compose exec backend bash

# Run migrations
alembic upgrade head

# Create default templates
python -c "from app.services.document_service import DocumentCustomizationService; DocumentCustomizationService().create_default_templates()"
```

### Create Admin User (Optional)
```bash
# In backend container
python -c "
from app.core.database import SessionLocal
from app.models.user import User
from app.core.security import get_password_hash
db = SessionLocal()
user = User(
    email='admin@applicationbot.com',
    username='admin',
    hashed_password=get_password_hash('admin123'),
    first_name='Admin',
    last_name='User',
    is_active=True
)
db.add(user)
db.commit()
print('Admin user created: admin@applicationbot.com / admin123')
"
```

## Service Architecture

### Core Services
- **FastAPI Backend** (Port 8000): REST API and business logic
- **PostgreSQL** (Port 5432): Primary database
- **Redis** (Port 6379): Task queue and caching
- **Celery Worker**: Background task processing
- **React Frontend** (Port 3000): User interface

### Background Tasks
- **Job Scraping**: Hourly discovery of new jobs
- **Auto-Apply**: Automated application submission
- **Follow-ups**: Scheduled email communications
- **Score Updates**: Daily job fit score recalculation

## Monitoring & Maintenance

### Check System Health
```bash
# Check all services
docker-compose ps

# View logs
docker-compose logs -f backend
docker-compose logs -f celery
docker-compose logs -f frontend

# Check database
docker-compose exec postgres psql -U applicationbot -d applicationbot -c "\dt"
```

### Backup Database
```bash
# Create backup
docker-compose exec postgres pg_dump -U applicationbot applicationbot > backup_$(date +%Y%m%d).sql

# Restore backup
docker-compose exec -T postgres psql -U applicationbot applicationbot < backup_20240101.sql
```

### Scale Workers
```bash
# Scale Celery workers
docker-compose up -d --scale celery=3
```

## Security Considerations

### Production Checklist
- [ ] Change default passwords in `.env`
- [ ] Use strong SECRET_KEY (generate with `openssl rand -hex 32`)
- [ ] Enable HTTPS with reverse proxy (nginx/Apache)
- [ ] Restrict database access to application only
- [ ] Regular security updates
- [ ] Monitor logs for suspicious activity

### Credential Protection
- Platform credentials are encrypted at rest
- Database passwords should be rotated regularly
- Use environment-specific `.env` files
- Never commit secrets to version control

## Troubleshooting

### Common Issues

**1. Celery Tasks Not Running**
```bash
# Check Redis connection
docker-compose exec redis redis-cli ping

# Restart Celery
docker-compose restart celery
```

**2. Database Connection Errors**
```bash
# Check PostgreSQL status
docker-compose exec postgres pg_isready -U applicationbot

# Reset database
docker-compose down -v
docker-compose up -d postgres
# Wait 30 seconds, then run migrations
```

**3. Scraping Failures**
```bash
# Check Chrome/Selenium setup
docker-compose exec backend python -c "
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
options = Options()
options.add_argument('--headless')
driver = webdriver.Chrome(options=options)
driver.get('https://google.com')
print('Chrome test successful')
driver.quit()
"
```

**4. Frontend Build Issues**
```bash
# Rebuild frontend
docker-compose build frontend
docker-compose up -d frontend
```

### Log Analysis
```bash
# Backend errors
docker-compose logs backend | grep ERROR

# Application failures
docker-compose exec backend tail -f /app/logs/application.log

# Job scraping issues
docker-compose logs celery | grep "scrape_jobs_task"
```

## Performance Optimization

### Database Optimization
```sql
-- Add indexes for common queries
CREATE INDEX idx_jobs_fit_score ON jobs(fit_score DESC);
CREATE INDEX idx_jobs_priority_status ON jobs(priority, status);
CREATE INDEX idx_applications_status_date ON applications(status, created_at);
```

### Scraping Performance
- Adjust `MAX_CONCURRENT_SCRAPERS` in `.env`
- Tune `SCRAPING_DELAY_MIN/MAX` for rate limiting
- Monitor platform rate limits
- Use proxy rotation for high-volume scraping

### Task Queue Optimization
```bash
# Monitor queue length
docker-compose exec redis redis-cli llen celery

# Adjust worker concurrency
# Add to docker-compose.yml:
# command: celery -A app.core.celery worker --loglevel=info --concurrency=4
```

## API Integration

### Webhook Setup (Optional)
Configure webhooks for external integrations:
```python
# Add to user settings
{
  "webhooks": {
    "job_discovered": "https://your-app.com/webhook/job-discovered",
    "application_submitted": "https://your-app.com/webhook/application-submitted"
  }
}
```

### External API Usage
```bash
# Get job statistics
curl http://localhost:8000/api/v1/jobs/stats/summary

# Trigger scraping
curl -X POST http://localhost:8000/api/v1/scrapers/scrape \
  -H "Content-Type: application/json" \
  -d '{"keywords": ["Product Manager"], "location": "Remote", "remote_only": true}'
```

## Backup & Recovery

### Automated Backups
```bash
# Add to crontab
0 2 * * * cd /path/to/ApplicationBot && docker-compose exec postgres pg_dump -U applicationbot applicationbot | gzip > backups/backup_$(date +\%Y\%m\%d).sql.gz
```

### Disaster Recovery
1. Stop all services: `docker-compose down`
2. Restore database from backup
3. Restart services: `docker-compose up -d`
4. Verify data integrity
5. Resume normal operations

## Support

For technical support:
1. Check logs for error messages
2. Review this deployment guide
3. Search existing GitHub issues
4. Create new issue with logs and configuration details