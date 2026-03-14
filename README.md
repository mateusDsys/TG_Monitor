# TG Monitor Pro

TG Monitor Pro é uma aplicação desktop avançada desenvolvada em Python para monitorar em tempo real mensagens de canais e grupos do Telegram. Ideal para acompanhar palavras-chave específicas como alertas de promoções, vagas de emprego, sinais de mercado ou qualquer termo de interesse, automatizando o envio de notificações visuais, sonoras e repasses para o Discord.

## 🚀 Principais Funcionalidades

### 1. Busca Avançada (Modo Regex)
Além da busca padrão (com operadores `+` para AND e `/` para OR), o sistema conta com um **Modo Regex**. Se ativado, permite buscar padrões complexos (ex: `vaga.*python` para encontrar "vaga" e "python" na mesma frase, ou `\d+% off` para encontrar descontos).

### 2. Filtros de Canais (Whitelist e Blacklist)
Cansado de pesquisar IDs no Google? O app possui um botão mágico **"Listar Meus Canais"** que conecta ao seu Telegram e puxa a lista completa com os nomes e IDs dos seus grupos. Você pode adicionar canais à:
*   **Whitelist:** O bot ignorará todo o resto e monitorará **apenas** estes canais.
*   **Blacklist:** O bot monitorará tudo, **exceto** estes canais.

### 3. Inteligência Anti-Spam
Evita que seu PC apite sem parar se um usuário mandar a mesma mensagem várias vezes seguidas. Você define um tempo em segundos (ex: 60s). O bot "grava" a mensagem na memória e só te avisará novamente se a mesma mensagem for enviada após o tempo estipulado. O sistema conta com auto-limpeza de memória (Garbage Collector) para evitar vazamentos (Memory Leaks).

### 4. Integração nativa com Discord (Webhooks)
Não quer ficar preso ao PC? Cole a URL de um Webhook do seu servidor do Discord na aba de "Integrações". O bot empacotará os alertas em balões bonitos (Embeds) e enviará instantaneamente para o seu Discord (PC ou Celular), contendo o nome do grupo, o texto completo e um **link clicável** que te leva direto para a mensagem original no aplicativo do Telegram.

### 5. Histórico e Banco de Dados (SQLite)
Todas as mensagens encontradas são salvas eternamente no banco de dados local (`monitor_history.db`). 
*   Você pode ler o histórico completo sem abrir o Telegram (basta clicar no trecho da mensagem na aba "Histórico" para abrir um Pop-up de leitura).
*   Você pode exportar todo o histórico para um arquivo `.csv` para relatórios ou planilhas do Excel.

### 6. Sistema de Áudio Confortável
5 alertas sonoros gerados sinteticamente com foco no conforto auditivo humano (frequências médias-graves e envelopes de fade-in/fade-out). Variam de um leve "Beep" até uma sirene de "Urgente", todos controláveis pela barra de volume.

### 7. Comodidades de Uso
*   **Auto-Start:** Pode ser configurado para abrir de forma invisível toda vez que você liga o computador.
*   **Minimizar para a Bandeja (System Tray):** Fica escondido ao lado do relógio do Windows. 
*   **Controles Rápidos:** Clique com o botão direito no ícone da bandeja para pausar ou retomar o monitoramento sem abrir a janela.
*   **Auto-Reconexão:** Se sua internet cair, ele fica tentando reconectar silenciosamente a cada 10 segundos.

## ⚙️ Pré-Requisitos e Instalação

Assegure-se de ter o **Python 3.10+** instalado no seu sistema. Em seguida, instale todas as bibliotecas necessárias rodando o comando no terminal:

```bash
pip install customtkinter telethon pygame unidecode plyer pystray pillow requests winshell pypiwin32
```

## 🔐 Como logar (API do Telegram)
Para usar o aplicativo, você precisa criar as suas credenciais de Desenvolvedor no Telegram (é gratuito).
1. Acesse [https://my.telegram.org](https://my.telegram.org)
2. Faça login com seu número.
3. Vá em "API development tools".
4. Crie um aplicativo qualquer e copie o **API ID** e o **API Hash**.
5. Abra o TG Monitor Pro e cole esses dados junto com seu número de telefone.

*(O app suporta perfeitamente contas que possuem Autenticação de Dois Fatores - 2FA ativada).*

## 🛠️ Arquitetura do Projeto
*   `BotApp.py`: Interface Gráfica principal e orquestrador de eventos.
*   `bot_telegram.py`: Motor de comunicação com a API do Telegram (`telethon`), responsável pela leitura e aplicação de regras e filtros.
*   `bot_config.py`: Gerenciador de salvar/carregar as opções do usuário e cuidar do atalho de auto-start do Windows.
*   `bot_audio.py`: Gerador matemático de ondas sonoras sintéticas e player de áudio usando o mixer do `pygame`.
*   `bot_db.py`: Conexão com o banco de dados SQLite para gravação segura e leitura de histórico (`sqlite3`).
*   `bot_discord.py`: Repassador de mensagens via requisições HTTP para a nuvem do Discord (`requests`).
