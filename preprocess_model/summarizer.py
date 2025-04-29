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
    אני אשלח לך קובץ JSON המכיל הודעות חדשות ממספר ערוצים. כל הודעה כוללת טקסט, תאריך ולעיתים מזהה. תפקידך הוא לסכם את המידע בנקודות עיקריות, בצורה מדויקת, ברורה ומסודרת.

הוראות הסיכום:

1. חלק את הסיכום לקטגוריות ברורות, לפי התחומים הבאים (אם יש מידע רלוונטי):
   - פוליטיקה בישראל
   - ביטחון ומלחמה (בארץ ובאזור)
   - פשיעה ואירועים פליליים
   - אירועים ביטוחניים (אסונות, תשתיות, סייבר)
   - חדשות כלליות בישראל
   - חדשות חוץ ועולם
   - צבע אדום – מיקום, תדירות, ופרטים אם ידועים

2. הסר חזרות במידע – אין צורך לציין שוב את אותו אירוע או דמות במספר מקומות, אלא אם מדובר בהקשר שונה לגמרי.

3. סדר את המידע לפי חשיבות – פרטים קריטיים ובולטים יופיעו ראשונים בכל קטגוריה, אירועים משניים או שוליים יופיעו אחרונים או בקצרה.

4. שמור על אחידות – אם יש פרטי נפגעים או מספרים, ציין אותם באופן עקבי ככל האפשר. אם לא ידוע, אל תנחש – כתוב "לא פורסם".

5. הימנע ממידע טכני לא רלוונטי (כמו מזהים, ניסוחים לא ברורים, קיצורים לא מוסברים).

6. כתוב בעברית תקנית, בהירה ועניינית. אפשר להשתמש בבולטים, אך במבנה נוח לקריאה ולא רשימה גולמית.

7. הדגש אירועים חריגים במיוחד, התפתחויות חריפות, שינויי מדיניות, מינויי מפתח או אסונות משמעותיים.

המטרה היא לייצר סיכום חדשות יומי איכותי, מדויק, קצר יחסית, וקל להבנה עבור הקוראים, בלי לפספס מידע חשוב.
    '''

    # Combine the Hebrew prompt + JSON string
    full_prompt = f"{prompt}\n\nהנה הקובץ:\n\n{json_string}"

    # Send to Gemini
    response = model.generate_content(full_prompt)

    return response.text
