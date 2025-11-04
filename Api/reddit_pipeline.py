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
DB_PATH = pathlib.Path(__file__).parent.parent / "sentiment_analysis.db" # <--- AJUSTADO (asumiendo que este script está en la carpeta 'Api')

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

    for submission in tqdm(subreddit.hot(limit=LIMITE_PUBLICACIONES), total=LIMITE_PUBLICACIONES, desc="Scraping Posts"):
        publicacion_actual = {
            "id_publicacion": submission.id,
            "titulo_publicacion": submission.title,
            "comentarios": [],
            "red_social": "Reddit" # <--- CAMBIO 1: Identificamos la red social
        }
        
        submission.comments.replace_more(limit=0)
        for comment in submission.comments[:LIMITE_COMENTARIOS_POR_POST]:
            if hasattr(comment, 'body') and comment.body.strip():
                publicacion_actual["comentarios"].append({
                    "id_comentario": comment.id, # <--- CAMBIO 2: Capturamos el ID único del comentario
                    "autor": str(comment.author),
                    "texto": comment.body,
                })
        
        publicaciones_extraidas.append(publicacion_actual)
    return publicaciones_extraidas

def analyze_and_enrich_data(publications_data):
    """Traduce y analiza el sentimiento de los datos extraídos."""
    print("\nCargando modelos de IA (esto puede tardar la primera vez)...")
    try:
        translator = pipeline("translation_en_to_es", model="Helsinki-NLP/opus-mt-en-es") # type: ignore
        # Este modelo devuelve etiquetas como 'positive', 'negative', 'neutral'
        sentiment_analyzer = pipeline("sentiment-analysis", model="cardiffnlp/twitter-xlm-roberta-base-sentiment") # type: ignore
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
            pub['titulo_traducido'] = pub['titulo_publicacion']

        # Procesar comentarios
        for comment in pub['comentarios']:
            try:
                # El texto original está en inglés
                comment['lang'] = 'en' # <--- CAMBIO 3: Guardamos el idioma original
                
                # Traducir comentario
                comment['texto_traducido'] = translator(comment['texto'], max_length=512)[0]['translation_text']
                
                # Analizar sentimiento del texto original
                sentiment_result = sentiment_analyzer(comment['texto'])[0]
                
                # Mapeamos a 'POSITIVE', 'NEGATIVE', 'NEUTRAL'
                etiqueta = sentiment_result['label'].upper()
                if etiqueta == 'LABEL_2': etiqueta = 'POSITIVE'
                if etiqueta == 'LABEL_1': etiqueta = 'NEUTRAL'
                if etiqueta == 'LABEL_0': etiqueta = 'NEGATIVE'
                
                comment['analisis_sentimiento'] = {
                    "etiqueta": etiqueta,
                    "confianza": sentiment_result['score']
                }
            except Exception:
                comment['lang'] = 'und' # 'undetermined'
                comment['texto_traducido'] = "[Error de procesamiento]"
                comment['analisis_sentimiento'] = {"etiqueta": "NEUTRAL", "confianza": 0.0}
    
    return publications_data

def update_database(processed_data):
    """Inserta los nuevos datos en la base de datos SQLite, adaptada al nuevo esquema."""
    print(f"\nConectando a la base de datos en: {DB_PATH}")
    if not DB_PATH.exists():
        print(f"❌ Error: La base de datos no existe. Ejecuta 'database_setup.py' primero.")
        return

    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    
    print("Insertando datos en la base de datos (se omitirán duplicados)...")
    pub_count, com_count = 0, 0
    
    for pub in tqdm(processed_data, desc="Updating DB"):
        # --- CAMBIO 4: INSERT para 'publications' actualizado ---
        # Ahora insertamos en 'red_social' y 'source_id'
        # Usamos ON CONFLICT(id) DO UPDATE para refrescar los títulos si ya existen
        try:
            cur.execute(
                """
                INSERT INTO publications (id, title_original, title_translated, red_social, source_id) 
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    title_original = excluded.title_original,
                    title_translated = excluded.title_translated
                """,
                (
                    pub['id_publicacion'], 
                    pub['titulo_publicacion'], 
                    pub.get('titulo_traducido'),
                    pub['red_social'], # ej: 'Reddit'
                    pub['id_publicacion'] # Usamos el ID de Reddit como PK y source_id
                )
            )
            # 'rowcount' será > 0 si fue un INSERT. No cuenta en 'UPDATE'.
            # Para saber si fue nuevo, necesitaríamos una lógica diferente,
            # pero para este fin, nos enfocamos en los comentarios.

            for comment in pub['comentarios']:
                # --- CAMBIO 5: INSERT para 'comments' actualizado ---
                # Ahora insertamos 'lang' y 'source_comment_id'
                # Usamos ON CONFLICT(source_comment_id) DO NOTHING para evitar duplicados
                
                sentiment_data = comment.get('analisis_sentimiento', {})
                
                cur.execute(
                    """
                    INSERT INTO comments (
                        publication_id, 
                        author, 
                        text_translated, 
                        sentiment_label,
                        lang,                 
                        source_comment_id     
                    ) 
                    VALUES (?, ?, ?, ?, ?, ?)
                    ON CONFLICT(source_comment_id) DO NOTHING
                    """,
                    (
                        pub['id_publicacion'],
                        comment.get('autor'),
                        comment.get('texto_traducido'),
                        sentiment_data.get('etiqueta'),
                        comment.get('lang'),            # 'en' o 'und'
                        comment.get('id_comentario')    # El ID único de Reddit
                    )
                )
                if cur.rowcount > 0: 
                    com_count += 1
                    
        except sqlite3.Error as e:
            # Captura errores generales de la base de datos
            print(f"Error al procesar la publicación {pub['id_publicacion']}: {e}")
            continue

    con.commit()
    con.close()
    print(f"\n✅ Proceso de base de datos completado.")
    # (El conteo de publicaciones nuevas ya no es preciso con 'ON CONFLICT...DO UPDATE')
    print(f"   - Se revisaron {len(processed_data)} publicaciones.")
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

    print("\n🏁 ¡Pipeline de Reddit finalizado!")