import asyncio
import logging
from typing import List, Dict, Any, Optional

from telegram_scraper_client.client import MyTelegramClient
from preprocess_model import summarizer_V2
from telegram_bot_controller import post_to_telegram

# === CONFIGURATION ===

GROUPS_TO_EXCLUDE: List[int] = [
    2037759911, 4782122177, 1366957750, 1221094308,
    1462170103, 1282609022, 1327700838, 1281218345,
    1414072921, 4711287485, 1002596608857
]

BATCH_SIZE: int = 5
SLEEP_BETWEEN_BATCHES: int = 20  # seconds

# Hebrew-to-English translated prompts
PARTIAL_SUMMARIES_PROMPT = """\
Here are partial summaries from several news groups:
{batch_summaries}

Please merge them into one concise and clear summary.
Focus only on the most important details and strictly avoid any duplication.
"""

MERGE_EXISTING_SUMMARIES_PROMPT = """\
Here is the current summary:
{existing}

Here is a new summary from another group:
{new}

Merge both into a short and clear summary without repeating information.
"""

# === LOGGING ===

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# === TELEGRAM CLIENT ===

telegram_client = MyTelegramClient()


# === HELPER FUNCTIONS ===

def batch_groups(groups: List[Dict[str, Any]], batch_size: int) -> List[List[Dict[str, Any]]]:
    """Split groups into batches of a specified size."""
    return [groups[i:i + batch_size] for i in range(0, len(groups), batch_size)]


async def initialize_telegram_client() -> None:
    """Start the Telegram client."""
    try:
        await telegram_client.start()
        logger.info("✅ Telegram client started successfully")
    except Exception as e:
        logger.error(f"❌ Failed to start Telegram client: {e}")
        raise


async def get_filtered_groups() -> List[List[Dict[str, Any]]]:
    """Fetch groups and filter out the excluded ones, returning them in batches."""
    groups = await telegram_client.list_my_groups()
    filtered = [g for g in groups if g["id"] not in GROUPS_TO_EXCLUDE]
    logger.info(f"Fetched {len(filtered)} groups after filtering.")
    return batch_groups(filtered, BATCH_SIZE)


async def summarize_group(group: Dict[str, Any]) -> Optional[str]:
    """Fetch recent messages from a group and generate a summary."""
    group_id = group["id"]
    group_name = group.get("name") or str(group_id)

    try:
        messages = await telegram_client.get_recent_messages(group_id)
        input_data = {"result": {group_name: messages}}
        summary = summarizer_V2.summarize_json_dict_as_string(input_data)
        logger.info(f"✅ Summarized group: {group_name}")
        return summary
    except Exception as e:
        logger.error(f"❌ Failed to summarize {group_name}: {e}")
        return None


def combine_batch_summaries(summaries: List[str]) -> str:
    """Combine individual group summaries into one batch summary."""
    prompt = PARTIAL_SUMMARIES_PROMPT.format(batch_summaries="\n\n".join(summaries))
    input_data = {"result": {"Batch Summary": [{"text": prompt}]}}
    return summarizer_V2.summarize_individual_batch(input_data)


def merge_with_existing_summary(existing: str, new: str) -> str:
    """Merge a new summary into the existing summary."""
    prompt = MERGE_EXISTING_SUMMARIES_PROMPT.format(existing=existing, new=new)
    input_data = {"result": {"Final Summary": [{"text": prompt}]}}
    return summarizer_V2.summarize_json_dict_as_string(input_data)


async def post_summary_to_telegram(summary: str, language_id: int) -> None:
    """Split and post summary to Telegram in the given language."""
    messages = summarizer_V2.split_summary_for_telegram(summary)
    for i, message in enumerate(messages, start=1):
        logger.info(f"msg #{i} [lang {language_id}]: {message[:100]}")
        post_to_telegram(message, language_id)


async def process_group_batches(batches: List[List[Dict[str, Any]]]) -> str:
    """Process all batches and return the final combined summary."""
    current_summary = ""

    for idx, batch in enumerate(batches, start=1):
        logger.info(f"Processing batch {idx}/{len(batches)}...")
        summaries = []

        for group in batch:
            summary = await summarize_group(group)
            if summary:
                summaries.append(summary)

        if not summaries:
            logger.warning(f"No valid summaries in batch {idx}. Skipping...")
            continue

        try:
            batch_summary = combine_batch_summaries(summaries)
            current_summary = (
                batch_summary if not current_summary else
                merge_with_existing_summary(current_summary, batch_summary)
            )
            logger.info(f"✅ Finished batch {idx}/{len(batches)}.")
        except Exception as e:
            logger.error(f"❌ Failed to combine batch {idx}: {e}")

        await asyncio.sleep(SLEEP_BETWEEN_BATCHES)

    return current_summary or "No groups or messages found for summarization."


async def run_summarization_pipeline() -> None:
    """Main pipeline for summarizing and posting Telegram news."""
    try:
        await initialize_telegram_client()
        batches = await get_filtered_groups()
        summary = await process_group_batches(batches)

        summary_he = summarizer_V2.translate_summary_to_telegram_hebrew(summary)
        await post_summary_to_telegram(summary_he, language_id=1)

        summary_ru = summarizer_V2.translate_summary_to_telegram_russian(summary)
        await post_summary_to_telegram(summary_ru, language_id=2)

        logger.info("✅ All summaries posted successfully.")

    except Exception as e:
        logger.exception(f"❌ Pipeline error: {e}")


def main() -> None:
    """Entrypoint."""
    asyncio.run(run_summarization_pipeline())


if __name__ == "__main__":
    main()
