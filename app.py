from quart import Quart, jsonify
from telegram_scraper_client.client import MyTelegramClient
import logging
from db import db, connect_db, disconnect_db
from datetime import datetime



app = Quart(__name__)
telegram = MyTelegramClient()


# Shared status message
status_message = {"message": "Waiting for groups..."}

# Configure logging
logging.basicConfig(level=logging.INFO)


@app.before_serving
async def startup():
    await connect_db()
    try:
        await telegram.start()
        logging.info("Telegram client started successfully")
        status_message["message"] = "Telegram client ready"
    except Exception as e:
        logging.error(f"Error starting Telegram client: {e}")
        status_message["message"] = f"Error: {e}"

@app.after_serving
async def shutdown():
    await disconnect_db()


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

        # Save groups into DB
        query = """INSERT INTO chat_groups (id, name, username, type)
                          VALUES (:id, :name, :username, :type)
                          ON CONFLICT (id) DO NOTHING"""
        for group in groups:
            await db.execute(query, group)
    except Exception as e:
        logging.error(f"Failed to fetch groups: {e}")
        return jsonify({"error": str(e)}), 500

    if groups:
        logging.info(f"there are {len(groups)} groups: {groups}")
        return jsonify({"groups": groups}), 200
    else:
        logging.error("No groups found")
        return jsonify({"error": "No groups found"}), 404


@app.route('/msgFromGroups')
async def get_msg_from_groups():
    try:
        result={}
        groups = await telegram.list_my_groups()
        for group in groups:
            group_id = group['id']
            group_name = group['name']
            identifier = group_name or str(group_id)  # fallback if no name

            messages = await telegram.get_recent_messages(group_id)
            result[identifier] = messages

            # Save messages to DB
            insert_query = """INSERT INTO messages (id, group_id, message_text, date)
                                          VALUES (:id, :group_id, :text, :date)
                                          ON CONFLICT (id) DO NOTHING"""
            for msg in messages:
                msg_date = datetime.fromisoformat(msg["date"]).replace(tzinfo=None)
                await db.execute(insert_query, {
                    "id": msg["id"],
                    "group_id": group_id,
                    "text": msg["text"],
                    "date":  msg_date,
                })

        return jsonify({"result": result}), 200
    except Exception as e:
        logging.error(f"Failed to fetch msgs: {e}")




if __name__ == '__main__':
    app.run(debug=True)
