import json
import os

CONFIG_FILE = "config.json"

DEFAULT_CONFIG = {
    "api_id": "",
    "api_hash": "",
    "phone": "",
    "keywords": ["urgente", "vaga", "promoção", "desconto", "comprar"],
    "notifications": {
        "enabled": True,
        "volume": 0.5,
        "sound": "Som 1 (Beep)"
    },
    "monitor_active": True
}

def load_config():
    if not os.path.exists(CONFIG_FILE):
        save_config(DEFAULT_CONFIG)
        return DEFAULT_CONFIG
    
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except Exception:
            return DEFAULT_CONFIG

def save_config(config):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=4, ensure_ascii=False)
