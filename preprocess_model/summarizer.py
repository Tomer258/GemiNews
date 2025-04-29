import os
import google.generativeai as genai
from dotenv import load_dotenv
import json

# Load environment variables
load_dotenv()

# Configure Gemini API
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise ValueError("GEMINI_API_KEY not found in .env file")

genai.configure(api_key=api_key)

# Load Gemini model
model = genai.GenerativeModel('gemini-1.5-flash-latest')

def summarize_json_dict_as_string(data: dict):
    """Summarize the full JSON dictionary by sending it as a big JSON string."""

    if not isinstance(data, dict):
        raise TypeError("Expected a Python dict object.")

    # Convert the entire Python dict to a JSON string
    json_string = json.dumps(data, ensure_ascii=False)

    # Create the prompt in Hebrew
    prompt = '''\
    אני אשלח לך קובץ JSON שמכיל הודעות חדשות ממספר ערוצים.
    כל הודעה מכילה תאריך, טקסט, ולעיתים גם מזהה.
    סכם את כל ההודעות בנקודות עיקריות בצורה ברורה ומסודרת.
    בתשובה שלך חלק את הסיכום לחלקים לדוגמה:מידע על פוליטיקה, מידע על אירועים ביטוחניים,
    מידע על אירוע פשיעה,אירועים כלליים בעולם, כמות אזעקות צבע אדום באותו יום ומאיפה, אירועים חשובים במלחמה או בפן הבטחוני.
    המידע חייב להיות כתוב בצורה ברורה וקריאה וחשוב שלא ישארו פיסות מידע חשובות מאחור.
    תתמקד בפרטי האירועים החשובים ביותר ובדמויות המרכזיות.
    אין צורך לפרט מידע טכני שאינו רלוונטי.
    '''

    # Combine the Hebrew prompt + JSON string
    full_prompt = f"{prompt}\n\nהנה הקובץ:\n\n{json_string}"

    # Send to Gemini
    response = model.generate_content(full_prompt)

    return response.text
