from pydantic_settings import BaseSettings, SettingsConfigDict                                                                                                      
                                                                                                                                                                        
class Settings(BaseSettings):                                                                                                                                       
    DATABASE_URL: str  # Required (will raise an validation error if missing)                                                                                       
    REDIS_URL: str                                                                                      
    JWT_SECRET_KEY: str
    ADMIN_REGISTRATION_SECRET: str = "super-secret-admin-key-change-me"
    ENV: str = "production"
    LOG_LEVEL: str = "INFO"

    # Grafana Loki Configuration
    LOKI_URL: str | None = None
    LOKI_USER: str | None = None
    LOKI_TOKEN: str | None = None

    # Provider Configuration
    EMAIL_PROVIDER: str = "resend"  # Options: resend, console, sendgrid
    CACHE_PROVIDER: str = "memory"  # Options: memory, redis
    
    # Provider Keys
    RESEND_API_KEY: str | None = None
    SENDGRID_API_KEY: str | None = None
    EMAIL_FROM: str = "onboarding@resend.dev"
    APP_BASE_URL: str = "http://localhost:3000"

    # Tells Pydantic to read from a .env file if the OS variables aren't set
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
settings = Settings()