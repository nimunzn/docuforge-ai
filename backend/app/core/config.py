from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    google_cloud_project_id: str = ""
    google_cloud_location: str = "us-central1"
    google_service_account_file: str = ""
    database_url: str = "sqlite:///./docuforge.db"
    secret_key: str = "your-secret-key-here"
    environment: str = "development"
    
    # Optional settings
    ollama_base_url: str = "http://localhost:11434"
    default_llm_provider: str = "google"
    default_openai_model: str = "gpt-4"
    default_claude_model: str = "claude-3-sonnet-20240229"
    default_google_model: str = "gemini-2.5-pro"

    class Config:
        env_file = ".env"


settings = Settings()