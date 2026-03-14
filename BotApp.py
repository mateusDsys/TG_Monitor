import customtkinter as ctk
import datetime
import webbrowser
import os
import threading
import csv
import sys
from tkinter import filedialog
from PIL import Image
import pystray
from pystray import MenuItem as item
from plyer import notification

from bot_config import load_config, save_config
from bot_audio import init_audio, play_sound
from bot_telegram import TelegramMonitorThread
from bot_db import init_db, get_history, clear_history, add_to_blacklist
from bot_discord import send_to_discord

# Configurações globais
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.title("TG Monitor Pro")
        self.geometry("1100x750")
        self.minsize(950, 650)
        
        init_db()
        self.config = load_config()
        init_audio()
        
        self.bot_thread = None
        self.tray_icon = None
        self.current_tab = "login"
        self.is_quitting = False
        
        # Grid Principal
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=0) # Sidebar
        self.grid_columnconfigure(1, weight=1) # Conteúdo
        
        self.build_sidebar()
        self.build_login_frame()
        self.build_main_frame()
        self.build_history_frame()
        self.build_channels_frame()
        self.build_integrations_frame()
        self.build_settings_frame()
        
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Iniciar na bandeja se o argumento --tray foi passado (Auto-start do Windows)
        if "--tray" in sys.argv:
            self.withdraw()
            self.create_tray()
            self.start_connection() # Conecta automaticamente
        else:
            # Lógica de Login Automático:
            # Se já temos as três credenciais básicas, pula a tela de login e tenta conectar
            if self.config.get("api_id") and self.config.get("api_hash") and self.config.get("phone"):
                self.show_frame("main")
                # Usa .after para deixar a janela principal renderizar antes de travar a thread
                self.after(500, self.start_connection)
            else:
                self.show_frame("login")
        
    def build_sidebar(self):
        self.sidebar = ctk.CTkFrame(self, width=220, corner_radius=0)
        self.sidebar.grid_rowconfigure(7, weight=1)
        
        self.logo = ctk.CTkLabel(self.sidebar, text="TG MONITOR PRO", font=ctk.CTkFont(size=20, weight="bold"))
        self.logo.grid(row=0, column=0, padx=20, pady=(30, 20))
        
        self.nav_buttons = {}
        items = [
            ("main", " Monitoramento"),
            ("history", " Histórico"),
            ("channels", " Canais/Filtros"),
            ("integrations", " Integrações"),
            ("settings", " Configurações")
        ]
        
        for i, (name, label) in enumerate(items):
            btn = ctk.CTkButton(self.sidebar, text=label, anchor="w", height=40,
                               command=lambda n=name: self.show_frame(n))
            btn.grid(row=i+1, column=0, padx=20, pady=5, sticky="ew")
            self.nav_buttons[name] = btn
            
        self.status_dot = ctk.CTkLabel(self.sidebar, text="● Desconectado", text_color="#FF6B6B", font=ctk.CTkFont(weight="bold"))
        self.status_dot.grid(row=6, column=0, padx=20, pady=(10, 5), sticky="s")
        
        self.btn_logoff = ctk.CTkButton(self.sidebar, text="Sair da Conta", fg_color="transparent", 
                                        text_color="#e74c3c", hover_color="#c0392b", height=30,
                                        command=self.perform_logoff)
        self.btn_logoff.grid(row=7, column=0, padx=20, pady=(0, 20), sticky="s")
        
    def build_login_frame(self):
        self.login_frame = ctk.CTkFrame(self, corner_radius=15)
        container = ctk.CTkFrame(self.login_frame, fg_color="transparent")
        container.place(relx=0.5, rely=0.5, anchor="center")
        
        ctk.CTkLabel(container, text="Autenticação", font=ctk.CTkFont(size=24, weight="bold")).pack(pady=10)
        ctk.CTkLabel(container, text="Insira suas credenciais de desenvolvedor do Telegram.", text_color="gray").pack(pady=(0, 20))
        
        self.entry_api_id = self.create_input(container, "API ID", self.config["api_id"])
        self.entry_api_hash = self.create_input(container, "API Hash", self.config["api_hash"])
        self.entry_phone = self.create_input(container, "Telefone (+55...)", self.config["phone"])
        
        self.btn_connect = ctk.CTkButton(container, text="Conectar", height=45, command=self.start_connection)
        self.btn_connect.pack(pady=20, fill="x")
        
        # Sub-frames de Auth
        self.auth_area = ctk.CTkFrame(container, fg_color="transparent")
        self.entry_code = ctk.CTkEntry(self.auth_area, placeholder_text="Código OTP", height=40)
        self.entry_code.pack(side="left", padx=5, fill="x", expand=True)
        ctk.CTkButton(self.auth_area, text="OK", width=60, height=40, command=self.verify_code).pack(side="right")
        
        self.twofa_area = ctk.CTkFrame(container, fg_color="transparent")
        self.entry_2fa = ctk.CTkEntry(self.twofa_area, placeholder_text="Senha 2FA", height=40)
        self.entry_2fa.pack(side="left", padx=5, fill="x", expand=True)
        ctk.CTkButton(self.twofa_area, text="Entrar", width=60, height=40, command=self.verify_2fa).pack(side="right")

    def create_input(self, parent, label, val, show=None):
        f = ctk.CTkFrame(parent, fg_color="transparent")
        f.pack(fill="x", pady=5)
        ctk.CTkLabel(f, text=label, font=ctk.CTkFont(weight="bold")).pack(anchor="w")
        e = ctk.CTkEntry(f, width=350, height=40, show=show)
        e.insert(0, val); e.pack(pady=2); return e

    def build_main_frame(self):
        self.main_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.main_frame.grid_columnconfigure(0, weight=1); self.main_frame.grid_columnconfigure(1, weight=2)
        self.main_frame.grid_rowconfigure(1, weight=1)
        
        header = ctk.CTkFrame(self.main_frame, corner_radius=10)
        header.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 20))
        
        self.switch_mon = ctk.CTkSwitch(header, text="Monitor Ativo", font=ctk.CTkFont(weight="bold"), 
                                      command=self.toggle_mon, progress_color="#2ecc71")
        if self.config["monitor_active"]: self.switch_mon.select()
        self.switch_mon.pack(side="left", padx=20, pady=15)
        
        self.switch_regex = ctk.CTkSwitch(header, text="Regex", command=self.save_gen_config)
        if self.config["regex_mode"]: self.switch_regex.select()
        self.switch_regex.pack(side="right", padx=20, pady=15)

        # Palavras
        p_frame = ctk.CTkFrame(self.main_frame, corner_radius=10)
        p_frame.grid(row=1, column=0, sticky="nsew", padx=(0, 10))
        ctk.CTkLabel(p_frame, text="Palavras-Chave", font=ctk.CTkFont(weight="bold")).pack(pady=10)
        
        entry_f = ctk.CTkFrame(p_frame, fg_color="transparent")
        entry_f.pack(fill="x", padx=10)
        self.entry_kw = ctk.CTkEntry(entry_f, placeholder_text="Add...")
        self.entry_kw.pack(side="left", fill="x", expand=True, padx=5)
        self.entry_kw.bind("<Return>", lambda e: self.add_kw())
        ctk.CTkButton(entry_f, text="+", width=40, command=self.add_kw).pack(side="right")
        
        self.kw_scroll = ctk.CTkScrollableFrame(p_frame, fg_color="transparent")
        self.kw_scroll.pack(fill="both", expand=True, padx=5, pady=10)
        self.render_kw()

        # Console
        c_frame = ctk.CTkFrame(self.main_frame, corner_radius=10)
        c_frame.grid(row=1, column=1, sticky="nsew", padx=(10, 0))
        
        c_header = ctk.CTkFrame(c_frame, fg_color="transparent")
        c_header.pack(fill="x", padx=10, pady=(10, 0))
        ctk.CTkLabel(c_header, text="Live Log", font=ctk.CTkFont(weight="bold")).pack(side="left")
        ctk.CTkButton(c_header, text="Limpar", width=60, height=24, fg_color="gray", command=self.clear_log).pack(side="right")
        
        self.log_box = ctk.CTkTextbox(c_frame, state="disabled", font=("Consolas", 12))
        self.log_box.pack(fill="both", expand=True, padx=10, pady=10)
        self.log_box.tag_config("match", foreground="#2ecc71")
        self.log_box.tag_config("sys", foreground="#3498db")

    def build_history_frame(self):
        self.history_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.history_frame.grid_rowconfigure(1, weight=1); self.history_frame.grid_columnconfigure(0, weight=1)
        
        h_header = ctk.CTkFrame(self.history_frame, corner_radius=10)
        h_header.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        
        ctk.CTkLabel(h_header, text="Histórico de Matches (Banco SQLite)", font=ctk.CTkFont(weight="bold")).pack(side="left", padx=20, pady=10)
        ctk.CTkButton(h_header, text="Limpar Tudo", fg_color="#e74c3c", width=100, command=self.clear_history_ui).pack(side="right", padx=10)
        ctk.CTkButton(h_header, text="Exportar CSV", fg_color="#27ae60", width=100, command=self.export_history).pack(side="right", padx=10)
        ctk.CTkButton(h_header, text="Atualizar", width=100, command=self.render_history).pack(side="right", padx=10)
        
        self.h_scroll = ctk.CTkScrollableFrame(self.history_frame, fg_color="transparent")
        self.h_scroll.grid(row=1, column=0, sticky="nsew")

    def build_integrations_frame(self):
        self.integrations_frame = ctk.CTkFrame(self, fg_color="transparent")
        c = ctk.CTkFrame(self.integrations_frame, corner_radius=15)
        c.pack(fill="both", expand=True, padx=50, pady=50)
        
        ctk.CTkLabel(c, text="Integração com Discord", font=ctk.CTkFont(size=20, weight="bold"), text_color="#5865F2").pack(pady=(20, 5))
        ctk.CTkLabel(c, text="Receba alertas bonitos no seu celular ou servidor através de Webhooks.", text_color="gray").pack(pady=(0, 20))
        
        frame_hook = ctk.CTkFrame(c, fg_color="transparent")
        frame_hook.pack(fill="x", padx=40, pady=10)
        
        ctk.CTkLabel(frame_hook, text="URL do Webhook:", font=ctk.CTkFont(weight="bold")).pack(anchor="w")
        self.entry_discord = ctk.CTkEntry(frame_hook, placeholder_text="https://discord.com/api/webhooks/...", height=40)
        self.entry_discord.insert(0, self.config.get("discord_webhook", ""))
        self.entry_discord.pack(fill="x", pady=5)
        
        btn_frame = ctk.CTkFrame(c, fg_color="transparent")
        btn_frame.pack(fill="x", padx=40, pady=20)
        
        ctk.CTkButton(btn_frame, text="Salvar URL", command=self.save_integrations).pack(side="left")
        ctk.CTkButton(btn_frame, text="Testar Conexão", fg_color="#5865F2", command=self.test_discord).pack(side="left", padx=10)
        
    def save_integrations(self):
        self.config["discord_webhook"] = self.entry_discord.get().strip()
        save_config(self.config)
        self.add_log("Webhook do Discord salvo.", "sys")
        
    def test_discord(self):
        url = self.entry_discord.get().strip()
        if not url:
            self.add_log("Erro: Insira uma URL de Webhook primeiro.", "error")
            return
            
        self.add_log("Enviando teste para o Discord...", "sys")
        success = send_to_discord(url, "TESTE", "Sistema TG Monitor", "Se você está lendo isso, a integração com o Discord está funcionando perfeitamente! 🎉")
        
        if success:
            self.add_log("Teste do Discord enviado com sucesso!", "match")
        else:
            self.add_log("Falha ao enviar teste pro Discord. Verifique a URL.", "error")

    def build_channels_frame(self):
        self.channels_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.channels_frame.grid_columnconfigure((0,1), weight=1); self.channels_frame.grid_rowconfigure(2, weight=1)
        
        # Cabeçalho com o botão de buscar canais
        header = ctk.CTkFrame(self.channels_frame, fg_color="transparent")
        header.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(10, 0))
        
        ctk.CTkLabel(header, text="Filtros de Canais", font=ctk.CTkFont(size=18, weight="bold")).pack(side="left", padx=20)
        
        self.btn_load_dialogs = ctk.CTkButton(header, text="Listar Meus Canais (Descobrir IDs)", fg_color="#8e44ad", 
                                              command=self.load_dialogs)
        self.btn_load_dialogs.pack(side="right", padx=20)
        
        ctk.CTkLabel(self.channels_frame, text="Adicione IDs de canais abaixo para filtrar.", text_color="gray").grid(row=1, column=0, columnspan=2, pady=(0, 10))
        
        self.build_list_panel(self.channels_frame, "Whitelist (Monitorar APENAS estes)", "whitelist_channels", 0, 2)
        self.build_list_panel(self.channels_frame, "Blacklist (IGNORAR estes)", "blacklist_channels", 1, 2)

    def build_list_panel(self, parent, title, config_key, col, row):
        frame = ctk.CTkFrame(parent, corner_radius=10)
        frame.grid(row=row, column=col, sticky="nsew", padx=10, pady=10)
        ctk.CTkLabel(frame, text=title, font=ctk.CTkFont(weight="bold")).pack(pady=10)
        
        add_f = ctk.CTkFrame(frame, fg_color="transparent")
        add_f.pack(fill="x", padx=10)
        entry = ctk.CTkEntry(add_f, placeholder_text="ID do canal (ex: -100...)")
        entry.pack(side="left", fill="x", expand=True, padx=5)
        ctk.CTkButton(add_f, text="+", width=40, command=lambda e=entry, k=config_key: self.add_id(e, k)).pack(side="right")
        
        scroll = ctk.CTkScrollableFrame(frame, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=5, pady=10)
        setattr(self, f"scroll_{config_key}", scroll)
        self.render_ids(config_key)

    def build_settings_frame(self):
        self.settings_frame = ctk.CTkFrame(self, fg_color="transparent")
        c = ctk.CTkFrame(self.settings_frame, corner_radius=15)
        c.pack(fill="both", expand=True, padx=50, pady=50)
        
        ctk.CTkLabel(c, text="Preferências Avançadas", font=ctk.CTkFont(size=20, weight="bold")).pack(pady=20)
        
        self.sw_sound = self.create_sw(c, "Som", "notifications", "enabled")
        self.sw_toast = self.create_sw(c, "Notificação Windows", "notifications", "desktop")
        self.sw_tray = self.create_sw(c, "Minimizar ao fechar (Bandeja)", None, "minimize_to_tray")
        self.sw_recon = self.create_sw(c, "Auto-reconexão inteligente", None, "auto_reconnect")
        self.sw_startup = self.create_sw(c, "Iniciar com o Windows (Auto-Start)", None, "start_with_windows")
        
        ctk.CTkLabel(c, text="Volume", font=ctk.CTkFont(weight="bold")).pack(pady=(15,0))
        self.sl_vol = ctk.CTkSlider(c, from_=0, to=1, command=self.save_adv)
        self.sl_vol.set(self.config["notifications"]["volume"]); self.sl_vol.pack(pady=5, fill="x", padx=100)
        
        ctk.CTkLabel(c, text="Anti-Spam (Segundos entre repetições)", font=ctk.CTkFont(weight="bold")).pack(pady=(15,0))
        self.sl_spam = ctk.CTkSlider(c, from_=0, to=600, number_of_steps=60, command=self.save_adv)
        self.sl_spam.set(self.config["anti_spam_seconds"]); self.sl_spam.pack(pady=5, fill="x", padx=100)
        self.spam_val = ctk.CTkLabel(c, text=f"{int(self.config['anti_spam_seconds'])}s"); self.spam_val.pack()

        ctk.CTkLabel(c, text="Tipo de Som", font=ctk.CTkFont(weight="bold")).pack(pady=(15, 5))
        lista_sons = ["Som 1 (Beep)", "Som 2 (Alerta)", "Som 3 (Suave)", "Som 4 (Sino)", "Som 5 (Urgente)"]
        self.combo_sound = ctk.CTkOptionMenu(c, values=lista_sons, command=self.test_sound, width=250)
        self.combo_sound.set(self.config["notifications"]["sound"])
        self.combo_sound.pack(pady=5)

    def test_sound(self, _):
        self.save_adv()
        play_sound(self.config["notifications"]["sound"], self.config["notifications"]["volume"])

    def create_sw(self, p, t, s, k):
        sw = ctk.CTkSwitch(p, text=t, command=self.save_adv)
        v = self.config[s][k] if s else self.config[k]
        if v: sw.select()
        sw.pack(pady=8, anchor="w", padx=100)
        return sw

    def perform_logoff(self):
        """Limpa as credenciais, encerra a sessão e volta para a tela de login."""
        # 1. Apaga do config local
        self.config["api_id"] = ""
        self.config["api_hash"] = ""
        self.config["phone"] = ""
        save_config(self.config)
        
        # 2. Apaga a sessão física do Telethon se existir
        if os.path.exists("session_monitor_gui.session"):
            try: os.remove("session_monitor_gui.session")
            except: pass
            
        # 3. Para a thread atual do bot
        if self.bot_thread:
            self.bot_thread.stop()
            self.bot_thread = None
            
        # 4. Atualiza a UI para a tela de login
        self.status_dot.configure(text="● Desconectado", text_color="#FF6B6B")
        
        # Limpa os campos visuais de login
        self.entry_api_id.delete(0, "end")
        self.entry_api_hash.delete(0, "end")
        self.entry_phone.delete(0, "end")
        self.entry_code.delete(0, "end")
        self.entry_2fa.delete(0, "end")
        
        self.btn_connect.configure(state="normal", text="Conectar")
        self.auth_area.pack_forget()
        self.twofa_area.pack_forget()
        self.btn_connect.pack(pady=20, fill="x")
        
        self.show_frame("login")
        self.add_log("Logoff realizado com sucesso.", "sys")

    # --- LÓGICA ---
    def show_frame(self, name):
        for f in [self.login_frame, self.main_frame, self.history_frame, self.channels_frame, self.integrations_frame, self.settings_frame]: 
            f.grid_forget()
        
        self.current_tab = name
        if name == "login": self.sidebar.grid_forget(); self.login_frame.grid(row=0, column=0, columnspan=2, sticky="nsew", padx=100, pady=50)
        else:
            self.sidebar.grid(row=0, column=0, sticky="nsew")
            getattr(self, f"{name}_frame").grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
            for k, btn in self.nav_buttons.items(): btn.configure(fg_color=("#3B8ED0", "#1F6AA5") if k == name else "transparent")
            if name == "history": self.render_history()

    def start_connection(self):
        self.config.update({"api_id": self.entry_api_id.get(), "api_hash": self.entry_api_hash.get(), "phone": self.entry_phone.get()})
        save_config(self.config)
        self.btn_connect.configure(state="disabled", text="Conectando...")
        
        cbs = {
            'on_log': lambda m: self.after(0, self.add_log, m),
            'on_match': lambda r, c, s, l=None: self.after(0, self.on_match, r, c, s, l),
            'on_auth_needed': lambda: self.after(0, lambda: self.auth_area.pack(pady=10)),
            'on_2fa_needed': lambda: self.after(0, lambda: [self.auth_area.pack_forget(), self.twofa_area.pack(pady=10)]),
            'on_auth_success': lambda: self.after(0, self.on_success),
            'on_dialogs_loaded': lambda d: self.after(0, self.show_dialogs_popup, d)
        }
        self.bot_thread = TelegramMonitorThread(self.config["api_id"], self.config["api_hash"], self.config["phone"], cbs, self.config)
        self.bot_thread.keywords = self.config["keywords"]; self.bot_thread.is_active = self.config["monitor_active"]
        self.bot_thread.start()

    def on_success(self):
        self.status_dot.configure(text="● Online", text_color="#2ecc71")
        if self.current_tab == "login":
            self.show_frame("main")
        
    def add_log(self, m, tag=None):
        if not tag:
            tag = "match" if "Match" in m else "sys" if ">>" in m else None
        
        self.log_box.configure(state="normal")
        self.log_box.insert("end", f"[{datetime.datetime.now().strftime('%H:%M:%S')}] {m}\n", tag)
        
        # Limita o console em ~500 linhas para não pesar a memória UI
        lines = int(self.log_box.index('end-1c').split('.')[0])
        if lines > 500:
            self.log_box.delete("1.0", f"{lines-500}.0")
            
        self.log_box.see("end")
        self.log_box.configure(state="disabled")
        
    def clear_log(self):
        self.log_box.configure(state="normal")
        self.log_box.delete("1.0", "end")
        self.log_box.configure(state="disabled")

    def on_match(self, rule, chat, snippet, link=None):
        self.config["stats"][rule] = self.config["stats"].get(rule, 0) + 1
        save_config(self.config); self.render_kw()
        if self.config["notifications"]["enabled"]: play_sound(self.config["notifications"]["sound"], self.config["notifications"]["volume"])
        if self.config["notifications"]["desktop"]:
            try: notification.notify(title=f"Match: {rule}", message=f"Grupo: {chat}\n{snippet}", app_name="TG Monitor", timeout=5)
            except: pass
            
        # Integração Discord
        discord_url = self.config.get("discord_webhook", "")
        if discord_url:
            threading.Thread(target=send_to_discord, args=(discord_url, rule, chat, snippet, link), daemon=True).start()
            
        if self.current_tab == "history": self.render_history()

    def render_history(self):
        for w in self.h_scroll.winfo_children(): w.destroy()
        data = get_history(50)
        for r in data:
            f = ctk.CTkFrame(self.h_scroll, fg_color=("gray85", "gray15"))
            f.pack(fill="x", pady=2, padx=5)
            t = r['timestamp'].split('.')[0]
            ctk.CTkLabel(f, text=f"[{t}]", font=("Consolas", 10), text_color="gray").pack(side="left", padx=5)
            ctk.CTkLabel(f, text=f" {r['rule']} ", fg_color="#3498db", corner_radius=5).pack(side="left", padx=5)
            ctk.CTkLabel(f, text=f" {r['chat_name']} ", font=ctk.CTkFont(weight="bold")).pack(side="left", padx=5)
            
            txt = r['message_text'][:80].replace('\n', ' ') + "..."
            lbl_txt = ctk.CTkLabel(f, text=txt, text_color="gray", cursor="hand2")
            lbl_txt.pack(side="left", padx=5, fill="x", expand=True)
            lbl_txt.bind("<Button-1>", lambda e, r_rule=r['rule'], c_name=r['chat_name'], m_txt=r['message_text']: self.show_full_message(r_rule, c_name, m_txt))

    def show_full_message(self, rule, chat_name, full_text):
        top = ctk.CTkToplevel(self)
        top.title(f"Match: {rule}")
        top.geometry("600x450")
        top.minsize(400, 300)
        top.attributes("-topmost", True)
        top.focus_force()
        ctk.CTkLabel(top, text=f"Grupo: {chat_name}", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=10, padx=20, anchor="w")
        txt_box = ctk.CTkTextbox(top, font=("Consolas", 13), wrap="word")
        txt_box.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        txt_box.insert("1.0", full_text)
        txt_box.configure(state="disabled")

    def export_history(self):
        path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV", "*.csv")])
        if path:
            data = get_history(1000)
            if not data: return
            with open(path, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.DictWriter(f, fieldnames=data[0].keys())
                writer.writeheader(); writer.writerows(data)

    def clear_history_ui(self):
        clear_history(); self.render_history()

    # --- Canais e Filtros ---
    def load_dialogs(self):
        if not self.bot_thread or not self.bot_thread.is_alive():
            self.add_log("Erro: Conecte o bot primeiro antes de buscar canais.", "error")
            return
        
        self.btn_load_dialogs.configure(state="disabled", text="Buscando...")
        self.bot_thread.request_dialogs()

    def show_dialogs_popup(self, dialogs):
        self.btn_load_dialogs.configure(state="normal", text="Listar Meus Canais (Descobrir IDs)")
        
        top = ctk.CTkToplevel(self)
        top.title("Seus Canais e Grupos")
        top.geometry("700x500")
        top.attributes("-topmost", True)
        top.focus_force()
        
        ctk.CTkLabel(top, text="Selecione onde deseja adicionar os IDs:", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=10)
        
        scroll = ctk.CTkScrollableFrame(top)
        scroll.pack(fill="both", expand=True, padx=10, pady=10)
        
        for d in dialogs:
            f = ctk.CTkFrame(scroll)
            f.pack(fill="x", pady=2)
            
            # Limita tamanho do título
            title = d['title'][:40] + "..." if len(d['title']) > 40 else d['title']
            
            ctk.CTkLabel(f, text=title, font=ctk.CTkFont(weight="bold"), width=300, anchor="w").pack(side="left", padx=10, pady=5)
            ctk.CTkLabel(f, text=str(d['id']), text_color="gray").pack(side="left", padx=10)
            
            ctk.CTkButton(f, text="Add Blacklist", width=100, fg_color="#e74c3c", 
                          command=lambda i=d['id'], t=top: self.quick_add_id(i, "blacklist_channels", t)).pack(side="right", padx=5)
            ctk.CTkButton(f, text="Add Whitelist", width=100, fg_color="#2ecc71", 
                          command=lambda i=d['id'], t=top: self.quick_add_id(i, "whitelist_channels", t)).pack(side="right", padx=5)

    def quick_add_id(self, channel_id, config_key, top_window):
        if channel_id not in self.config[config_key]:
            self.config[config_key].append(channel_id)
            save_config(self.config)
            self.render_ids(config_key)
            self.add_log(f"ID {channel_id} adicionado à {config_key}")
        
    def render_ids(self, key):
        s = getattr(self, f"scroll_{key}")
        for w in s.winfo_children(): w.destroy()
        for i in self.config[key]:
            f = ctk.CTkFrame(s, fg_color=("gray85", "gray15"))
            f.pack(fill="x", pady=2)
            ctk.CTkLabel(f, text=str(i)).pack(side="left", padx=10)
            ctk.CTkButton(f, text="X", width=25, height=25, fg_color="#e74c3c", command=lambda v=i, k=key: self.rem_id(v, k)).pack(side="right", padx=5)

    def add_id(self, e, k):
        try: i = int(e.get().strip())
        except: return
        if i not in self.config[k]: 
            self.config[k].append(i); save_config(self.config); e.delete(0, "end"); self.render_ids(k)

    def rem_id(self, v, k):
        self.config[k].remove(v); save_config(self.config); self.render_ids(k)

    # --- Palavras Chave ---
    def render_kw(self):
        for w in self.kw_scroll.winfo_children(): w.destroy()
        for kw in self.config["keywords"]:
            c = self.config["stats"].get(kw, 0)
            f = ctk.CTkFrame(self.kw_scroll, fg_color=("gray85", "gray15"))
            f.pack(fill="x", pady=2)
            ctk.CTkLabel(f, text=kw).pack(side="left", padx=10)
            if c: ctk.CTkLabel(f, text=str(c), fg_color="#3498db", width=20, corner_radius=10).pack(side="left")
            ctk.CTkButton(f, text="X", width=25, height=25, fg_color="#e74c3c", command=lambda k=kw: self.rem_kw(k)).pack(side="right", padx=5)

    def add_kw(self):
        v = self.entry_kw.get().strip(); 
        if not self.config["regex_mode"]: v = v.lower()
        if v and v not in self.config["keywords"]:
            self.config["keywords"].append(v); save_config(self.config); self.entry_kw.delete(0, "end"); self.render_kw()
            if self.bot_thread: self.bot_thread.keywords = self.config["keywords"]

    def rem_kw(self, k):
        self.config["keywords"].remove(k); self.config["stats"].pop(k, None); save_config(self.config); self.render_kw()
        if self.bot_thread: self.bot_thread.keywords = self.config["keywords"]

    # --- Controles ---
    def toggle_mon(self, state=None):
        if state is not None:
            v = state
            if v: self.switch_mon.select()
            else: self.switch_mon.deselect()
        else:
            v = self.switch_mon.get() == 1
            
        self.config["monitor_active"] = v; save_config(self.config)
        if self.bot_thread: self.bot_thread.is_active = v
        self.add_log(f"Monitoramento {'ATIVADO' if v else 'PAUSADO'} via controle.")

    def save_gen_config(self):
        self.config["regex_mode"] = self.switch_regex.get() == 1; save_config(self.config)
        if self.bot_thread: self.bot_thread.regex_mode = self.config["regex_mode"]

    def save_adv(self, _=None):
        self.config["notifications"]["enabled"] = self.sw_sound.get() == 1
        self.config["notifications"]["desktop"] = self.sw_toast.get() == 1
        self.config["minimize_to_tray"] = self.sw_tray.get() == 1
        self.config["auto_reconnect"] = self.sw_recon.get() == 1
        self.config["start_with_windows"] = self.sw_startup.get() == 1
        self.config["notifications"]["volume"] = self.sl_vol.get()
        self.config["anti_spam_seconds"] = int(self.sl_spam.get())
        self.config["notifications"]["sound"] = self.combo_sound.get()
        self.spam_val.configure(text=f"{int(self.config['anti_spam_seconds'])}s")
        save_config(self.config)

    def verify_code(self): 
        if self.bot_thread: self.bot_thread.provide_code(self.entry_code.get())
    def verify_2fa(self): 
        if self.bot_thread: self.bot_thread.provide_password(self.entry_2fa.get())

    def on_closing(self):
        if self.config.get("minimize_to_tray"):
            self.withdraw()
            if not self.tray_icon: self.create_tray()
        else: self.quit_app()

    def create_tray(self):
        img = Image.new('RGB', (64, 64), color=(59, 142, 208))
        m = pystray.Menu(
            item('Abrir Interface', self.show_window_safe, default=True),
            pystray.Menu.SEPARATOR,
            item('Pausar Monitoramento', self.pause_from_tray, checked=lambda i: not self.config["monitor_active"]),
            item('Retomar Monitoramento', self.resume_from_tray, checked=lambda i: self.config["monitor_active"]),
            pystray.Menu.SEPARATOR,
            item('Sair Completamente', self.quit_app_safe)
        )
        self.tray_icon = pystray.Icon("TGMonitor", img, "TG Monitor Pro", m)
        threading.Thread(target=self.tray_icon.run, daemon=True).start()

    def pause_from_tray(self, icon, item):
        self.after(0, lambda: self.toggle_mon(False))
        
    def resume_from_tray(self, icon, item):
        self.after(0, lambda: self.toggle_mon(True))

    def show_window_safe(self, _=None):
        self.after(0, self.deiconify)
        self.after(50, self.focus_force)

    def quit_app_safe(self, _=None):
        self.after(0, self.quit_app)

    def quit_app(self):
        if self.is_quitting: return
        self.is_quitting = True
        if self.bot_thread: self.bot_thread.stop()
        if self.tray_icon: self.tray_icon.stop()
        self.destroy()
        sys.exit(0)

if __name__ == "__main__":
    app = App(); app.mainloop()
