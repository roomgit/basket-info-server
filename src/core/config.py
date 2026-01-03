import os


class Settings:
    """Application settings"""

    API_KEY: str = os.environ.get("API_KEY", "your-default-api-key-change-this")
    PORT: int = int(os.environ.get("PORT", 8080))
    HOST: str = "0.0.0.0"
    MAX_MESSAGE_LENGTH: int = 1000
    APP_TITLE: str = "WebSocket Server"


settings = Settings()
