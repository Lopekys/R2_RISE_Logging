import json
from pathlib import Path

CONFIG_PATH = Path('bot_config.json')

DEFAULT_CONFIG = {
    "telegram": {
        "api_id": "",
        "api_hash": "",
        "phone": "",
        "bot_username": ""
    },
    "google_sheets": {
        "sheet_id": ""
    }
}


def load_config():
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    return DEFAULT_CONFIG.copy()


def save_config(config):
    with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=4, ensure_ascii=False)
