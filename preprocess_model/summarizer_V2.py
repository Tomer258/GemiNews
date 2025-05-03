import os
import json
from dotenv import load_dotenv
import google.generativeai as genai

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

The goal: create a high-quality, readable, and concise daily news summary without omitting any important details.
    '''

    full_prompt = f"{prompt}\n\nHere is the JSON file:\n\n{json_string}"
    response = model.generate_content(full_prompt)
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
    response = model.generate_content(full_prompt)
    return response.text

def translate_summary_to_telegram_hebrew(summary: str):
    """
    Translate an English news summary to fluent Hebrew and format it for Telegram.
    """
    if not isinstance(summary, str):
        raise TypeError("Expected a plain text summary as input.")

    prompt = '''\
Translate the following English news summary into fluent and professional Hebrew.
Make the format appropriate for a Telegram chat:
- Use short and clean paragraphs
- Include clear section headers
- Optional bullet points
- Keep it easy to read and not too formal

Summary:
'''

    full_prompt = f"{prompt}\n\n{summary}"

    response = model.generate_content(contents=full_prompt)

    return response.text


def get_models():
    """List available model names."""
    models = genai.list_models()
    model_names = [amodel.name for amodel in models]
    print(model_names)
    return model_names
