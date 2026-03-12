import threading
import asyncio
from telethon import TelegramClient, events
from telethon.errors import SessionPasswordNeededError
from unidecode import unidecode

class TelegramMonitorThread(threading.Thread):
    def __init__(self, api_id, api_hash, phone, callbacks):
        super().__init__()
        self.api_id = api_id
        self.api_hash = api_hash
        self.phone = phone
        self.callbacks = callbacks  # on_log, on_match, on_auth_needed, on_auth_success
        self.loop = asyncio.new_event_loop()
        self.client = None
        self.is_active = False
        self.keywords = []
        
        self._auth_event = threading.Event()
        self._auth_code = None
        self.daemon = True

    def run(self):
        asyncio.set_event_loop(self.loop)
        # Usa um arquivo de sessão local
        self.client = TelegramClient('session_monitor_gui', self.api_id, self.api_hash)
        self.loop.run_until_complete(self.async_run())

    async def async_run(self):
        try:
            await self.client.connect()
            
            # Autenticação
            if not await self.client.is_user_authorized():
                self.callbacks['on_log']("Solicitando código de login ao Telegram...")
                try:
                    await self.client.send_code_request(self.phone)
                    self.callbacks['on_auth_needed']()
                    
                    # Aguarda o usuário inserir o código na UI
                    while not self._auth_event.is_set():
                        await asyncio.sleep(0.5)
                    
                    if self._auth_code:
                        try:
                            await self.client.sign_in(self.phone, self._auth_code)
                            self.callbacks['on_log']("Login realizado com sucesso!")
                        except SessionPasswordNeededError:
                            self.callbacks['on_log']("Erro: Conta com Autenticação de Dois Fatores (2FA) não suportada nesta interface.")
                            return
                except Exception as e:
                    self.callbacks['on_log'](f"Erro na autenticação: {e}")
                    return
            
            self.callbacks['on_auth_success']()
            
            # Configura o manipulador de eventos
            @self.client.on(events.NewMessage)
            async def handler(event):
                if not self.is_active: return
                if event.is_private: return  # Ignora DMs
                
                # Remove acentos e converte tudo para minúsculo
                texto = unidecode(event.raw_text.lower())
                
                for regra in self.keywords:
                    # Remove acentos da regra também
                    regra_lower = unidecode(regra.lower())
                    
                    # Separa os blocos que precisam existir juntos (operador + / AND)
                    blocos_obrigatorios = regra_lower.split('+')
                    
                    regra_atendida = True
                    for bloco in blocos_obrigatorios:
                        # Dentro de cada bloco, verifica se há opções alternativas (operador / / OR)
                        opcoes = bloco.split('/')
                        
                        bloco_atendido = False
                        for opcao in opcoes:
                            if opcao.strip() in texto:
                                bloco_atendido = True
                                break
                        
                        # Se nenhuma das opções (separadas por /) do bloco (separado por +) foi encontrada, a regra falha
                        if not bloco_atendido:
                            regra_atendida = False
                            break
                            
                    if regra_atendida:
                        chat = await event.get_chat()
                        chat_name = getattr(chat, 'title', 'Chat Desconhecido')
                        self.callbacks['on_log'](f"[{chat_name}] Regra '{regra}' encontrada! Encaminhando...")
                        
                        try:
                            await event.forward_to('me')
                            self.callbacks['on_log']("-> Mensagem salva com sucesso.")
                            self.callbacks['on_match']()
                        except Exception as e:
                            self.callbacks['on_log'](f"-> Erro ao encaminhar: {e}")
                        
                        break # Evita múltiplos encaminhamentos da mesma mensagem
                        
            self.callbacks['on_log']("Iniciado e aguardando mensagens...")
            
            # Mantém rodando até desconectar
            await self.client.run_until_disconnected()
            
        except Exception as e:
            self.callbacks['on_log'](f"Erro fatal no cliente Telegram: {e}")

    def provide_code(self, code):
        """Método chamado pela interface gráfica para injetar o código OTP"""
        self._auth_code = code
        self._auth_event.set()
        
    def stop(self):
        """Encerra graciosamente a conexão e a thread"""
        if self.client and self.loop.is_running():
            self.loop.call_soon_threadsafe(self.client.disconnect)
