import json
import os
import shutil
import winshell
from win32com.client import Dispatch
import sys

CONFIG_FILE = "config.json"
BACKUP_FILE = "config.bak"

DEFAULT_CONFIG = {
    "api_id": "",
    "api_hash": "",
    "phone": "",
    "keywords": ["urgente", "vaga", "promoção", "desconto", "comprar"],
    "regex_mode": False,
    "minimize_to_tray": False,
    "auto_reconnect": True,
    "anti_spam_seconds": 60,
    "start_with_windows": False,
    "discord_webhook": "",
    "notifications": {
        "enabled": True,
        "desktop": True,
        "volume": 0.5,
        "sound": "Som 1 (Beep)"
    },
    "monitor_active": True,
    "whitelist_channels": [],
    "blacklist_channels": [],
    "stats": {}
}

def manage_windows_startup(enable):
    """Cria ou remove o atalho de inicialização na pasta Startup do Windows."""
    startup_path = winshell.startup()
    shortcut_path = os.path.join(startup_path, "TG_Monitor.lnk")
    
    if enable:
        try:
            # Aponta para o interpretador python rodando o script atual silenciosamente
            python_exe = sys.executable
            script_path = os.path.abspath("BotApp.py")
            
            shell = Dispatch('WScript.Shell')
            shortcut = shell.CreateShortCut(shortcut_path)
            shortcut.Targetpath = python_exe
            # Usa pythonw.exe para não abrir o console preto (terminal) se possível
            if "python.exe" in python_exe.lower():
                pythonw_exe = python_exe.lower().replace("python.exe", "pythonw.exe")
                if os.path.exists(pythonw_exe):
                    shortcut.Targetpath = pythonw_exe
                    
            shortcut.Arguments = f'"{script_path}" --tray' # Passa argumento para iniciar minimizado
            shortcut.WorkingDirectory = os.path.abspath(os.path.dirname(script_path))
            shortcut.IconLocation = python_exe
            shortcut.save()
        except Exception as e:
            print(f"Erro ao criar atalho de inicialização: {e}")
    else:
        if os.path.exists(shortcut_path):
            try: os.remove(shortcut_path)
            except: pass

def load_config():
    if not os.path.exists(CONFIG_FILE):
        save_config(DEFAULT_CONFIG)
        return DEFAULT_CONFIG.copy()
    
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        try:
            config = json.load(f)
            changed = False
            for key, value in DEFAULT_CONFIG.items():
                if key not in config:
                    config[key] = value
                    changed = True
            
            # Limpa valores antigos se estiverem criptografados (Fernet tokens começam com 'gAAAAA')
            if isinstance(config.get("api_hash"), str) and config["api_hash"].startswith("gAAAAA"):
                config["api_hash"] = ""
            if isinstance(config.get("phone"), str) and config["phone"].startswith("gAAAAA"):
                config["phone"] = ""
            
            # Garante que o estado do atalho condiz com a config
            manage_windows_startup(config.get("start_with_windows", False))
            
            if changed: save_config(config)
            return config
        except Exception:
            return DEFAULT_CONFIG.copy()

def save_config(config_to_save):
    config = config_to_save.copy()
    
    if os.path.exists(CONFIG_FILE):
        shutil.copy2(CONFIG_FILE, BACKUP_FILE)
        
    # Atualiza o Windows Startup
    manage_windows_startup(config.get("start_with_windows", False))
    
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=4, ensure_ascii=False)
