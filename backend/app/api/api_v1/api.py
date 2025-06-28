from fastapi import APIRouter
from app.api.api_v1.endpoints import jobs, applications, communications, scrapers, email_parser

api_router = APIRouter()
api_router.include_router(jobs.router, prefix="/jobs", tags=["jobs"])
api_router.include_router(applications.router, prefix="/applications", tags=["applications"])
api_router.include_router(communications.router, prefix="/communications", tags=["communications"])
api_router.include_router(scrapers.router, prefix="/scrapers", tags=["scrapers"])
api_router.include_router(email_parser.router, prefix="/email-parser", tags=["email-parser"])