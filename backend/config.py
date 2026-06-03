"""Application configuration, loaded from environment / .env."""
from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

# Populate os.environ from .env so libraries that read the environment directly
# (notably LangChain's LangSmith tracer, which looks for LANGSMITH_*) pick it up.
# pydantic-settings only loads .env into the Settings object, not os.environ.
load_dotenv()


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # OpenAI (app runtime — GPT-4o + Whisper)
    openai_api_key: str = ""
    openai_model: str = "gpt-4o"
    openai_whisper_model: str = "whisper-1"

    # Storage
    upload_dir: str = "uploads"
    max_upload_mb: int = 500
    cloudinary_url: str = ""  # set in prod → switches storage backend

    # CORS
    frontend_origin: str = "http://localhost:5173"

    # Observability (optional)
    langsmith_tracing: bool = False
    langsmith_api_key: str = ""
    langsmith_project: str = "ai-video-editor"

    @property
    def use_cloudinary(self) -> bool:
        return bool(self.cloudinary_url)


settings = Settings()
