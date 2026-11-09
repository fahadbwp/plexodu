"""Report environment presence without values, network calls or configuration imports."""
import os
from pathlib import Path

from dotenv import load_dotenv


VARIABLES = (
    "SECRET_KEY", "DATABASE_URL", "YOUTUBE_API_KEY", "GROQ_API_KEY", "GROQ_MODEL",
    "CORS_ALLOWED_ORIGINS", "API_RATE_LIMIT_PER_MIN", "AI_RATE_LIMIT_PER_MIN",
    "DATA_DIR", "CRON_SECRET", "FLASK_ENV", "HOST", "PORT", "FLASK_DEBUG",
    "AUTH_RATE_LIMIT_PER_MIN",  # Still read by legacy security_guard.py.
)


def main():
    load_dotenv(Path(__file__).resolve().parent.parent / ".env")
    for name in VARIABLES:
        print(f"{name}: {'OK' if os.environ.get(name, '').strip() else 'MISSING'}")


if __name__ == "__main__":
    main()
