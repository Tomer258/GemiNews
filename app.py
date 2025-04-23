from quart import Quart, jsonify
from telegram_scraper_client.client import MyTelegramClient
import logging
import asyncio

app = Quart(__name__)
telegram = MyTelegramClient(session_name="session")

# Shared status message
status_message = {"message": "Waiting for groups..."}

# Configure logging
logging.basicConfig(level=logging.INFO)


@app.before_serving
async def startup():
    try:
        await telegram.start()
        logging.info("Telegram client started successfully")
        status_message["message"] = "Telegram client ready"
    except Exception as e:
        logging.error(f"Error starting Telegram client: {e}")
        status_message["message"] = f"Error: {e}"


@app.route('/')
async def home():
    return 'NewsGPT'


@app.route('/status')
async def get_status():
    return jsonify({"status": status_message["message"]}), 200


@app.route('/groups')
async def get_groups():
    logging.info("Starting to fetch groups...")
    try:
        groups = await telegram.list_my_groups()
    except Exception as e:
        logging.error(f"Failed to fetch groups: {e}")
        return jsonify({"error": str(e)}), 500

    if groups:
        logging.info(f"there are {len(groups)} groups: {groups}")
        return jsonify({"groups": groups}), 200
    else:
        logging.error("No groups found")
        return jsonify({"error": "No groups found"}), 404



if __name__ == '__main__':
    app.run(debug=True)
