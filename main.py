import os
import json
import requests
import feedparser
import time
from google import genai

def load_dotenv():
    """Carga variables de entorno desde un archivo .env si existe (útil para desarrollo local)."""
    if os.path.exists(".env"):
        try:
            with open(".env", "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        key, val = line.split("=", 1)
                        os.environ[key.strip()] = val.strip()
            print("Variables del archivo .env cargadas.")
        except Exception as e:
            print(f"Advertencia: No se pudo leer el archivo .env: {e}")


# Configuración de los feeds RSS de Inteligencia Artificial
FEEDS = {
    "OpenAI": "https://openai.com/news/rss.xml",
    "Google Blog": "https://blog.google/rss",
    "Hugging Face": "https://huggingface.co/blog/feed.xml",
    "TechCrunch AI": "https://techcrunch.com/category/artificial-intelligence/feed/",
    "Microsoft Research": "https://www.microsoft.com/en-us/research/blog/feed/",
    "Nvidia Blog": "https://blogs.nvidia.com/feed/"
}

STATE_FILE = "sent_articles.json"
MAX_STORED_ARTICLES = 10000

def load_sent_articles():
    """Carga la lista de URLs de artículos ya enviados."""
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Error al cargar el archivo de estado: {e}")
            return []
    return []

def save_sent_articles(sent_list):
    """Guarda la lista de URLs de artículos enviados, limitando la cantidad para evitar que crezca indefinidamente."""
    # Mantener solo los últimos MAX_STORED_ARTICLES para evitar crecimiento ilimitado
    if len(sent_list) > MAX_STORED_ARTICLES:
        sent_list = sent_list[-MAX_STORED_ARTICLES:]
    try:
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(sent_list, f, indent=4, ensure_ascii=False)
        print(f"Estado guardado. Total artículos registrados: {len(sent_list)}")
    except Exception as e:
        print(f"Error al guardar el archivo de estado: {e}")

def get_gemini_summary(client, title, source, content):
    """Utiliza Gemini para traducir el título y generar un resumen conciso en español."""
    prompt = f"""
Eres un editor experto en Inteligencia Artificial. Traduce y resume la siguiente noticia de IA en español.

Título original: {title}
Fuente: {source}
Contenido/Resumen original: {content}

Genera el siguiente formato exacto:
<b>[Título traducido al español]</b>

[Resumen en español, de 1 o 2 párrafos concisos y fluidos. Explica de qué se trata la noticia, el contexto técnico básico de forma sencilla y por qué es relevante para el campo de la Inteligencia Artificial. Utiliza un tono profesional y periodístico.]

Reglas estrictas:
1. No incluyas ningún enlace (link) en tu respuesta. El enlace se agregará automáticamente después.
2. No uses formato Markdown. Solo puedes usar etiquetas HTML básicas como <b>, <i>, <code> si quieres dar formato a algún término técnico o destacar algo.
3. No saludes ni des explicaciones extras, responde directamente con el título formateado en <b> y luego el resumen.
"""
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
        )
        return response.text.strip()
    except Exception as e:
        print(f"Error al llamar a Gemini: {e}")
        return f"<b>{title}</b>\n\n(No se pudo generar el resumen automático debido a un error: {e})"

def send_telegram_message(token, chat_id, text, link, source):
    """Envía el mensaje formateado a Telegram."""
    telegram_message = f"📢 {text}\n\n<i>Fuente: {source}</i>\n🔗 <a href='{link}'>Leer artículo completo</a>"
    
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": telegram_message,
        "parse_mode": "HTML",
        "disable_web_page_preview": False
    }
    
    try:
        response = requests.post(url, json=payload, timeout=15)
        response.raise_for_status()
        print(f"Mensaje enviado con éxito para la noticia de {source}.")
        return True
    except Exception as e:
        print(f"Error al enviar mensaje a Telegram: {e}")
        if response is not None:
            print(f"Respuesta del servidor Telegram: {response.text}")
        return False

