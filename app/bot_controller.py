import asyncio
import json
import logging
from logging.handlers import RotatingFileHandler
from telethon import events
from app.auth_session import auth_session
from bot.logic import parse_bot_message, connect_to_sheet

log_path = "bot_logger.log"
handler = RotatingFileHandler(log_path, maxBytes=1_000_000, backupCount=3, encoding="utf-8")
formatter = logging.Formatter('[%(asctime)s] %(levelname)s: %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
handler.setFormatter(formatter)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.addHandler(handler)
logger.propagate = False

_bot_future = None
_bot_started = False


def start_bot():
    global _bot_future, _bot_started
    if _bot_started:
        return False

    client = auth_session.get_client()

    with open("bot_config.json", "r", encoding="utf-8") as f:
        cfg = json.load(f)

    bot_username = cfg["telegram"]["bot_username"]
    sheet_id = cfg["google_sheets"]["sheet_id"]
    sheet = connect_to_sheet(sheet_id, logger=logger)

    logger.info(f"📡 Ожидаем сообщения от @{bot_username}...")

    @client.on(events.NewMessage(from_users=bot_username))
    async def handler(event):
        logger.info("📥 Получено новое сообщение от бота")
        parsed = parse_bot_message(event.message.text, logger=logger)

        if parsed:
            sheet.append_row(parsed)
            logger.info(f"📊 Данные записаны в таблицу: {parsed}")
        else:
            logger.warning("⛔ Сообщение не записано — парсинг не удался.")

    async def _run_bot():
        if not client.is_connected():
            await client.connect()
        await client.run_until_disconnected()

    _bot_future = asyncio.run_coroutine_threadsafe(
        _run_bot(),
        auth_session.loop
    )

    _bot_started = True
    logger.info("✅ Бот успешно запущен")
    return True


def stop_bot():
    global _bot_future, _bot_started
    client = auth_session.get_client()

    if not _bot_started or not _bot_future:
        return False

    async def _shutdown_bot():
        if client.is_connected():
            await client.disconnect()

    try:
        future = asyncio.run_coroutine_threadsafe(
            _shutdown_bot(),
            auth_session.loop
        )
        future.result(timeout=5)
        _bot_started = False
        logger.info("🛑 Бот успешно остановлен.")
        return True
    except Exception as e:
        logger.error(f"❌ Ошибка при остановке бота: {e}")
        return False



def is_bot_running():
    return _bot_started and _bot_future and not _bot_future.done()
