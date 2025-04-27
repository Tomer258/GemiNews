from telethon.sync import TelegramClient
from telethon.errors import SessionPasswordNeededError
from telethon.sessions import StringSession
from .config import API_ID, API_HASH, PHONE,PSWRD,STRING_SESSION
from telethon.tl.types import Channel, Chat
from datetime import datetime, timezone, timedelta


class MyTelegramClient:
    def __init__(self):
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

    async def get_recent_messages(self, entity, hours=24):
        """
        Fetch messages from the last day for a given group/channel.
        """
        now = datetime.now(timezone.utc)
        since = now - timedelta(hours=hours)

        messages = []
        async for message in self.client.iter_messages(entity):
            if message.date < since:
                break  # No need to continue older messages
            if message.text:
                messages.append({
                    "id": message.id,
                    "text": message.text,
                    "date": message.date.isoformat()
                })

        return messages
