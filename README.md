# TG Monitor

O **TG Monitor** é uma aplicação desktop desenvolvida em Python que monitora seus grupos e canais do Telegram em tempo real. Ele busca por palavras-chave (com suporte a regras compostas e ignorando acentos) e, ao encontrar uma correspondência, encaminha a mensagem automaticamente para as suas "Mensagens Salvas" e emite um alerta sonoro.

Ideal para monitorar promoções, vagas de emprego, alertas de servidores ou qualquer assunto do seu interesse sem precisar ficar lendo todos os grupos o tempo todo.

## 🚀 Funcionalidades

* **Interface Gráfica Moderna (GUI):** Desenvolvida com CustomTkinter para um visual escuro (Dark Mode) e amigável.
* **Monitoramento em Segundo Plano:** Utiliza threads assíncronas para não travar a interface enquanto monitora as mensagens.
* **Regras de Busca Avançadas:**
  * Ignora letras maiúsculas/minúsculas.
  * **Ignora acentuação** (ex: buscar "basico" encontra "básico").
  * **Operador E (`+`):** Buscar `iphone+15` exige que as duas palavras estejam na mensagem.
  * **Operador OU (`/`):** Buscar `vt9+pro/basico` exige a palavra "vt9" E ("pro" OU "basico").
* **Notificações Sonoras (Alertas):**
  * Sintetizador próprio gerando áudios limpos e de alto volume (dispensa downloads extras de áudio).
  * 5 tipos de toques disponíveis (Beep, Alerta, Suave, Sino e Urgente).
  * Controle de volume e ativação global integrados.
* **Sistema de Sessão:** Após o primeiro login, a sessão fica salva (usando `Telethon`), não necessitando do código OTP nas próximas inicializações.

---

## 🛠️ Tecnologias Utilizadas

* **[Python 3.x](https://www.python.org/)** - Linguagem principal.
* **[CustomTkinter](https://github.com/TomSchimansky/CustomTkinter)** - Interface gráfica moderna.
* **[Telethon](https://docs.telethon.dev/)** - Interação assíncrona com a API nativa do Telegram.
* **[Pygame](https://www.pygame.org/)** - Renderização e mixagem dos efeitos de áudio.
* **[Unidecode](https://pypi.org/project/Unidecode/)** - Tratamento de textos e remoção de acentos para a busca otimizada.

---

## ⚙️ Como Instalar e Rodar

### Pré-requisitos
Você precisa do Python instalado em sua máquina.

1. **Clone o repositório:**
```bash
git clone https://github.com/mateusDsys/TG-Monitor.git
cd TG-Monitor
```

2. **Instale as dependências:**
```bash
pip install customtkinter telethon pygame unidecode
```

3. **Execute a aplicação:**
```bash
python BotApp.py
```

### Onde encontro meu API ID e API Hash?
Para que o bot leia o seu Telegram, ele precisa usar o seu perfil de desenvolvedor:
1. Acesse: https://my.telegram.org e faça login com seu número.
2. Vá em **API development tools**.
3. Crie uma aplicação qualquer (o nome não importa).
4. Copie o **App api_id** e o **App api_hash** e cole na tela inicial do TG Monitor.

---

## 📦 Como gerar o Executável (.exe)

Se você deseja transformar o script num programa autônomo (Portable) de 1 arquivo só para Windows, sem a necessidade de instalar o Python:

1. Instale o PyInstaller:
```bash
pip install pyinstaller
```

2. Rode o comando de build (Ele embute a interface e retira a janela do console):
```bash
pyinstaller --noconfirm --onefile --windowed --name "TG_Monitor" --collect-all customtkinter BotApp.py
```

3. O arquivo final estará disponível na pasta `dist/TG_Monitor.exe`.

---

## 🔒 Segurança e Privacidade

* **Tudo Fica no seu PC:** A aplicação não possui backend de terceiros nem banco de dados na nuvem. Todas as suas credenciais (`config.json`) e sua sessão de login do Telegram (`session_monitor_gui.session`) ficam salvos **apenas localmente no seu computador** (na mesma pasta do executável).
* **Nunca envie arquivos de sessão para a internet.** (Se for dar commit neste projeto, utilize um `.gitignore` para bloquear `.session` e `config.json`).

## 📄 Licença
Distribuído sob a licença MIT. Sinta-se à vontade para modificar e usar como quiser!