def main():
    # Cargar variables locales si existe el archivo .env
    load_dotenv()
    
    # 1. Obtener credenciales de variables de entorno
    gemini_api_key = os.environ.get("GEMINI_API_KEY")
    telegram_token = os.environ.get("TELEGRAM_BOT_TOKEN")
    telegram_chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    
    if not all([gemini_api_key, telegram_token, telegram_chat_id]):
        print("ERROR: Faltan variables de entorno esenciales (GEMINI_API_KEY, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID).")
        return
    
    # 2. Inicializar clientes
    gemini_client = genai.Client(api_key=gemini_api_key)
    
    # 3. Cargar estado anterior
    is_first_run = not os.path.exists(STATE_FILE)
    sent_articles = load_sent_articles()
    
    print(f"Iniciando revisión de noticias. Modo de primera ejecución: {is_first_run}")
    
    # 4. Descargar artículos de todos los feeds
    new_articles = []
    current_urls = []
    
    for source_name, feed_url in FEEDS.items():
        print(f"Procesando feed de {source_name}...")
        try:
            response = requests.get(feed_url, timeout=15)
            response.raise_for_status()
            feed = feedparser.parse(response.content)
            # Procesar del más viejo al más nuevo por si hay varios nuevos
            entries = list(reversed(feed.entries))
            
            for entry in entries:
                # Obtener enlace del artículo
                link = entry.get("link") or entry.get("id") or entry.get("guid")
                if not link:
                    continue
                
                current_urls.append(link)
                
                # Si el artículo no ha sido enviado
                if link not in sent_articles:
                    title = entry.get("title", "Sin título")
                    content = entry.get("summary") or entry.get("description") or ""
                    
                    # Limpiar o formatear el contenido si es necesario (quitar HTML tags si dificultan la lectura de Gemini, 
                    # aunque Gemini suele manejarlos bien)
                    new_articles.append({
                        "title": title,
                        "link": link,
                        "content": content,
                        "source": source_name
                    })
        except Exception as e:
            print(f"Error al procesar el feed de {source_name}: {e}")
            
    print(f"Se encontraron {len(new_articles)} artículos nuevos.")
    
    # 5. Manejo del flujo según si es primera ejecución o no
    if is_first_run or len(sent_articles) == 0:
        print("Primera ejecución o archivo de estado vacío. Registrando artículos existentes y enviando bienvenida...")
        # Guardar todos los links actuales para no enviarlos después
        all_links = list(set(sent_articles + current_urls + [art["link"] for art in new_articles]))
        save_sent_articles(all_links)
        
        # Enviar un mensaje de bienvenida de prueba con la noticia más reciente si existe
        welcome_text = "<b>🤖 ¡Bot de Noticias de IA Activado!</b>\n\nEste bot revisará periódicamente las fuentes oficiales de IA y te mantendrá al día con resúmenes automatizados en tiempo real."
        if new_articles:
            latest = new_articles[-1] # La última noticia parseada (la más nueva)
            print(f"Generando resumen de prueba para: {latest['title']}")
            summary = get_gemini_summary(gemini_client, latest["title"], latest["source"], latest["content"])
            test_msg = f"{welcome_text}\n\nAquí tienes un ejemplo de noticia reciente:\n\n{summary}"
            send_telegram_message(telegram_token, telegram_chat_id, test_msg, latest["link"], latest["source"])
        else:
            send_telegram_message(telegram_token, telegram_chat_id, welcome_text, "https://openai.com", "Bot setup")
        return
        
    # Si detectamos un volumen de artículos inusual en una ejecución normal (más de 10)
    # podría deberse a un problema de estado o a que el bot estuvo apagado mucho tiempo.
    # Evitamos saturar enviando solo los 3 más recientes y registrando el resto como leídos.
    if len(new_articles) > 10:
        print(f"Advertencia: Se detectaron {len(new_articles)} artículos nuevos (límite de 10 superado).")
        print("Registrando el resto como leídos para evitar spam y cuota excedida. Solo se procesarán los 3 más recientes.")
        
        # Guardar todos los artículos como leídos inmediatamente
        all_links = list(set(sent_articles + current_urls + [art["link"] for art in new_articles]))
        save_sent_articles(all_links)
        
        # Quedarse con los 3 más recientes
        new_articles = new_articles[-3:]

    # 6. Procesar y enviar noticias nuevas
    if new_articles:
        successful_sends = []
        for article in new_articles:
            print(f"Procesando: {article['title']} ({article['source']})")
            
            # Generar resumen con Gemini
            summary = get_gemini_summary(gemini_client, article["title"], article["source"], article["content"])
            
            # Enviar a Telegram
            success = send_telegram_message(
                telegram_token, 
                telegram_chat_id, 
                summary, 
                article["link"], 
                article["source"]
            )
            
            if success:
                successful_sends.append(article["link"])
                # Evitar saturar la API de Telegram con demasiados mensajes seguidos
                time.sleep(2)
        
        # 7. Actualizar el archivo de estado con las noticias que realmente se enviaron
        if successful_sends:
            updated_sent_list = sent_articles + successful_sends
            save_sent_articles(updated_sent_list)
    else:
        print("No hay noticias nuevas para enviar.")

if __name__ == "__main__":
    main()
