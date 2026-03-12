import customtkinter as ctk
import datetime
import webbrowser
from bot_config import load_config, save_config
from bot_audio import init_audio, play_sound
from bot_telegram import TelegramMonitorThread

# Configurações globais do tema
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.title("TG Monitor")
        self.geometry("950x650")
        self.minsize(800, 500)
        
        self.config = load_config()
        init_audio()
        
        self.bot_thread = None
        
        # Estrutura principal da Janela (Grid)
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=0) # Sidebar
        self.grid_columnconfigure(1, weight=1) # Conteúdo principal
        
        # Constrói as views
        self.build_sidebar()
        self.build_login_frame()
        self.build_main_frame()
        self.build_settings_frame()
        
        # Evento para fechar a janela graciosamente
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Mostra a tela de Login inicialmente
        self.show_frame("login")
        
    def build_sidebar(self):
        self.sidebar = ctk.CTkFrame(self, width=220, corner_radius=0)
        self.sidebar.grid_rowconfigure(4, weight=1)
        
        # Logo / Título
        self.logo = ctk.CTkLabel(self.sidebar, text="TG Monitor", font=ctk.CTkFont(size=22, weight="bold"))
        self.logo.grid(row=0, column=0, padx=20, pady=(30, 20))
        
        # Botões de Navegação
        self.btn_nav_monitor = ctk.CTkButton(self.sidebar, text=" Monitoramento", anchor="w",
                                             command=lambda: self.show_frame("main"), height=40)
        self.btn_nav_monitor.grid(row=1, column=0, padx=20, pady=10, sticky="ew")
        
        self.btn_nav_settings = ctk.CTkButton(self.sidebar, text=" Configurações", anchor="w",
                                              command=lambda: self.show_frame("settings"), height=40)
        self.btn_nav_settings.grid(row=2, column=0, padx=20, pady=10, sticky="ew")
        
        # Status na parte inferior
        self.status_label = ctk.CTkLabel(self.sidebar, text="Status: Desconectado", text_color="#FF6B6B", font=ctk.CTkFont(weight="bold"))
        self.status_label.grid(row=4, column=0, padx=20, pady=30, sticky="s")
        
    def build_login_frame(self):
        self.login_frame = ctk.CTkFrame(self, corner_radius=15)
        
        # Container centralizado
        container = ctk.CTkFrame(self.login_frame, fg_color="transparent")
        container.place(relx=0.5, rely=0.5, anchor="center")
        
        ctk.CTkLabel(container, text="Acesso à API do Telegram", font=ctk.CTkFont(size=24, weight="bold")).pack(pady=(0, 5))
        
        instrucoes = "Para utilizar o sistema, você precisa de credenciais de desenvolvedor do Telegram.\nObtenha seu API ID e API Hash acessando:"
        ctk.CTkLabel(container, text=instrucoes, text_color="gray", font=ctk.CTkFont(size=12)).pack(pady=(0, 0))
        
        link_api = ctk.CTkLabel(container, text="https://my.telegram.org", text_color="#3B8ED0", cursor="hand2", font=ctk.CTkFont(size=12, underline=True))
        link_api.pack(pady=(0, 20))
        link_api.bind("<Button-1>", lambda e: webbrowser.open_new_tab("https://my.telegram.org"))
        
        # API ID
        frame_id = ctk.CTkFrame(container, fg_color="transparent")
        frame_id.pack(fill="x", pady=5)
        ctk.CTkLabel(frame_id, text="API ID:", font=ctk.CTkFont(weight="bold")).pack(anchor="w")
        self.entry_api_id = ctk.CTkEntry(frame_id, placeholder_text="Ex: 1234567", width=350, height=40)
        self.entry_api_id.insert(0, self.config.get("api_id", ""))
        self.entry_api_id.pack(pady=(2, 0))
        
        # API Hash
        frame_hash = ctk.CTkFrame(container, fg_color="transparent")
        frame_hash.pack(fill="x", pady=5)
        ctk.CTkLabel(frame_hash, text="API Hash:", font=ctk.CTkFont(weight="bold")).pack(anchor="w")
        self.entry_api_hash = ctk.CTkEntry(frame_hash, placeholder_text="Sua chave longa (letras e números)", width=350, height=40)
        self.entry_api_hash.insert(0, self.config.get("api_hash", ""))
        self.entry_api_hash.pack(pady=(2, 0))
        
        # Telefone
        frame_phone = ctk.CTkFrame(container, fg_color="transparent")
        frame_phone.pack(fill="x", pady=5)
        ctk.CTkLabel(frame_phone, text="Número de Telefone:", font=ctk.CTkFont(weight="bold")).pack(anchor="w")
        self.entry_phone = ctk.CTkEntry(frame_phone, placeholder_text="Ex: +5511999999999 (com código do país)", width=350, height=40)
        self.entry_phone.insert(0, self.config.get("phone", ""))
        self.entry_phone.pack(pady=(2, 0))
        
        self.btn_connect = ctk.CTkButton(container, text="Conectar e Iniciar", width=350, height=45,
                                         font=ctk.CTkFont(weight="bold"), command=self.start_connection)
        self.btn_connect.pack(pady=(20, 10))
        
        # Frame oculto para código de autenticação (OTP)
        self.auth_frame = ctk.CTkFrame(container, fg_color="transparent")
        ctk.CTkLabel(self.auth_frame, text="Insira o código recebido no Telegram/SMS:", font=ctk.CTkFont(weight="bold")).pack(anchor="w", pady=(10, 5))
        
        code_container = ctk.CTkFrame(self.auth_frame, fg_color="transparent")
        code_container.pack(fill="x")
        self.entry_code = ctk.CTkEntry(code_container, placeholder_text="Código", width=200, height=40)
        self.entry_code.pack(side="left", padx=(0, 10))
        
        self.btn_verify = ctk.CTkButton(code_container, text="Verificar", width=140, height=40, command=self.verify_code)
        self.btn_verify.pack(side="right")
        
    def build_main_frame(self):
        self.main_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.main_frame.grid_columnconfigure(0, weight=1) # Palavras-chave
        self.main_frame.grid_columnconfigure(1, weight=2) # Logs
        self.main_frame.grid_rowconfigure(1, weight=1)
        
        # Header - Switch Ativar/Desativar Monitor
        header = ctk.CTkFrame(self.main_frame, corner_radius=10)
        header.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 20))
        
        self.switch_monitor = ctk.CTkSwitch(header, text="Monitoramento Ativado", font=ctk.CTkFont(size=16, weight="bold"),
                                            command=self.toggle_monitor, progress_color="#2ecc71")
        if self.config.get("monitor_active", True):
            self.switch_monitor.select()
        self.switch_monitor.pack(side="left", padx=20, pady=15)
        
        # --- Painel Esquerdo: Palavras-chave ---
        kw_frame = ctk.CTkFrame(self.main_frame, corner_radius=10)
        kw_frame.grid(row=1, column=0, sticky="nsew", padx=(0, 10))
        
        ctk.CTkLabel(kw_frame, text="Palavras-Chave Monitoradas", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(15, 10))
        
        add_frame = ctk.CTkFrame(kw_frame, fg_color="transparent")
        add_frame.pack(fill="x", padx=15, pady=5)
        
        self.entry_kw = ctk.CTkEntry(add_frame, placeholder_text="Nova palavra...")
        self.entry_kw.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.entry_kw.bind("<Return>", lambda event: self.add_keyword()) # Permite dar Enter
        
        ctk.CTkButton(add_frame, text="Add", width=50, command=self.add_keyword).pack(side="right")
        
        self.kw_scroll = ctk.CTkScrollableFrame(kw_frame, fg_color="transparent")
        self.kw_scroll.pack(fill="both", expand=True, padx=10, pady=10)
        self.render_keywords()
        
        # --- Painel Direito: Logs ---
        log_frame = ctk.CTkFrame(self.main_frame, corner_radius=10)
        log_frame.grid(row=1, column=1, sticky="nsew", padx=(10, 0))
        
        ctk.CTkLabel(log_frame, text="Console de Execução", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(15, 10))
        
        self.log_box = ctk.CTkTextbox(log_frame, state="disabled", font=ctk.CTkFont(family="Consolas", size=13))
        self.log_box.pack(fill="both", expand=True, padx=15, pady=(0, 15))
        
    def build_settings_frame(self):
        self.settings_frame = ctk.CTkFrame(self, fg_color="transparent")
        
        container = ctk.CTkFrame(self.settings_frame, corner_radius=15)
        container.pack(fill="both", expand=True)
        
        ctk.CTkLabel(container, text="Configurações de Notificação", font=ctk.CTkFont(size=20, weight="bold")).pack(pady=(30, 30))
        
        # Ativar som
        self.switch_notif = ctk.CTkSwitch(container, text="Emitir som ao encontrar palavra-chave", 
                                          font=ctk.CTkFont(size=15), command=self.save_settings)
        if self.config["notifications"]["enabled"]:
            self.switch_notif.select()
        self.switch_notif.pack(pady=10, padx=40, anchor="w")
        
        # Volume
        ctk.CTkLabel(container, text="Volume da Notificação", font=ctk.CTkFont(weight="bold")).pack(pady=(20, 5), padx=40, anchor="w")
        self.slider_volume = ctk.CTkSlider(container, from_=0.0, to=1.0, command=self.save_settings)
        self.slider_volume.set(self.config["notifications"]["volume"])
        self.slider_volume.pack(pady=5, padx=40, anchor="w", fill="x")
        
        # Som
        ctk.CTkLabel(container, text="Tipo de Som", font=ctk.CTkFont(weight="bold")).pack(pady=(20, 5), padx=40, anchor="w")
        
        lista_sons = ["Som 1 (Beep)", "Som 2 (Alerta)", "Som 3 (Suave)", "Som 4 (Sino)", "Som 5 (Urgente)"]
        
        self.combo_sound = ctk.CTkOptionMenu(container, values=lista_sons, 
                                             command=self.test_sound, width=250)
        
        # Garante que o som salvo no config existe na nova lista, senão usa o padrão
        som_atual = self.config["notifications"]["sound"]
        if som_atual not in lista_sons:
            som_atual = lista_sons[0]
            
        self.combo_sound.set(som_atual)
        self.combo_sound.pack(pady=5, padx=40, anchor="w")
        
        ctk.CTkLabel(container, text="(Altere o som para testá-lo)", text_color="gray").pack(padx=40, anchor="w")

    # --- Navegação ---
    def show_frame(self, name):
        self.login_frame.grid_forget()
        self.main_frame.grid_forget()
        self.settings_frame.grid_forget()
        
        if name == "login":
            self.sidebar.grid_forget()
            self.login_frame.grid(row=0, column=0, columnspan=2, sticky="nsew", padx=100, pady=100)
        else:
            self.sidebar.grid(row=0, column=0, sticky="nsew")
            if name == "main":
                self.btn_nav_monitor.configure(fg_color=["#3B8ED0", "#1F6AA5"])
                self.btn_nav_settings.configure(fg_color="transparent")
                self.main_frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
            elif name == "settings":
                self.btn_nav_settings.configure(fg_color=["#3B8ED0", "#1F6AA5"])
                self.btn_nav_monitor.configure(fg_color="transparent")
                self.settings_frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)

    # --- Lógica de Negócio ---
    def start_connection(self):
        # Salva credenciais preenchidas
        self.config["api_id"] = self.entry_api_id.get().strip()
        self.config["api_hash"] = self.entry_api_hash.get().strip()
        self.config["phone"] = self.entry_phone.get().strip()
        save_config(self.config)
        
        try:
            api_id = int(self.config["api_id"])
        except ValueError:
            self.btn_connect.configure(text="Erro: API ID inválido", fg_color="red")
            self.after(2000, lambda: self.btn_connect.configure(text="Conectar e Iniciar", fg_color=["#3B8ED0", "#1F6AA5"]))
            return
            
        self.btn_connect.configure(state="disabled", text="Conectando...")
        
        # Mapeia callbacks usando after() para ser thread-safe na GUI
        callbacks = {
            'on_log': lambda msg: self.after(0, self.add_log, msg),
            'on_match': lambda: self.after(0, self.trigger_notification),
            'on_auth_needed': lambda: self.after(0, self.show_code_input),
            'on_auth_success': lambda: self.after(0, self.on_auth_success)
        }
        
        self.bot_thread = TelegramMonitorThread(api_id, self.config["api_hash"], self.config["phone"], callbacks)
        self.bot_thread.keywords = list(self.config["keywords"])
        self.bot_thread.is_active = self.config["monitor_active"]
        self.bot_thread.start()
        
    def show_code_input(self):
        self.btn_connect.pack_forget()
        self.auth_frame.pack(pady=(20, 10))
        self.add_log("Aguardando inserção de código de verificação.")
        
    def verify_code(self):
        code = self.entry_code.get().strip()
        if code and self.bot_thread:
            self.btn_verify.configure(state="disabled", text="Verificando...")
            self.bot_thread.provide_code(code)
            
    def on_auth_success(self):
        self.status_label.configure(text="Status: Conectado", text_color="#2ecc71")
        self.show_frame("main")
        self.add_log(">> Interface gráfica iniciada. Monitorando.")
        
    def add_log(self, msg):
        time_str = datetime.datetime.now().strftime("%H:%M:%S")
        full_msg = f"[{time_str}] {msg}\n"
        
        self.log_box.configure(state="normal")
        self.log_box.insert("end", full_msg)
        self.log_box.see("end") # Auto-scroll
        self.log_box.configure(state="disabled")
        
    def trigger_notification(self):
        if self.config["notifications"]["enabled"]:
            play_sound(self.config["notifications"]["sound"], self.config["notifications"]["volume"])
            
    def toggle_monitor(self):
        is_active = self.switch_monitor.get() == 1
        self.config["monitor_active"] = is_active
        save_config(self.config)
        
        if self.bot_thread:
            self.bot_thread.is_active = is_active
            estado = "ATIVADO" if is_active else "DESATIVADO"
            self.add_log(f"--- Monitoramento {estado} ---")
            
    # --- Palavras-Chave ---
    def render_keywords(self):
        # Limpa widgets atuais
        for widget in self.kw_scroll.winfo_children():
            widget.destroy()
            
        for kw in self.config["keywords"]:
            frame = ctk.CTkFrame(self.kw_scroll, fg_color=("gray80", "gray20"))
            frame.pack(fill="x", pady=3)
            
            ctk.CTkLabel(frame, text=kw, font=ctk.CTkFont(size=14)).pack(side="left", padx=15, pady=8)
            
            btn = ctk.CTkButton(frame, text="X", width=28, height=28, fg_color="#E74C3C", hover_color="#C0392B",
                                font=ctk.CTkFont(weight="bold"), command=lambda k=kw: self.remove_keyword(k))
            btn.pack(side="right", padx=10)
            
    def add_keyword(self):
        kw = self.entry_kw.get().strip().lower()
        if kw and kw not in self.config["keywords"]:
            self.config["keywords"].append(kw)
            save_config(self.config)
            
            self.entry_kw.delete(0, "end")
            self.render_keywords()
            
            if self.bot_thread:
                self.bot_thread.keywords = list(self.config["keywords"])
                self.add_log(f"Palavra adicionada: '{kw}'")
                
    def remove_keyword(self, kw):
        if kw in self.config["keywords"]:
            self.config["keywords"].remove(kw)
            save_config(self.config)
            self.render_keywords()
            
            if self.bot_thread:
                self.bot_thread.keywords = list(self.config["keywords"])
                self.add_log(f"Palavra removida: '{kw}'")
                
    # --- Configurações ---
    def save_settings(self, _=None):
        self.config["notifications"]["enabled"] = self.switch_notif.get() == 1
        self.config["notifications"]["volume"] = self.slider_volume.get()
        self.config["notifications"]["sound"] = self.combo_sound.get()
        save_config(self.config)
        
    def test_sound(self, choice):
        self.save_settings()
        self.trigger_notification()

    def on_closing(self):
        """Encerra a thread do Telegram antes de fechar a janela"""
        if self.bot_thread:
            self.bot_thread.stop()
        self.destroy()

if __name__ == "__main__":
    app = App()
    app.mainloop()
