# Placeholder for configuration
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    EDITORIAL_SERVICE_URL: str = "http://editorial-service:8040"
    TOPIC_MANAGER_URL: str = "http://topic-manager:8041"
    CHROMADB_HOST: str = "chromadb"
    CHROMADB_PORT: int = 8000
    
    # Schedule for the harvester to run (cron format)
    HARVEST_SCHEDULE_CRON: str = "0 */6 * * *" # Every 6 hours

    # API Keys
    # GITHUB_API_KEY: str | None = None

settings = Settings()
