# Placeholder for configuration
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    EDITORIAL_SERVICE_URL: str = "http://editorial-service:8040"
    TOPIC_MANAGER_URL: str = "http://topic-manager:8041"
    CHROMADB_HOST: str = "chromadb"
    CHROMADB_PORT: int = 8000
    CHROMADB_COLLECTION: str = "raw_trends"
    
    # Schedule for the harvester to run (cron format)
    HARVEST_SCHEDULE_CRON: str = "0 */6 * * *" # Every 6 hours

    # API Keys
    DEV_TO_API_KEY: str | None = None
    NEWS_DATA_API_KEY: str | None = None
    PRODUCT_HUNT_DEVELOPER_TOKEN: str | None = None
    TOPIC_MANAGER_TOKEN: str | None = None

    # Selective triage thresholds
    SELECTIVE_PROFILE_THRESHOLD: float = 0.7
    SELECTIVE_NOVELTY_THRESHOLD: float = 0.8
    # GITHUB_API_KEY: str | None = None

settings = Settings()
