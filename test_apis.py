import os
import requests
from google import genai

def load_dotenv():
    """Carga variables de entorno desde un archivo .env si existe."""
    if os.path.exists(".env"):
        try:
            with open(".env", "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        key, val = line.split("=", 1)
                        os.environ[key.strip()] = val.strip()
            print("✅ Variables del archivo .env cargadas.")
        except Exception as e:
            print(f"❌ Advertencia: No se pudo leer el archivo .env: {e}")

def test_gemini(api_key):
    print("\n🔍 Probando conexión con la API de Gemini...")
    try:
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents="Saluda en una línea diciendo que la conexión con Gemini fue un éxito.",
        )
        text = response.text.strip()
        print(f"✅ Gemini respondió: \"{text}\"")
        return True
    except Exception as e:
        print(f"❌ Error al conectar con Gemini: {e}")
        return False

def test_telegram(token, chat_id):
    print("\n🔍 Probando conexión con la API de Telegram...")
    test_message = (
        "🤖 <b>¡Conexión Exitosa!</b>\n\n"
        "Esta es un mensaje de prueba enviado desde tu script local. "
        "Tanto el Token del Bot como tu Chat ID están bien configurados."
    )
    
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": test_message,
        "parse_mode": "HTML"
    }
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
        print("✅ Mensaje enviado a Telegram con éxito. Revisa tu chat.")
        return True
    except Exception as e:
        print(f"❌ Error al enviar mensaje a Telegram: {e}")
        if 'response' in locals() and response is not None:
            print(f"Detalle del error del servidor: {response.text}")
        return False

def main():
    load_dotenv()
    
    gemini_key = os.environ.get("GEMINI_API_KEY")
    telegram_token = os.environ.get("TELEGRAM_BOT_TOKEN")
    telegram_chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    
    missing = []
    if not gemini_key: missing.append("GEMINI_API_KEY")
    if not telegram_token: missing.append("TELEGRAM_BOT_TOKEN")
    if not telegram_chat_id: missing.append("TELEGRAM_CHAT_ID")
    
    if missing:
        print(f"❌ Error: Faltan las siguientes variables de entorno: {', '.join(missing)}")
        print("Por favor, crea un archivo '.env' en este directorio con las variables necesarias.")
        return
        
    print("Variables encontradas. Iniciando pruebas de conexión...")
    
    gemini_ok = test_gemini(gemini_key)
    telegram_ok = test_telegram(telegram_token, telegram_chat_id)
    
    print("\n--- RESUMEN DE PRUEBAS ---")
    print(f"Gemini API: {'✅ OK' if gemini_ok else '❌ Error'}")
    print(f"Telegram Bot: {'✅ OK' if telegram_ok else '❌ Error'}")
    
    if gemini_ok and telegram_ok:
        print("\n🎉 ¡Todo listo! Puedes configurar el script en GitHub Actions ahora.")
    else:
        print("\n⚠️ Por favor, revisa los errores anteriores y vuelve a intentarlo.")

if __name__ == "__main__":
    main()
