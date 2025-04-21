from flask import Flask, jsonify
from telegram_scraper_client.client import MyTelegramClient
import threading
import logging
import asyncio

app = Flask(__name__)

# Shared status message
status_message = {"message": "Waiting for groups..."}
status_lock = threading.Lock()

# Configure logging
logging.basicConfig(level=logging.INFO)

@app.route('/')
def home():
    return 'NewsGPT'

@app.route('/status')
def get_status():
    with status_lock:
        return jsonify({"status": status_message["message"]}), 200

def start_telegram_listener():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    telegram = MyTelegramClient(session_name="session")

    async def run():
        await telegram.start()

        groups = await telegram.list_my_groups()

        if groups:
            logging.info(f"The first group is: {groups[0]['name']}")
        else:
            logging.error("No groups found")

    loop.run_until_complete(run())

if __name__ == '__main__':
    # Start Telegram listener in background thread
    listener_thread = threading.Thread(target=start_telegram_listener, daemon=True)
    listener_thread.start()

    # Start Flask
    app.run(debug=True)
