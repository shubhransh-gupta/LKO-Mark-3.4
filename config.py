import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file from project root
ROOT_DIR = Path(__file__).parent.resolve()
load_dotenv(ROOT_DIR / ".env", override=True)

class Config:
    ROOT_DIR: Path = ROOT_DIR
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-flash-lite-latest")
    
    # Telegram Bot Settings
    TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    ALLOWED_TELEGRAM_USER_IDS: list[int] = [
        int(uid.strip())
        for uid in os.getenv("ALLOWED_TELEGRAM_USER_IDS", "").split(",")
        if uid.strip().isdigit()
    ]
    
    # Computer Use / Screen Settings
    SCREENSHOT_DIR: Path = ROOT_DIR / "screenshots"
    SCREENSHOT_MAX_WIDTH: int = 1920
    
    # App Settings
    APP_NAME: str = "LKO Mark 3.4"
    
    @classmethod
    def is_configured(cls) -> tuple[bool, str]:
        load_dotenv(ROOT_DIR / ".env", override=True)
        cls.GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
        if not cls.GEMINI_API_KEY:
            return False, "GEMINI_API_KEY missing"
        return True, "Configured"

# Ensure screenshot directory exists
Config.SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)
