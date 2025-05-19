from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError
import asyncio
import threading
import json

class TelegramAuthSession:
    def __init__(self):
        self.client = None
        self.status = "idle"
        self.config = {}
        self.loop = None
        self.loop_thread = None
        self._ensure_event_loop()

    def _ensure_event_loop(self):
        if not self.loop:
            self.loop = asyncio.new_event_loop()
            self.loop_thread = threading.Thread(target=self._start_loop, daemon=True)
            self.loop_thread.start()

    def _start_loop(self):
        asyncio.set_event_loop(self.loop)
        self.loop.run_forever()

    def load_config(self):
        with open("bot_config.json", "r", encoding="utf-8") as f:
            self.config = json.load(f)

    def get_client(self):
        self.load_config()
        if not self.client:
            api_id = int(self.config["telegram"]["api_id"])
            api_hash = self.config["telegram"]["api_hash"]
            self.client = TelegramClient("session", api_id, api_hash)
        return self.client

    def start_auth_flow(self):
        future = asyncio.run_coroutine_threadsafe(self._start_auth(), self.loop)
        return future.result()

    def sign_in_with_code(self, code):
        future = asyncio.run_coroutine_threadsafe(self._sign_in(code), self.loop)
        return future.result()

    def submit_2fa_password(self, password):
        future = asyncio.run_coroutine_threadsafe(self._sign_2fa(password), self.loop)
        return future.result()

    async def _start_auth(self):
        client = self.get_client()
        await client.connect()
        if not await client.is_user_authorized():
            await client.send_code_request(self.config["telegram"]["phone"])
            self.status = "awaiting_code"
        else:
            self.status = "ready"

    async def _sign_in(self, code: str):
        client = self.get_client()
        phone = self.config["telegram"]["phone"]
        try:
            await client.sign_in(phone=phone, code=code)
            self.status = "ready"
            return "success"
        except SessionPasswordNeededError:
            self.status = "awaiting_password"
            return "password_needed"
        except Exception as e:
            return f"error: {e}"

    async def _sign_2fa(self, password: str):
        client = self.get_client()
        try:
            await client.sign_in(password=password)
            self.status = "ready"
            return "success"
        except Exception as e:
            return f"error: {e}"

auth_session = TelegramAuthSession()
