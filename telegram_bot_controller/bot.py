import os
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

TELEGRAM_BOT_KEY = os.getenv("TELEGRAM_BOT_KEY")
TELEGRAM_BOT_GROUP_ID = os.getenv("TELEGRAM_BOT_GROUP_ID")
TELEGRAM_BOT_RU_GROUP_ID = os.getenv("TELEGRAM_BOT_RU_GROUP_ID")


def post_to_telegram(message: str,grp:int = 1):
    """
    Sends a message to a Telegram channel.
    """
    if not TELEGRAM_BOT_KEY or not TELEGRAM_BOT_GROUP_ID:
        raise ValueError("Missing Telegram bot token or chat ID.")

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_KEY}/sendMessage"
    payload = {
        "chat_id": (TELEGRAM_BOT_GROUP_ID if grp == 1 else TELEGRAM_BOT_RU_GROUP_ID) ,
        "text": message,
        "parse_mode": "HTML",  # or "Markdown"
        "disable_web_page_preview": True,
    }

    response = requests.post(url, json=payload)
    if response.status_code != 200:
        raise Exception(f"Telegram API error: {response.text}")

    return response.json()
