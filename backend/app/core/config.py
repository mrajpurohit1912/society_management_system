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
    EMAIL_PROVIDER: str = "smtp"  # Options: smtp, resend, console, sendgrid
    CACHE_PROVIDER: str = "memory"  # Options: memory, redis
    
    # SMTP Email Configuration (Gmail, AWS SES SMTP, Sendgrid SMTP, etc.)
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str | None = None
    SMTP_PASSWORD: str | None = None
    SMTP_USE_TLS: bool = True

    # Provider Keys
    RESEND_API_KEY: str | None = None
    SENDGRID_API_KEY: str | None = None
    EMAIL_FROM: str = "mrajpurohit1912@gmail.com"
    APP_BASE_URL: str = "https://society-management-system-roan.vercel.app"

    # CORS & External Providers
    ALLOWED_ORIGINS: str | None = None
    GOOGLE_CLIENT_ID: str = "your-google-client-id"
    RAZORPAY_KEY_ID: str | None = None
    RAZORPAY_KEY_SECRET: str | None = None

    # Tells Pydantic to read from a .env file if the OS variables aren't set
    model_config = SettingsConfigDict(env_file=(".env", "backend/.env"), extra="ignore")
settings = Settings()