# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Environment Setup
```bash
# Initial setup
./setup.sh                                    # Creates .env and directories
cp .env.example .env                          # Manual environment file creation

# Backend development
cd backend
python -m venv venv
source venv/bin/activate                      # Linux/Mac
pip install -r requirements.txt

# Frontend development  
cd frontend
npm install
npm start                                     # Development server on port 3000
```

### Email Parsing Configuration
For email parsing to work, add these settings to your `.env` file:

```bash
# Email Parsing Settings
EMAIL_PARSING_ENABLED=true
IMAP_SERVER=imap.gmail.com                    # For Gmail users
IMAP_USER=your-email@gmail.com
IMAP_PASSWORD=your-app-specific-password      # Use app password for Gmail

# Alternative email providers:
# IMAP_SERVER=imap.outlook.com               # For Outlook/Hotmail
# IMAP_SERVER=imap.yahoo.com                 # For Yahoo Mail
```

**Gmail App Password Setup:**
1. Enable 2-factor authentication on your Google account
2. Go to Google Account settings > Security > App passwords
3. Generate app password for "Mail"
4. Use this password (not your regular password) in IMAP_PASSWORD

### Docker Operations
```bash
# Production deployment
docker-compose up -d                         # Start all services
docker-compose down                          # Stop all services
docker-compose ps                            # Check service status
docker-compose logs -f [service]             # View logs

# Database operations
docker-compose exec backend alembic upgrade head                # Run migrations
docker-compose exec backend alembic revision --autogenerate    # Create migration
docker-compose exec postgres psql -U applicationbot applicationbot  # Database access
```

