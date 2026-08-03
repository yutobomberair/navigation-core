import os

from dotenv import load_dotenv

load_dotenv()

LINE_CHANNEL_SECRET = "LINE_CHANNEL_SECRET"
LINE_CHANNEL_ACCESS_TOKEN = "LINE_CHANNEL_ACCESS_TOKEN"

# Where to send LINE users to finish onboarding (destination/current
# position/checkpoint test still happen on the web wizard, not LINE).
WEB_APP_BASE_URL = os.environ.get("WEB_APP_BASE_URL", "http://localhost:8501")


def get_env(key: str) -> str:
    value = os.environ.get(key)
    if not value:
        raise RuntimeError(
            f"Missing environment variable '{key}'. Set it in management/.env "
            "(gitignored) or your shell before running the webhook server."
        )
    return value
