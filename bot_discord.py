import requests
import json
import datetime

def send_to_discord(webhook_url, rule, chat_name, full_text, link=None):
    """Envia uma notificação formatada para o Discord usando Webhooks."""
    if not webhook_url or not webhook_url.startswith("http"):
        return False
        
    # Limitar o texto para não estourar o limite do Discord (4096 caracteres na descrição)
    if len(full_text) > 4000:
        full_text = full_text[:4000] + "\n\n... [Texto truncado devido ao tamanho]"

    description = full_text
    if link:
        description += f"\n\n🔗 [**Clique aqui para abrir a mensagem no Telegram**]({link})"

    # Usar um Embed para ficar bonito
    embed = {
        "title": f"🚨 Nova Correspondência: {rule}",
        "description": description,
        "color": 3066993, # Cor verde (#2ecc71)
        "fields": [
            {
                "name": "🏷️ Palavra-chave",
                "value": f"`{rule}`",
                "inline": True
            },
            {
                "name": "📍 Grupo/Canal",
                "value": f"**{chat_name}**",
                "inline": True
            }
        ],
        "footer": {
            "text": "TG Monitor Pro • " + datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
        }
    }
    
    # Se houver link, transforma o título em clicável também
    if link:
        embed["url"] = link

    payload = {
        "username": "TG Monitor",
        "avatar_url": "https://i.imgur.com/2bAEMtV.png", # Ícone genérico de bot
        "embeds": [embed]
    }

    try:
        response = requests.post(
            webhook_url, 
            data=json.dumps(payload), 
            headers={"Content-Type": "application/json"},
            timeout=5
        )
        return response.status_code in [200, 204]
    except Exception as e:
        print(f"Erro ao enviar para Discord: {e}")
        return False
