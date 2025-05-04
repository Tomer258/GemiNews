from preprocess_model import summarizer_V2
from telegram_scraper_client.client import MyTelegramClient
import logging
import asyncio
from telegram_bot_controller import post_to_telegram

logging.basicConfig(level=logging.INFO)
telegram = MyTelegramClient()
GROUPS_TO_FILTER = [
    2037759911, 4782122177, 1366957750, 1221094308,
    1462170103, 1282609022, 1327700838, 1281218345, 1414072921,4711287485,-1002596608857
]

def batch_groups(groups, batch_size=5):
    for i in range(0, len(groups), batch_size):
        yield groups[i:i + batch_size]

async def get_summarize():
    current_summary = None
    try:
        await telegram.start()
        logging.info("Telegram client started successfully")
    except Exception as e:
        logging.error(f"Error starting Telegram client: {e}")


    try:
        groups = await telegram.list_my_groups()
        filtered_groups = [g for g in groups if g['id'] not in GROUPS_TO_FILTER]
        logging.info(f"Fetched {len(filtered_groups)} groups after filtering.")

        batches = list(batch_groups(filtered_groups, batch_size=5))
        logging.info(f"Split into {len(batches)} batches.")

        for batch_number, batch in enumerate(batches, 1):
            logging.info(f"Processing batch {batch_number}/{len(batches)}...")
            batch_summaries = []

            for group in batch:
                group_id = group['id']
                group_name = group.get('name') or str(group_id)

                try:
                    messages = await telegram.get_recent_messages(group_id)
                    group_data = { "result": { group_name: messages } }

                    summary = summarizer_V2.summarize_json_dict_as_string(group_data)
                    batch_summaries.append(summary)

                    logging.info(f"✅ Summarized group: {group_name}")
                except Exception as e:
                    logging.error(f"❌ Failed to summarize {group_name}: {e}")

            combined_batch_text = "\n\n".join(batch_summaries)
            combined_prompt = f"""\
הנה סיכומים חלקיים של מספר קבוצות חדשות:
{combined_batch_text}

אחד את הסיכומים הללו לסיכום אחד תמציתי וברור.
התמקד רק בפרטים החשובים ביותר והימנע באופן מוחלט מכפילויות.
"""
            try:
                batch_input = {
                    "result": {
                        "Batch Summary": [{"text": combined_prompt}]
                    }
                }
                batch_summary = summarizer_V2.summarize_individual_batch(batch_input)

                if current_summary is None:
                    current_summary = batch_summary
                else:
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
                    current_summary = summarizer_V2.summarize_json_dict_as_string(final_data)

                logging.info(f"✅ Finished batch {batch_number}/{len(batches)}.")
            except Exception as e:
                logging.error(f"❌ Failed to combine batch {batch_number}: {e}")

            await asyncio.sleep(20)

        if not current_summary:
            current_summary = "לא נמצאו קבוצות או הודעות לסיכום."

        final_summary = summarizer_V2.translate_summary_to_telegram_hebrew(current_summary)
        messages = summarizer_V2.split_summary_for_telegram(final_summary)
        for i, msg in enumerate(messages, 1):
            logging.info(f"msg #{i} is: {msg[:100]}")
            post_to_telegram(msg,1)

        final_summary_ru = summarizer_V2.translate_summary_to_telegram_russian(final_summary)
        messages_ru = summarizer_V2.split_summary_for_telegram(final_summary_ru)
        for i, msg in enumerate(messages_ru, 1):
            logging.info(f"russian msg #{i} is: {msg[:100]}")
            post_to_telegram(msg,2)

        logging.info("All summaries posted successfully.")

    except Exception as e:
        logging.error(f"Unhandled error in get_summarize(): {e}")


if __name__ == "__main__":
    asyncio.run(get_summarize())
