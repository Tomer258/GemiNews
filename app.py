from flask import Flask, jsonify
from telegram_scraper_client.client import MyTelegramClient
import threading
import logging
import asyncio

app = Flask(__name__)
telegram = MyTelegramClient()

# This variable can be used to store the message status.
status_message = None

# Configure logging
logging.basicConfig(level=logging.INFO)


@app.route('/')
def home():
    return 'NewsGPT'


@app.route('/status')
def get_status():
    # You can access the status message here
    if status_message:
        return jsonify({"status": status_message}), 200
    else:
        return jsonify({"status": "Waiting for groups..."}), 200


def start_telegram_listener():
    global status_message
    # Create a new event loop for this thread
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)  # Set this as the current event loop for the thread
    telegram.start()  # Start the Telegram client in the event loop

    groups = telegram.list_my_groups()
    if groups:
        logging.info(f"The first group is: {groups[0]['name']}")
        status_message = f"First group: {groups[0]['name']}"  # Store this in the global variable
    else:
        logging.error("No groups found")
        status_message = "No groups found"

    # This will keep the listener alive, but without returning anything from the thread.
    if groups:
        telegram.listen_to_group(groups[0]['name'])


if __name__ == '__main__':
    # Start the Telethon listener in a background thread
    listener_thread = threading.Thread(target=start_telegram_listener, daemon=True)
    listener_thread.start()

    # Start the Flask server
    app.run(debug=True)
