from telethon.sync import TelegramClient, events
from telethon.errors import SessionPasswordNeededError
from telethon.tl.functions.messages import GetHistoryRequest
from telethon.sessions import StringSession
from .config import API_ID, API_HASH, PHONE,PSWRD,STRING_SESSION


class MyTelegramClient:
    def __init__(self, session_name="session"):
        self.client = TelegramClient(StringSession(STRING_SESSION), API_ID, API_HASH)

    async def start(self):
        print(">>> Connecting to Telegram...")
        await self.client.connect()

        if not await self.client.is_user_authorized():
            print("[!] Requesting login code...")
            sent = await self.client.send_code_request(PHONE)
            code = input("Enter the code sent to your Telegram app: ").strip()

            try:
                await self.client.sign_in(phone=PHONE, password=PSWRD, code=code, phone_code_hash=sent.phone_code_hash)
            except SessionPasswordNeededError:
                await self.client.sign_in(password=PSWRD)
        else:
            print("[+] Logged in successfully.")



    def stop(self):
        self.client.disconnect()


    async def list_my_groups(self):
        print(">>> Fetching groups...")
        dialogs = await self.client.get_dialogs()
        return [
            {"id": d.id, "name": d.name}
            for d in dialogs if d.is_group
        ]
