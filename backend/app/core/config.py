from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "ApplicationBot"
    
    # Database
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_USER: str = "applicationbot"
    POSTGRES_PASSWORD: str = "password"
    POSTGRES_DB: str = "applicationbot"
    DATABASE_URL: Optional[str] = None
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379"
    
    # Security
    SECRET_KEY: str = "your-secret-key-change-this-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Email - SMTP (sending)
    SMTP_TLS: bool = True
    SMTP_PORT: Optional[int] = None
    SMTP_HOST: Optional[str] = None
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    
    # Email - IMAP (receiving/parsing)
    IMAP_SERVER: Optional[str] = None
    IMAP_USER: Optional[str] = None
    IMAP_PASSWORD: Optional[str] = None
    EMAIL_PARSING_ENABLED: bool = False
    
    # OpenAI
    OPENAI_API_KEY: Optional[str] = None
    
    # Job Platforms
    LINKEDIN_USERNAME: Optional[str] = None
    LINKEDIN_PASSWORD: Optional[str] = None
    INDEED_USERNAME: Optional[str] = None
    INDEED_PASSWORD: Optional[str] = None
    
    # Scraping Settings
    SCRAPING_DELAY_MIN: int = 2
    SCRAPING_DELAY_MAX: int = 5
    MAX_CONCURRENT_SCRAPERS: int = 3
    
    class Config:
        env_file = ".env"
        case_sensitive = True

    @property
    def database_url(self) -> str:
        if self.DATABASE_URL:
            return self.DATABASE_URL
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}/{self.POSTGRES_DB}"

settings = Settings()