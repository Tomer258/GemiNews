import os
import json
from dotenv import load_dotenv
import google.generativeai as genai
import ast


# Load environment variables
load_dotenv()

# Get API key
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise ValueError("GEMINI_API_KEY not found in .env file")

# Configure the Gemini client
genai.configure(api_key=api_key)

# Load the model
model = genai.GenerativeModel("gemini-2.0-flash")
model2 = genai.GenerativeModel("gemini-1.5-flash")
model3 = genai.GenerativeModel("gemini-2.5-flash-preview-05-20")

def summarize_json_dict_as_string(data: dict):
    """Summarize a full JSON dictionary representing multi-channel news updates."""
    if not isinstance(data, dict):
        raise TypeError("Expected a Python dict object.")

    json_string = json.dumps(data, ensure_ascii=False)

    prompt = '''\
You will receive a JSON file containing news messages from various sources. Each message includes text, a timestamp, and sometimes an identifier. Your task is to summarize the content accurately and clearly, using the following guidelines:

1. Organize the summary into these categories (if applicable):
   - Politics in Israel
   - Security and War (Israel only)
   - Crime and Criminal Events (Israel only)
   - General News in Israel
   - Foreign and International News
   - Rocket or missile fire into Israeli territory

2. Remove duplicate reports. Each event should appear only once.

3. Prioritize key events first in each category. Less important items may be brief or appear later.

4. Use consistent formatting. If injury counts or other numbers are included, ensure clarity. If unknown, write “Not published.”

5. Exclude technical or irrelevant details (e.g., message IDs, unclear abbreviations).

6. Use clean, proper English. Bullet points are okay but format them clearly for readability.

7. Highlight major or exceptional events, serious developments, policy changes, key appointments, or significant disasters.

8. If an update relates to an event older than 24 hours, mention that explicitly.

9. dont give main headline. only the topics headlines!

The goal: create a high-quality, readable, and concise daily news summary without omitting any important details.
    '''

    full_prompt = f"{prompt}\n\nHere is the JSON file:\n\n{json_string}"
    response = model3.generate_content(full_prompt)
    return response.text


def summarize_individual_batch(data: dict):
    """Quick summary of messages from a single news source."""
    if not isinstance(data, dict):
        raise TypeError("Expected a Python dict object.")

    json_string = json.dumps(data, ensure_ascii=False)

    prompt = '''\
You are given a JSON file with messages from a news source. Summarize each topic clearly and briefly in a single sentence.
Avoid duplicates, write proper English, and focus on the core message.
    '''

    full_prompt = f"{prompt}\n\nHere is the JSON file:\n\n{json_string}"
    response = model3.generate_content(full_prompt)
    return response.text


def split_summary_for_telegram(summary_text: str) -> list[str]:
    prompt = (
        "Take the following summary and split it into separate Telegram messages. Each message should: "
        "Be under 4000 characters. "
        "Be structured clearly with headings and bullet points. "
        "Use Markdown formatting supported by Telegram (like **bold** and *italics*). "
        "Group items by topic. "
        "Format in a way suitable for direct posting in a Telegram channel. "
        "keep only headlines that are related to a topic and not general headlines. "
        "Return the messages as an array of strings. "
        "Return only text, no Python functions or code at all. "
        "Separate messages with a line containing only three dashes (---). "
        "Include *all* relevant items for the topic in one message, without unnecessary splitting (i.e., avoid creating multiple 'continuation' messages for the same topic)"
        "Here is the summary:\n\n"
        + summary_text
    )

    response = model.generate_content(prompt)

    # Split the response by "---"
    messages = [msg.strip() for msg in response.text.split('---') if msg.strip()]
    return messages


def get_models():
    """List available model names."""
    models = genai.list_models()
    model_names = [amodel.name for amodel in models]
    print(model_names)
    return model_names

def translate_summary_to_hebrew_and_russian(summary: str, delimiter: str = "---DELIMITER---") :
    """
    Translates an English summary to Hebrew and Russian using Gemini.
    Returns a single string with translations separated by the given delimiter.
    """
    if not isinstance(summary, str):
        raise TypeError("Expected a plain text summary as input.")

    base_prompt = f"""You are a professional translator fluent in English, Hebrew, and Russian.

Translate the following English news summary into both:
1. Hebrew
2. Russian

Return the result as a plain text with the two translations, separated by this delimiter: {delimiter}

Formatting:
- Short, clean paragraphs
- Section headers if applicable
- Bullet points when helpful
- Suitable for Telegram: readable, clear, friendly tone

Do NOT include any explanation, Markdown, list syntax, or extra formatting. Just the two translations separated by the delimiter.

Summary to translate:
"""

    full_prompt = f"{base_prompt}\n\n{summary}"

    response = model3.generate_content(full_prompt)
    parts = response.text.strip().split(delimiter, maxsplit=1)
    if len(parts) == 2:
        hebrew, russian = parts
        return hebrew.strip(), russian.strip()

    return "", ""