### Synology NAS Deployment
The system is currently deployed on Synology NAS with the following configuration:
- **NAS IP**: 192.168.1.79
- **Frontend Port**: 9001 (accessible at http://192.168.1.79:9001)
- **Backend Port**: 8001 (API at http://192.168.1.79:8001)
- **Database Port**: 5433 (mapped from container port 5432)
- **Redis Port**: 6380 (mapped from container port 6379)
- **Project Location**: `/volume1/docker/ApplicationBot/`

**Known Issues & Solutions**:
- CORS configured for development with wildcard origins
- Database enum values use lowercase strings, not enum names
- TypeScript imports require explicit .tsx/.ts extensions
- Port conflicts resolved by using non-standard ports

### Development & Testing
```bash
# Backend development
cd backend
uvicorn app.main:app --reload                # Start FastAPI with hot reload
python -m pytest                             # Run backend tests
alembic upgrade head                          # Apply database migrations

# Frontend development
cd frontend
npm test                                      # Run React tests
npm run build                                # Production build

# Background tasks
cd backend
celery -A app.core.celery worker --loglevel=info    # Start Celery worker
celery -A app.core.celery beat --loglevel=info      # Start Celery scheduler
```

### Recent Updates (2025-06-28)
**Workflow Implementation Completed**:
- ✅ Two-column Jobs page layout ("Jobs Available" vs "Jobs Applied For")
- ✅ Kanban-style Applications page with drag-and-drop functionality
- ✅ Automated workflow: job application → status sync → Kanban progression
- ✅ In-memory persistence for mock data across page navigation
- ✅ Fixed decimal displays in dashboard charts and statistics
- ✅ Priority-based color coding and visual "Apply Now" buttons
- ✅ Complete job-application status synchronization in backend

**Email Parsing System Added**:
- ✅ Email parser service for extracting jobs from platform emails
- ✅ Support for LinkedIn, Indeed, and BuiltIn email formats
- ✅ IMAP integration for reading email inbox
- ✅ Pattern-based job information extraction (title, company, location, URL)
- ✅ API endpoints for email parsing with configuration testing
- ✅ Safer alternative to web scraping with real job alert emails

**Automatic Background Processing**:
- ✅ Celery task for automatic email processing every 15 minutes
- ✅ Clean dashboard UI without manual trigger buttons
- ✅ Email processing status indicator on dashboard
- ✅ Duplicate job detection and filtering
- ✅ Integration with existing mock data store
- ✅ Comprehensive EMAIL_SETUP_GUIDE.md documentation
- ✅ Production-ready for dogfooding and future monetization

### Database Management
```bash
# Initialize database with default data
docker-compose exec backend python -c "from app.services.document_service import DocumentCustomizationService; DocumentCustomizationService().create_default_templates()"

# Create database migration
docker-compose exec backend alembic revision --autogenerate -m "description"

# Backup/restore
docker-compose exec postgres pg_dump -U applicationbot applicationbot > backup.sql
docker-compose exec -T postgres psql -U applicationbot applicationbot < backup.sql
```

## Architecture Overview

### High-Level System Design
ApplicationBot is a multi-container job application automation system built with:
- **FastAPI Backend**: RESTful API with async support, Celery task queue integration
- **React Frontend**: TypeScript SPA with Tailwind CSS, real-time dashboard
- **PostgreSQL**: Primary data store with SQLAlchemy ORM, Alembic migrations
- **Redis**: Task queue backend and caching layer
- **Celery**: Background task processing for scraping, scoring, applications

### Core Domain Models
The system revolves around three primary entities with specific state transitions:

**Job Lifecycle**: `DISCOVERED -> FILTERED -> APPLIED -> UNDER_REVIEW -> INTERVIEW_SCHEDULED -> (REJECTED|OFFER_RECEIVED)`
- Jobs have `fit_score` (0-10) and `priority` (MUST_APPLY, GOOD_FIT, STRETCH, LOW_PRIORITY)
- Platform-specific scrapers inherit from `BaseScraper` with standardized interfaces
- Duplicate detection via `platform_id` and fuzzy matching

**Application Workflow**: `PENDING -> SUBMITTED|FAILED -> (retry logic)`
- Applications link jobs to execution attempts with error tracking
- Method tracking: AUTOMATED, MANUAL, SEMI_AUTOMATED
- Document customization per application with template system

**Communication Pipeline**: Automated follow-up sequences with template system
- Direction: INBOUND/OUTBOUND with status tracking
- Scheduled communications via Celery beat scheduler
- Integration points for email/calendar systems

### Service Layer Architecture
Services follow dependency injection pattern with database session management:

**ScraperService**: Orchestrates concurrent platform scraping
- Manages 4 platform-specific scrapers (LinkedIn, Indeed, BuiltIn, ZipRecruiter)
- Rate limiting and error recovery
- Duplicate detection across platforms

**JobMatchingService**: AI-powered job scoring and prioritization
- Multi-factor scoring algorithm (title, experience, skills, location, salary, remote)
- OpenAI integration for enhanced job analysis
- Dynamic score recalculation based on user profile changes

**ApplicationAutomator**: Form detection and submission automation
- Selenium-based form field detection and mapping
- Platform-specific application logic with fallback handling
- Document customization and upload automation

**CommunicationService**: Email automation and scheduling
- SMTP integration with template system
- Celery-based scheduling for follow-up sequences
- Communication history tracking

### Background Task System
Celery tasks are organized by functional area with specific scheduling:

**Periodic Tasks** (configured in `app/core/celery.py`):
- `scrape_jobs_task`: Hourly job discovery across all platforms
- `auto_apply_jobs_task`: 30-minute automated application processing  
- `process_scheduled_communications_task`: 10-minute email processing
- `update_job_scores_task`: Daily score recalculation

**On-Demand Tasks**:
- Individual platform scraping, AI job analysis, document generation
- Email sending, application retry logic

### Frontend Architecture
React application with TypeScript, organized by feature domains:
- **Services Layer**: Axios-based API client with typed interfaces
- **Component Hierarchy**: Reusable components with Tailwind CSS
- **State Management**: Local state with API integration, no global state library
- **Routing**: React Router with protected routes (when auth implemented)

### Database Schema Patterns
SQLAlchemy models use consistent patterns:
- Enum-based status fields with defined state transitions
- Timestamp tracking (`created_at`, `updated_at`) with server defaults
- Foreign key relationships with proper cascading
- Indexes on frequently queried fields (platform_id, status, priority)

### Configuration Management
Pydantic Settings pattern with environment-based configuration:
- `.env` file loading with validation
- Separate configs for development/production
- Platform credentials with encryption at rest
- Feature flags for AI integration, auto-apply functionality

### Security Architecture
- JWT-based authentication (user system ready but not enforced)
- Credential encryption using Fernet symmetric encryption
- Rate limiting for external API calls and scraping
- SQL injection protection via SQLAlchemy ORM
- CORS configuration for frontend/backend communication

### Error Handling Patterns
- Service layer exceptions with specific error types
- Celery task retries with exponential backoff
- Scraper error recovery with fallback strategies
- Database transaction rollback on failures
- Comprehensive logging with structured format

### Integration Points
- **OpenAI API**: Job analysis and document generation (optional)
- **SMTP**: Email communication (optional)
- **Web Scraping**: Selenium WebDriver with platform-specific logic
- **External Applications**: Platform-specific form submission

The system is designed for horizontal scaling with stateless services and external session storage (Redis).