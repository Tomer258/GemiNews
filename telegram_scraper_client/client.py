from telethon.sync import TelegramClient, events
from telethon.errors import SessionPasswordNeededError
from telethon.tl.functions.messages import GetHistoryRequest
from .config import API_ID, API_HASH, PHONE,PSWRD


class MyTelegramClient:
    def __init__(self, session_name="session"):
        self.client = TelegramClient(session_name, API_ID, API_HASH)

    def start(self):
        self.client.connect()

        if not self.client.is_user_authorized():
            print("[!] Requesting login code...")
            sent = self.client.send_code_request(PHONE)  # only once
            code = input("Enter the code sent to your Telegram app: ").strip()

            try:
                self.client.sign_in(phone=PHONE, code=code, phone_code_hash=sent.phone_code_hash)
            except SessionPasswordNeededError:
                self.client.sign_in(password=PSWRD)

        print("[+] Logged in successfully.")

    def stop(self):
        self.client.disconnect()

    def listen_to_group(self, group_name):
        @self.client.on(events.NewMessage(chats=group_name))
        async def handler(event):
            print(f"[{event.chat.title}] {event.sender_id}: {event.raw_text}")

        self.client.loop.run_until_complete(self.client.connect())

        if not self.client.is_user_authorized():
            raise Exception("Client not authorized. Call start() first.")

        print(f"Listening to group '{group_name}'...")
        self.client.run_until_disconnected()

    def list_my_groups(self):
        async def _fetch():
            groups = []
            async for dialog in self.client.iter_dialogs():
                if dialog.is_group or (dialog.is_channel and dialog.entity.megagroup):
                    groups.append({
                        "name": dialog.name,
                        "id": dialog.id,
                        "username": getattr(dialog.entity, 'username', None)
                    })
            return groups

        return self.client.loop.run_until_complete(_fetch())
