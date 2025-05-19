import datetime
import re
import gspread
from oauth2client.service_account import ServiceAccountCredentials

HEADERS = ["Character", "Item", "Count", "Price", "Left", "Silver", "Date", "Time"]


def parse_bot_message(message: str, logger=None) -> list:
    try:
        character = re.search(r'Персонаж (\w+)', message).group(1)
        item_match = re.search(r'у вас (.+?) \((\d+) шт\.\)', message)
        price = re.search(r'за ([\d,]+) серебра', message).group(1)
        left = re.search(r'Осталось ([\d,]+) шт', message).group(1)
        silver = re.search(r'Серебро: ([\d,]+)', message).group(1)

        item_name = item_match.group(1)
        item_count = item_match.group(2)

        now = datetime.datetime.now()
        date_str = now.strftime('%Y-%m-%d')
        time_str = now.strftime('%H:%M:%S')

        parsed = [
            character,
            item_name,
            item_count,
            price,
            left.replace(',', ''),
            silver.replace(',', ''),
            date_str,
            time_str
        ]

        if logger:
            logger.info(f"✅ Успешно разобрано сообщение: {parsed}")

        return parsed

    except Exception as e:
        if logger:
            logger.error(f"❌ Ошибка разбора сообщения: {e} | Исходный текст: {message}")
        return None


def connect_to_sheet(sheet_id: str, logger=None):
    scope = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
    client = gspread.authorize(creds)
    sheet = client.open_by_key(sheet_id).sheet1

    first_row = sheet.row_values(1)
    if first_row != HEADERS:
        sheet.insert_row(HEADERS, 1)
        if logger:
            logger.info("📋 Заголовки таблицы добавлены.")

    if logger:
        logger.info(f"📊 Подключено к Google Sheets (ID: {sheet_id})")

    return sheet
