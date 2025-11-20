import praw
import os
from pathlib import Path 
from dotenv import load_dotenv
from .database import SessionLocal, Publication, Comment

# --- 1. CONFIGURACIÓN DE RUTA SEGURA (.env) ---
# Estamos en: SentimetrikaITse/Api/reddit_scraper_opt.py
# Queremos ir a: SentimetrikaITse/.env (Subir 2 niveles)
env_path = Path(__file__).resolve().parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

# Configuración de API
CLIENT_ID = os.getenv("REDDIT_CLIENT_ID")
CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET")
USER_AGENT = "python:SentimentApp:v2.0 (by /u/SentimetrikaBot)"

def _mapear_sentimiento_reddit(label_original: str) -> str:
    """Convierte las etiquetas del modelo (LABEL_0, POSITIVE, etc) a formato estándar"""
    label = label_original.upper()
    if label in ['POSITIVE', 'LABEL_2', 'POS']: return 'positive'
    if label in ['NEGATIVE', 'LABEL_0', 'NEG']: return 'negative'
    return 'neutral'

def run_reddit_scraper(progress_callback, search_query, translator=None, sentiment_analyzer=None, limit=10):
    """
    Busca temas en Reddit, analiza sentimientos con IA y guarda en PostgreSQL.
    """
    
    # Validación de Credenciales
    if not CLIENT_ID or not CLIENT_SECRET:
        progress_callback("⚠️ Error: Faltan credenciales de Reddit en el archivo .env")
        return 

    progress_callback(f"📡 Conectando a Reddit para buscar: '{search_query}'...")
    
    try:
        reddit = praw.Reddit(
            client_id=CLIENT_ID, 
            client_secret=CLIENT_SECRET, 
            user_agent=USER_AGENT
        )
    except Exception as e:
        progress_callback(f"❌ Error de conexión a Reddit: {e}")
        return

    session = SessionLocal()
    nuevos_comentarios_totales = 0

    try:
        # Buscamos en 'all' para encontrar cualquier subreddit relevante
        subreddit = reddit.subreddit("all")
        
        progress_callback(f"🔎 Buscando hilos más relevantes sobre '{search_query}'...")
        
        # Buscamos por relevancia
        iterator = subreddit.search(search_query, limit=limit, sort='relevance')

        for i, submission in enumerate(iterator):
            post_id = submission.id
            post_title = submission.title
            
            progress_callback(f"Procesando {i+1}/{limit}: {post_title[:40]}...")

            # --- A. GESTIÓN DE PUBLICACIÓN ---
            existing_pub = session.query(Publication).filter_by(id=str(post_id)).first()

            if not existing_pub:
                # Intentamos traducir el título para el dashboard (Opcional)
                title_trans = post_title
                if translator:
                    try:
                        # Si el título está en inglés y queremos español, o viceversa
                        res = translator(post_title, max_length=512)
                        if res and 'translation_text' in res[0]:
                            title_trans = res[0]['translation_text']
                    except: 
                        pass # Si falla la traducción, usamos el original

                new_pub = Publication(
                    id=str(post_id),
                    red_social='Reddit',
                    title_original=post_title,
                    title_translated=title_trans
                )
                session.add(new_pub)
                session.commit()
            
            # --- B. GESTIÓN DE COMENTARIOS ---
            submission.comments.replace_more(limit=0) 
            comments_batch = submission.comments[:15] # Limitamos a 15 comentarios por post para velocidad
            
            nuevos_en_post = 0

            for comment in comments_batch:
                try:
                    if not hasattr(comment, 'body') or not comment.body: continue

                    c_text = comment.body
                    c_author = str(comment.author) if comment.author else "[deleted]"

                    # Verificar duplicados en DB
                    exists = session.query(Comment).filter_by(
                        publication_id=str(post_id),
                        text_original=c_text
                    ).first()

                    if exists: continue

                    # --- C. PROCESAMIENTO DE IA 🧠 ---
                    text_translated = c_text
                    
                    # 1. Traducción (si hay modelo)
                    if translator:
                        try:
                            res_t = translator(c_text, max_length=512)
                            text_translated = res_t[0]['translation_text']
                        except:
                            pass 

                    # 2. Sentimiento (si hay modelo)
                    sent_label = 'neutral'
                    sent_score = '0.0'
                    
                    if sentiment_analyzer:
                        try:
                            # Analizamos el texto (usamos el traducido si el modelo lo requiere)
                            res_s = sentiment_analyzer(text_translated[:512])[0]
                            sent_label = _mapear_sentimiento_reddit(res_s['label'])
                            sent_score = str(round(res_s.get('score', 0.0), 4))
                        except Exception as e_ia:
                            print(f"Error IA en comentario: {e_ia}")

                    # Guardar en DB
                    new_comment = Comment(
                        publication_id=str(post_id),
                        author=c_author,
                        text_original=c_text,
                        text_translated=text_translated, 
                        sentiment_label=sent_label, # ¡Aquí va el sentimiento real!
                        sentiment_score=sent_score  # ¡Aquí va el score real!
                    )
                    session.add(new_comment)
                    nuevos_en_post += 1

                except Exception:
                    continue
            
            if nuevos_en_post > 0:
                session.commit()
                nuevos_comentarios_totales += nuevos_en_post
                progress_callback(f"   └ 💾 Guardados {nuevos_en_post} comentarios analizados.")

    except Exception as e:
        session.rollback()
        progress_callback(f"❌ Error durante el scraping: {e}")
    finally:
        session.close()
        if nuevos_comentarios_totales > 0:
            progress_callback(f"✨ Éxito: Se analizaron y guardaron {nuevos_comentarios_totales} comentarios nuevos.")
        else:
            progress_callback("💤 Búsqueda terminada. No se encontraron comentarios nuevos para guardar.")