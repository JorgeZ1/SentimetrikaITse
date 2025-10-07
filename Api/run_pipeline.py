import praw
import json
import os
import sqlite3
import pathlib
from transformers import pipeline
from tqdm import tqdm

# --- 1. CONFIGURACIÓN GENERAL ---
# Lee las credenciales de Reddit desde variables de entorno
CLIENT_ID = os.getenv("REDDIT_CLIENT_ID", "TU_CLIENT_ID")
CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET", "TU_CLIENT_SECRET")
USER_AGENT = "python:DataScraper:v1.2 (by /u/TuNombreDeUsuario)"

# Parámetros de extracción y base de datos
NOMBRE_SUBREDDIT = 'Futurology'
LIMITE_PUBLICACIONES = 5
LIMITE_COMENTARIOS_POR_POST = 50
DB_PATH = pathlib.Path(__file__).parent.parent.parent / "sentiment_analysis.db"

def scrape_reddit_data():
    """Extrae publicaciones y comentarios de Reddit."""
    if CLIENT_ID == "TU_CLIENT_ID" or CLIENT_SECRET == "TU_CLIENT_SECRET":
        print("⚠️  ADVERTENCIA: Usando credenciales de ejemplo. Configura tus variables de entorno.")

    print("Iniciando conexión con Reddit...")
    reddit = praw.Reddit(client_id=CLIENT_ID, client_secret=CLIENT_SECRET, user_agent=USER_AGENT)
    print("✅ Conexión con Reddit exitosa.")

    publicaciones_extraidas = []
    subreddit = reddit.subreddit(NOMBRE_SUBREDDIT)
    print(f"\nExtrayendo hasta {LIMITE_PUBLICACIONES} publicaciones de r/{NOMBRE_SUBREDDIT}...")

    # Usamos tqdm para una barra de progreso
    for submission in tqdm(subreddit.hot(limit=LIMITE_PUBLICACIONES), total=LIMITE_PUBLICACIONES, desc="Scraping Posts"):
        publicacion_actual = {
            "id_publicacion": submission.id,
            "titulo_publicacion": submission.title,
            "comentarios": []
        }
        
        submission.comments.replace_more(limit=0)
        for comment in submission.comments[:LIMITE_COMENTARIOS_POR_POST]:
            if hasattr(comment, 'body') and comment.body.strip():
                publicacion_actual["comentarios"].append({
                    "autor": str(comment.author),
                    "texto": comment.body,
                })
        
        publicaciones_extraidas.append(publicacion_actual)
    return publicaciones_extraidas

def analyze_and_enrich_data(publications_data):
    """Traduce y analiza el sentimiento de los datos extraídos."""
    print("\nCargando modelos de IA (esto puede tardar la primera vez)...")
    try:
        translator = pipeline("translation_en_to_es", model="Helsinki-NLP/opus-mt-en-es")
        sentiment_analyzer = pipeline("sentiment-analysis", model="cardiffnlp/twitter-xlm-roberta-base-sentiment")
        print("✅ Modelos cargados exitosamente.")
    except Exception as e:
        print(f"❌ Error al cargar los modelos: {e}")
        return []

    print("\nProcesando datos con modelos de IA...")
    for pub in tqdm(publications_data, desc="Analyzing Data"):
        # Traducir título
        try:
            pub['titulo_traducido'] = translator(pub['titulo_publicacion'], max_length=512)[0]['translation_text']
        except Exception:
            pub['titulo_traducido'] = pub['titulo_publicacion'] # Si falla, usa el original

        # Procesar comentarios
        for comment in pub['comentarios']:
            try:
                # Traducir comentario
                comment['texto_traducido'] = translator(comment['texto'], max_length=512)[0]['translation_text']
                # Analizar sentimiento del texto original
                sentiment_result = sentiment_analyzer(comment['texto'])[0]
                comment['analisis_sentimiento'] = {
                    "etiqueta": sentiment_result['label'].upper(),
                    "confianza": sentiment_result['score']
                }
            except Exception:
                comment['texto_traducido'] = "[Error de procesamiento]"
                comment['analisis_sentimiento'] = {"etiqueta": "ERROR", "confianza": 0.0}
    
    return publications_data

def update_database(processed_data):
    """Inserta los nuevos datos en la base de datos SQLite, evitando duplicados."""
    print(f"\nConectando a la base de datos en: {DB_PATH}")
    if not DB_PATH.exists():
        print(f"❌ Error: La base de datos no existe. Ejecuta 'database_setup.py' primero.")
        return

    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    
    print("Insertando datos en la base de datos (se omitirán duplicados)...")
    pub_count, com_count = 0, 0
    for pub in tqdm(processed_data, desc="Updating DB"):
        try:
            cur.execute(
                "INSERT OR IGNORE INTO publications (id, title_original, title_translated) VALUES (?, ?, ?)",
                (pub['id_publicacion'], pub['titulo_publicacion'], pub.get('titulo_traducido'))
            )
            if cur.rowcount > 0: pub_count += 1

            for comment in pub['comentarios']:
                cur.execute(
                    "INSERT INTO comments (publication_id, author, text_translated, sentiment_label) VALUES (?, ?, ?, ?)",
                    (
                        pub['id_publicacion'],
                        comment.get('autor'),
                        comment.get('texto_traducido'),
                        comment.get('analisis_sentimiento', {}).get('etiqueta')
                    )
                )
                com_count += 1
        except sqlite3.IntegrityError as e:
            # Esto puede ocurrir si un comentario ya existe, lo ignoramos.
            print(f"Saltando comentario duplicado o error de integridad: {e}")
            continue

    con.commit()
    con.close()
    print(f"\n✅ Proceso de base de datos completado.")
    print(f"   - {pub_count} nuevas publicaciones añadidas.")
    print(f"   - {com_count} nuevos comentarios añadidos.")

# --- PUNTO DE ENTRADA PRINCIPAL ---
if __name__ == "__main__":
    # Etapa 1: Extraer datos de Reddit
    scraped_data = scrape_reddit_data()
    
    if scraped_data:
        # Etapa 2: Analizar y enriquecer los datos
        enriched_data = analyze_and_enrich_data(scraped_data)
        
        if enriched_data:
            # Etapa 3: Actualizar la base de datos
            update_database(enriched_data)

    print("\n🏁 ¡Pipeline finalizado!")