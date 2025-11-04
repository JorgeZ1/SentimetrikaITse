import discord
import sqlite3
import os
from transformers import pipeline
from tqdm import tqdm
import dotenv

dotenv.load_dotenv()  # <-- CAMBIO: Cargar las variables del archivo .env

# Lee las variables desde el archivo .env
BOT_TOKEN = os.environ.get("BOT_TOKEN")
PUBLICATION_ID_PARA_DB = os.environ.get("PUBLICATION_ID_PARA_DB")
DB_NAME = os.environ.get("DB_NAME")

# --- 2. MODELOS DE IA Y CONEXIÓN DB ---
print("Cargando modelos de IA...")
translator = pipeline("translation_en_to_es", model="Helsinki-NLP/opus-mt-en-es") # pyright: ignore
sentiment_analyzer = pipeline("sentiment-analysis", model="cardiffnlp/twitter-xlm-roberta-base-sentiment") # type: ignore
print("✅ Modelos cargados.")

def mapear_sentimiento(label_original: str) -> str:
    label = label_original.upper()
    if label == 'POSITIVE' or label == 'LABEL_2': return 'positive'
    if label == 'NEUTRAL' or label == 'LABEL_1': return 'neutral'
    if label == 'NEGATIVE' or label == 'LABEL_0': return 'negative'
    return 'neutral'

# --- 3. CONFIGURACIÓN DEL BOT DE DISCORD ---
# Configurar los "Intents" (permisos) que activamos en el portal
intents = discord.Intents.default()
intents.message_content = True # Permiso para leer mensajes
intents.messages = True

bot = discord.Bot(intents=intents)

@bot.event
async def on_ready():
    print(f"✅ Bot conectado como {bot.user}")
    print("--- ¡Bot listo! ---")
    print("Ve a tu servidor de Discord y escribe en cualquier canal:")
    print("/analizar <ID_DEL_CANAL> [limite_mensajes]")

# --- 4. EL COMANDO PARA SCRAPEAR ---
# Esto crea un comando "slash" (/) en Discord
@bot.slash_command(
    name="analizar", 
    description="Analiza el historial de un canal y lo guarda en la DB."
)
async def analizar(
    ctx: discord.ApplicationContext,
    id_del_canal: str,
    limite: int = 100 # Número de mensajes a buscar (por defecto 100)
):
    await ctx.respond(f"🤖 ¡Iniciando análisis de {limite} mensajes en el canal {id_del_canal}! Esto puede tardar...")
    
    try:
        # Obtener el canal
        channel = bot.get_channel(int(id_del_canal))
        if not channel or not isinstance(channel, discord.TextChannel):
            await ctx.send("❌ Error: No se encontró ese canal de texto.")
            return

        con = sqlite3.connect(DB_NAME) # type: ignore
        cur = con.cursor()
        
        nuevos_comentarios = 0
        
        # Usamos tqdm para mostrar el progreso en la consola
        print(f"\nIniciando recolección de {limite} mensajes del canal {channel.name}...")
        
        # Itera sobre el historial del canal
        async for message in tqdm(channel.history(limit=limite), total=limite, desc="Procesando mensajes"): # type: ignore
            try:
                comment_id = str(message.id)
                comment_text_orig = message.content
                comment_author = str(message.author)
                
                if not comment_text_orig or message.author.bot:
                    continue # Ignorar mensajes vacíos o de otros bots

                # --- Revisar duplicado ---
                cur.execute("SELECT 1 FROM comments WHERE source_comment_id = ?", (comment_id,))
                if cur.fetchone():
                    continue # Ya existe, saltar

                # --- Análisis y Traducción (asumimos que todo es 'es' o 'en') ---
                # (Una detección de idioma real sería más lenta)
                text_translated = comment_text_orig
                text_para_analisis = comment_text_orig
                lang = 'es' # Asumir español por defecto
                
                try:
                    # Intenta traducir. Si falla, probablemente no es inglés.
                    translation_result = translator(comment_text_orig, max_length=512)
                    # Simple heurística: si la traducción es muy diferente, era inglés.
                    if translation_result and abs(len(translation_result[0]['translation_text']) - len(comment_text_orig)) > 5:
                        text_translated = translation_result[0]['translation_text']
                        lang = 'en'
                except Exception:
                    pass # Dejar como español

                # Analizar sentimiento
                sentiment_result = sentiment_analyzer(text_para_analisis)[0]
                sentiment_label = mapear_sentimiento(sentiment_result['label'])

                # --- Guardar en DB ---
                cur.execute(
                    """
                    INSERT INTO comments (
                        publication_id, source_comment_id, lang, 
                        sentiment_label, text_translated, author
                    ) VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (PUBLICATION_ID_PARA_DB, comment_id, lang, sentiment_label, text_translated, comment_author)
                )
                
                if cur.rowcount > 0:
                    nuevos_comentarios += 1

            except Exception as e_msg:
                print(f"Error procesando mensaje {message.id}: {e_msg}")

        con.commit()
        con.close()
        
        await ctx.send(f"✅ ¡Análisis completado! Se añadieron {nuevos_comentarios} nuevos mensajes a la base de datos.")
        print(f"--- Análisis de canal {channel.name} completado ---")
        
    except Exception as e:
        await ctx.send(f"❌ Error fatal en el comando: {e}")

# --- 5. EJECUTAR EL BOT ---
if __name__ == "__main__":
    if not BOT_TOKEN:
        print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
        print("ERROR: Debes editar el archivo 'discord_pipeline.py'")
        print("y pegar tu BOT_TOKEN en la línea 8.")
        print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
    else:
        bot.run(BOT_TOKEN)