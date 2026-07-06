import os
from pathlib import Path
from dotenv import load_dotenv

# Base directory of the project
BASE_DIR = Path(__file__).resolve().parent.parent

# Load environment variables from .env file
env_path = BASE_DIR / ".env"
if env_path.exists():
    load_dotenv(dotenv_path=env_path)
else:
    # Fallback to general environment
    load_dotenv()

class Settings:
    """Application settings loaded from environment variables."""
    # Server Settings
    HOST: str = os.getenv("HOST", "127.0.0.1")
    PORT: int = int(os.getenv("PORT", "8000"))
    DEBUG: bool = os.getenv("DEBUG", "True").lower() in ("true", "1", "t", "y", "yes")

    # API Keys and Models
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    DEFAULT_MODEL: str = os.getenv("DEFAULT_MODEL", "gemini").lower()  # 'gemini' or 'lamini'
    GEMINI_MODEL_NAME: str = os.getenv("GEMINI_MODEL_NAME", "gemini-2.5-flash")
    LAMINI_MODEL_NAME: str = os.getenv("LAMINI_MODEL_NAME", "MBZUAI/LaMini-Flan-T5-248M")

    # Paths
    BASE_PATH: Path = BASE_DIR
    STATIC_PATH: Path = BASE_DIR / "app" / "static"
    TEMPLATES_PATH: Path = BASE_DIR / "app" / "templates"
    LOGS_PATH: Path = BASE_DIR / "logs"

    # HF cache directory path to prevent dumping in user home
    HF_CACHE_DIR: Path = BASE_DIR / ".cache" / "huggingface"

    # MongoDB Settings
    MONGODB_URL: str = os.getenv("MONGODB_URL", "")
    MONGODB_DB_NAME: str = os.getenv("MONGODB_DB_NAME", "edugenie")

    # JWT Settings
    JWT_SECRET: str = os.getenv("JWT_SECRET", "super_secret_pedagogical_genie_key_2026_change_me")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")


    def is_gemini_configured(self) -> bool:
        """Check if Gemini API Key is loaded."""
        return bool(self.GEMINI_API_KEY and self.GEMINI_API_KEY != "your_gemini_api_key_here")

# Instantiate settings singleton
settings = Settings()
