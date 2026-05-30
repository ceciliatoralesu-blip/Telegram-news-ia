# Bot de Telegram para Noticias de IA con Gemini y GitHub Actions

Este proyecto es un bot automatizado que recopila noticias de Inteligencia Artificial de múltiples fuentes RSS (como OpenAI, Google Research, Hugging Face, etc.), genera un resumen en español usando **Gemini 2.5 Flash** y las envía en tiempo real a un canal o chat de Telegram.

Funciona de forma 100% gratuita ejecutándose en **GitHub Actions** cada 30 minutos sin necesidad de servidores.

---

## 🛠️ Configuración de Credenciales

Para que el bot funcione, necesitas obtener tres credenciales:

### 1. API Key de Gemini
1. Ve a [Google AI Studio](https://aistudio.google.com/).
2. Haz clic en **Create API Key**.
3. Copia la clave generada. Es gratuita para este volumen de uso.

### 2. Token de Telegram Bot
1. Abre Telegram y busca al bot oficial `@BotFather`.
2. Envía el comando `/newbot`.
3. Sigue los pasos para asignarle un nombre y un usuario a tu bot (ej. `mi_ai_news_bot`).
4. `@BotFather` te dará un Token (ej: `123456789:ABCdefGhIJKlmNoPQRsTUVwxyZ`). Cópialo.
5. **IMPORTANTE:** Busca a tu bot en Telegram e inicia un chat con él pulsando `/start`. Si no lo haces, no podrá enviarte mensajes.

### 3. Telegram Chat ID
Para saber a dónde enviar las noticias (a ti directamente o a un grupo/canal):
* **Para Chat Privado:**
  1. Busca al bot `@userinfobot` en Telegram.
  2. Envía `/start` y te dará tu ID numérico (ej. `987654321`).
* **Para un Canal o Grupo:**
  1. Agrega a tu bot recién creado como **administrador** en el canal o grupo con permisos para enviar mensajes.
  2. Envía un mensaje cualquiera al canal o grupo.
  3. Reenvía ese mensaje al bot `@ShowJsonBot` para ver el ID de chat (los IDs de canales suelen empezar con `-100`, ej: `-1001234567890`).

---

## 🚀 Configuración en GitHub (Despliegue)

1. Crea un nuevo repositorio en tu cuenta de GitHub (puede ser público o privado).
2. Sube todo el código de esta carpeta a tu repositorio:
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git branch -M main
   git remote add origin <URL_DE_TU_REPOSITORIO>
   git push -u origin main
   ```
3. Configura los Secretos en GitHub:
   - Ve a la página de tu repositorio en GitHub.
   - Entra en **Settings** -> **Secrets and variables** -> **Actions**.
   - Haz clic en **New repository secret** y añade las siguientes tres claves:
     - `GEMINI_API_KEY`: Tu clave de Google AI Studio.
     - `TELEGRAM_BOT_TOKEN`: El token que te dio `@BotFather`.
     - `TELEGRAM_CHAT_ID`: Tu ID de chat de Telegram.
4. **Habilitar permisos de escritura para GitHub Actions (¡CRÍTICO!)**:
   - Ve a **Settings** -> **Actions** -> **General** en tu repositorio.
   - Baja hasta la sección **Workflow permissions**.
   - Selecciona **Read and write permissions**.
   - Haz clic en **Save**.
   *Esto es necesario para que el bot pueda guardar y actualizar el archivo `sent_articles.json` en tu repositorio y evitar que te envíe las mismas noticias repetidas.*

---

## 🖥️ Ejecución y Pruebas Locales

Si deseas probar el bot localmente en tu computadora:

1. Instala las dependencias:
   ```bash
   pip install -r requirements.txt
   ```
2. Crea un archivo `.env` en la raíz del proyecto con tus credenciales:
   ```env
   GEMINI_API_KEY=tu_api_key_aquí
   TELEGRAM_BOT_TOKEN=tu_token_de_telegram_aquí
   TELEGRAM_CHAT_ID=tu_chat_id_aquí
   ```
3. Ejecuta el script de prueba:
   ```bash
   python test_apis.py
   ```
4. Ejecuta el script principal:
   ```bash
   python main.py
   ```
