import threading
import asyncio
import re
import time
from telethon import TelegramClient, events
from telethon.errors import SessionPasswordNeededError
from unidecode import unidecode
from bot_db import save_match, get_blacklist

class TelegramMonitorThread(threading.Thread):
    def __init__(self, api_id, api_hash, phone, callbacks, config):
        super().__init__()
        self.api_id = api_id
        self.api_hash = api_hash
        self.phone = phone
        self.callbacks = callbacks  # on_log, on_match, on_auth_needed, on_auth_success, on_2fa_needed, on_dialogs_loaded
        self.config = config
        
        self.loop = asyncio.new_event_loop()
        self.client = None
        self.is_active = False
        self.keywords = []
        self.regex_mode = config.get("regex_mode", False)
        
        self.recent_matches = {} 
        
        self._auth_event = threading.Event()
        self._auth_code = None
        self._auth_password = None
        self._is_2fa = False
        
        # Evento para solicitar os canais assincronamente
        self._request_dialogs = False
        
        self.daemon = True

    def request_dialogs(self):
        """Agenda a busca de diálogos no loop de eventos em execução."""
        if self.client and self.loop.is_running():
            asyncio.run_coroutine_threadsafe(self._fetch_dialogs_async(), self.loop)

    async def _fetch_dialogs_async(self):
        """Busca os diálogos e envia para a interface via callback."""
        try:
            self.callbacks['on_log']("Buscando lista de canais...")
            dialogs = await self.client.get_dialogs()
            channels = []
            
            for dialog in dialogs:
                if dialog.is_channel or dialog.is_group:
                    channels.append({
                        "id": dialog.id,
                        "title": dialog.title
                    })
            
            # Ordena alfabeticamente
            channels.sort(key=lambda x: x["title"].lower())
            
            if 'on_dialogs_loaded' in self.callbacks:
                self.callbacks['on_dialogs_loaded'](channels)
            
            self.callbacks['on_log'](f"{len(channels)} canais/grupos encontrados.")
            
        except Exception as e:
            self.callbacks['on_log'](f"Erro ao buscar canais: {e}")
        finally:
            self._request_dialogs = False

    def run(self):
        asyncio.set_event_loop(self.loop)
        self.client = TelegramClient('session_monitor_gui', self.api_id, self.api_hash)
        
        while True:
            try:
                self.loop.run_until_complete(self.async_run())
            except Exception as e:
                self.callbacks['on_log'](f"Conexão perdida. Reconectando em 10s... ({e})")
                time.sleep(10)
            else:
                break

    async def async_run(self):
        try:
            await self.client.connect()
            
            if not await self.client.is_user_authorized():
                self.callbacks['on_log']("Solicitando código de login ao Telegram...")
                await self.client.send_code_request(self.phone)
                self.callbacks['on_auth_needed']()
                
                while not self._auth_event.is_set():
                    await asyncio.sleep(0.5)
                
                if self._auth_code and not self._is_2fa:
                    try:
                        await self.client.sign_in(self.phone, self._auth_code)
                    except SessionPasswordNeededError:
                        self.callbacks['on_log']("Conta protegida por 2FA.")
                        self._auth_event.clear()
                        self._is_2fa = True
                        self.callbacks['on_2fa_needed']()
                        
                        while not self._auth_event.is_set():
                            await asyncio.sleep(0.5)
                            
                        if self._auth_password:
                            await self.client.sign_in(password=self._auth_password)
            
            self.callbacks['on_auth_success']()
            
            @self.client.on(events.NewMessage)
            async def handler(event):
                if not self.is_active: return
                if event.is_private: return
                
                chat = await event.get_chat()
                chat_id = getattr(chat, 'id', 0)
                
                whitelist = self.config.get("whitelist_channels", [])
                blacklist = self.config.get("blacklist_channels", [])
                
                if whitelist and chat_id not in whitelist: return
                if blacklist and chat_id in blacklist: return
                
                sender = await event.get_sender()
                sender_id = getattr(sender, 'id', 0)
                if sender_id in get_blacklist(): return
                
                texto = event.raw_text
                texto_unidecode = unidecode(texto.lower())
                
                for regra in self.keywords:
                    match_found = False
                    if self.regex_mode:
                        try:
                            # PROTEÇÃO: Ignora erros de Regex caso o usuário digite algo inválido
                            if re.search(regra, texto, re.IGNORECASE): match_found = True
                        except re.error:
                            pass 
                    else:
                        regra_lower = unidecode(regra.lower())
                        blocos = regra_lower.split('+')
                        match_found = True
                        for b in blocos:
                            opcoes = b.split('/')
                            if not any(o.strip() in texto_unidecode for o in opcoes):
                                match_found = False; break
                                
                    if match_found:
                        agora = time.time()
                        limite_spam = self.config.get("anti_spam_seconds", 60)
                        
                        # ANTI-SPAM (Memory Leak Fix): 
                        # Limpa hashes velhos do dicionário antes de checar para a memória RAM não explodir
                        self.recent_matches = {k: v for k, v in self.recent_matches.items() if agora - v < limite_spam}
                        
                        msg_hash = hash(texto)
                        is_duplicate = False
                        if msg_hash in self.recent_matches:
                            is_duplicate = True
                        
                        self.recent_matches[msg_hash] = agora
                        
                        chat_name = getattr(chat, 'title', 'Chat Desconhecido')
                        sender_name = getattr(sender, 'first_name', 'Desconhecido')
                        if getattr(sender, 'last_name', ''): sender_name += f" {sender.last_name}"
                        
                        # Tenta gerar o link clicável da mensagem para facilitar o acesso
                        msg_link = ""
                        if getattr(chat, 'username', None):
                            msg_link = f"https://t.me/{chat.username}/{event.id}"
                        else:
                            # Grupos/Canais privados usam o prefixo 'c/ID' (removendo o -100)
                            raw_id = abs(chat_id)
                            if str(raw_id).startswith("100"):
                                raw_id = int(str(raw_id)[3:])
                            msg_link = f"https://t.me/c/{raw_id}/{event.id}"
                        
                        save_match(regra, chat_name, chat_id, sender_name, sender_id, texto, is_duplicate)
                        
                        if not is_duplicate:
                            self.callbacks['on_log'](f"[{chat_name}] Match: '{regra}'")
                            try:
                                await event.forward_to('me')
                                snippet = texto[:100].replace('\n', ' ') + ('...' if len(texto) > 100 else '')
                                self.callbacks['on_match'](regra, chat_name, snippet, msg_link)
                            except Exception as e:
                                self.callbacks['on_log'](f"Erro ao encaminhar: {e}")
                        
                        break
                        
            self.callbacks['on_log']("Monitoramento ativo e inteligente iniciado.")
            await self.client.run_until_disconnected()
            
        except Exception as e:
            self.callbacks['on_log'](f"Erro no monitor: {e}")
            raise e

    def provide_code(self, code):
        self._auth_code = code
        self._auth_event.set()
        
    def provide_password(self, password):
        self._auth_password = password
        self._auth_event.set()
        
    def stop(self):
        if self.client:
            try:
                self.client.disconnect()
            except: pass
        if self.loop.is_running():
            self.loop.stop()
