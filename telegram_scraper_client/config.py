import os
from dotenv import load_dotenv

load_dotenv()

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
PSWRD = os.getenv("PSWRD")
PHONE = os.getenv("PHONE")
STRING_SESSION = os.getenv("STRING_SESSION")
