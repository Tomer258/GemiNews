from telethon.sync import TelegramClient, events
from telethon.errors import SessionPasswordNeededError
from telethon.tl.functions.messages import GetHistoryRequest
from telethon.sessions import StringSession
from .config import API_ID, API_HASH, PHONE,PSWRD,STRING_SESSION
from telethon.tl.types import Channel, Chat


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
        dialogs = await self.client.get_dialogs()
        groups_and_channels = [
            {
                "id": dialog.entity.id,
                "name": dialog.name,
                "username": getattr(dialog.entity, "username", None),
                "type": (
                    "channel" if getattr(dialog.entity, "broadcast", False)
                    else "megagroup" if getattr(dialog.entity, "megagroup", False)
                    else "group"
                )
            }
            for dialog in dialogs
            if isinstance(dialog.entity, (Channel, Chat))
        ]

        return groups_and_channels
