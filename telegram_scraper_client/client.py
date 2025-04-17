from telethon.sync import TelegramClient,events
from telethon.tl.functions.messages import GetHistoryRequest
from .config import API_ID,API_HASH,PHONE



class MyTelegramClient:

    def __init__(self, session_name="session"):
        self.client = TelegramClient(session_name,API_ID,API_HASH)

    def start(self):
        self.client.start()

    def stop(self):
        self.client.disconnect()

    def listen_to_group(self, group_name):
        @self.client.on(events.NewMessage(chats=group_name))
        async def handler(event):
            print(f"[{event.chat.title}] {event.sender_id}: {event.raw_text}")

        self.client.loop.run_until_complete(self.client.connect())
        if not self.client.is_user_authorized():
            self.client.loop.run_until_complete(self.client.sign_in())

        print(f"Listening to group '{group_name}'")
        self.client.loop.run_forever()

    def list_my_groups(self):
        async def _fetch():
            groups = []
            async for dialog in self.client.iter_dialogs():
                if dialog.is_group or dialog.is_channel and dialog.entity.megagroup:
                    groups.append({
                        "name": dialog.name,
                        "id": dialog.id,
                        "username": getattr(dialog.entity, 'username', None)
                    })
            return groups

        return self.client.loop.run_until_complete(_fetch())