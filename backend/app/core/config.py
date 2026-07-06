from pydantic_settings import BaseSettings, SettingsConfigDict                                                                                                      
                                                                                                                                                                        
class Settings(BaseSettings):                                                                                                                                       
    DATABASE_URL: str  # Required (will raise an validation error if missing)                                                                                       
    REDIS_URL: str                                                                                      
    JWT_SECRET_KEY: str

    # Tells Pydantic to read from a .env file if the OS variables aren't set
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
settings = Settings()