from quart import Quart, jsonify,render_template_string

import preprocess_model
from preprocess_model.summarizer import get_models
from preprocess_model.summarizer_V2 import summarize_individual_batch,get_models
from telegram_scraper_client.client import MyTelegramClient
import logging
from database_controller.db import db, connect_db, disconnect_db
from datetime import datetime
import asyncio
from telegram_bot_controller import post_to_telegram



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


def batch_groups(groups, batch_size=5):
    for i in range(0, len(groups), batch_size):
        yield groups[i:i + batch_size]

@app.route('/models')
async def get_models():
    models = get_models()
    return await render_template_string("""
                <!DOCTYPE html>
                <html lang="he" dir="rtl">
                <head>
                    <meta charset="UTF-8">
                    <title>MODELS</title>
                </head>
                <body>
                    <h1>MODELS </h1>
                    <pre style="font-family: Arial, sans-serif; white-space: pre-wrap;">{{ summary|safe }}</pre>
                </body>
                </html>
            """, summary=models)


@app.route('/result')
async def get_summarize():
    current_summary = None
    try:
        groups = await telegram.list_my_groups()

        # Filter unwanted groups
        filtered_groups = [
            group for group in groups
            if group['id'] != 2037759911
        ]

        logging.info(f"Fetched {len(filtered_groups)} groups after filtering.")

        # Break into batches of 5
        batches = list(batch_groups(filtered_groups, batch_size=5))

        logging.info(f"Split into {len(batches)} batches of 5 groups each.")

        batch_number = 1

        for batch in batches:
            logging.info(f"Processing batch {batch_number} / {len(batches)}...")

            batch_summaries = []

            for group in batch:
                group_id = group['id']
                group_name = group['name']
                identifier = group_name or str(group_id)

                # Fetch messages for the group
                messages = await telegram.get_recent_messages(group_id)

                group_data = {
                    "result": {
                        identifier: messages
                    }
                }

                try:
                    # Summarize this group
                    group_summary = preprocess_model.summarizer_V2.summarize_json_dict_as_string(group_data)
                    batch_summaries.append(group_summary)

                    logging.info(f"Summarized group: {identifier}")

                except Exception as e:
                    logging.error(f"Failed to summarize group {identifier}: {e}")

            # Merge all group summaries in the batch into one text
            combined_batch_text = "\n\n".join(batch_summaries)

            # Create a "batch combine" prompt
            combined_prompt = f"""\
            הנה סיכומים חלקיים של מספר קבוצות חדשות:
            {combined_batch_text}
            
            אחד את הסיכומים הללו לסיכום אחד תמציתי וברור.
            התמקד רק בפרטים החשובים ביותר והימנע באופן מוחלט מכפילויות.
            """

            try:
                # Summarize the whole batch
                batch_combined_data = {
                    "result": {
                        "Batch Summary": [{"text": combined_prompt}]
                    }
                }
                batch_summary = preprocess_model.summarizer_V2.summarize_individual_batch(batch_combined_data)

                if current_summary is None:
                    current_summary = batch_summary
                else:
                    # Merge this batch summary into the current global summary
                    final_prompt = f"""\
                    להלן סיכום קיים:
                    {current_summary}
                    
                    להלן סיכום חדש של קבוצת חדשות נוספת:
                    {batch_summary}
                    
                    אחד את שני הסיכומים לסיכום אחד קצר וברור, מבלי לחזור על מידע.
                    """

                    final_data = {
                        "result": {
                            "Final Summary": [{"text": final_prompt}]
                        }
                    }
                    current_summary = preprocess_model.summarizer_V2.summarize_json_dict_as_string(final_data)

                logging.info(f"✅ Finished batch {batch_number}/{len(batches)}.")

            except Exception as e:
                logging.error(f"Failed to combine batch {batch_number}: {e}")

            batch_number += 1

            # 💤 Sleep after each batch to avoid quota limit
            await asyncio.sleep(20)

        if current_summary is None:
            current_summary = "לא נמצאו קבוצות או הודעות לסיכום."

        current_summary = preprocess_model.summarizer_V2.translate_summary_to_telegram_hebrew(current_summary)
        chunks_to_post = preprocess_model.summarizer_V2.split_summary_for_telegram(current_summary)
        for i, msg in enumerate(chunks_to_post, 1):
            post_to_telegram(msg)

        # Render final summary
        return await render_template_string("""
            <!DOCTYPE html>
            <html lang="he" dir="rtl">
            <head>
                <meta charset="UTF-8">
                <title>סיכום חדשות מאוחד</title>
            </head>
            <body>
                <h1>📰 סיכום חדשות מאוחד</h1>
                <pre style="font-family: Arial, sans-serif; white-space: pre-wrap;">{{ summary|safe }}</pre>
            </body>
            </html>
        """, summary=current_summary)

    except Exception as e:
        logging.error(f"Failed to summarize everything: {e}")
        return "קרתה שגיאה בעת סיכום החדשות", 500




if __name__ == '__main__':
    app.run(debug=True)
