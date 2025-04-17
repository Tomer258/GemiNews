import os
from dotenv import load_dotenv


def hello():
    return 'this is the scraper here!!'

def load_scraper():
    load_dotenv()
    api_id = int(os.getenv("API_ID"))
    api_hash = os.getenv("API_HASH")
    print('yo')
    print(f"API ID: {api_id}, API HASH: {api_hash[:5]}***")