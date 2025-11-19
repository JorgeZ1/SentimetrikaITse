import praw
import os
from dotenv import load_dotenv
# --- CAMBIO: Importamos la DB de Postgres ---
from .database import SessionLocal, Publication, Comment

load_dotenv() 

# Configuración
CLIENT_ID = os.getenv("REDDIT_CLIENT_ID")
CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET")
USER_AGENT = "python:SentimentApp:v2.0 (by /u/TuUsuario)"

def _mapear_sentimiento_reddit(label_original: str) -> str:
    """Normaliza las etiquetas del modelo"""
    label = label_original.upper()
    if label in ['POSITIVE', 'LABEL_2', 'POS']: return 'positive'
    if label in ['NEGATIVE', 'LABEL_0', 'NEG']: return 'negative'
    return 'neutral'

def run_reddit_scrape_opt(progress_callback, translator, sentiment_analyzer, subreddit_name, post_limit, comment_limit):
    """
    Versión PostgreSQL optimizada para Reddit.
    """
    
    # 1. Validar Credenciales
    if not CLIENT_ID or not CLIENT_SECRET:
        progress_callback("⚠️ ADVERTENCIA: Faltan credenciales de Reddit en el .env")
        return 

    progress_callback(f"Conectando a Reddit para analizar r/{subreddit_name}...")
    
    try:
        reddit = praw.Reddit(
            client_id=CLIENT_ID, 
            client_secret=CLIENT_SECRET, 
            user_agent=USER_AGENT
        )
        # Prueba de conexión ligera
        reddit.user.me() 
    except Exception as e:
        # Si falla user.me() puede ser modo solo lectura, intentamos seguir, 
        # pero si es error de credenciales fallará abajo.
        pass

    # 2. Iniciar Sesión DB
    session = SessionLocal()
    nuevos_comentarios_totales = 0

    try:
        subreddit = reddit.subreddit(subreddit_name)
        # Usamos .hot() para obtener lo más relevante
        iterator = subreddit.hot(limit=post_limit)
        
        progress_callback(f"Descargando publicaciones de r/{subreddit_name}...")

        for i, submission in enumerate(iterator):
            post_id = submission.id
            post_title = submission.title
            
            progress_callback(f"Procesando Post {i+1}/{post_limit}: {post_title[:40]}...")

            # --- GESTIÓN PUBLICACIÓN (ORM) ---
            existing_pub = session.query(Publication).filter_by(id=str(post_id)).first()

            if not existing_pub:
                # Traducir título si es necesario
                title_translated = post_title
                try:
                    # Asumimos que si está en inglés lo traducimos, 
                    # pero Reddit no siempre da el idioma. 
                    # Intentamos traducir directo.
                    if translator:
                        res = translator(post_title, max_length=512)
                        if res: title_translated = res[0]['translation_text']
                except:
                    pass

                new_pub = Publication(
                    id=str(post_id),
                    red_social='Reddit',
                    title_original=post_title,
                    title_translated=title_translated
                )
                session.add(new_pub)
                session.commit() # Guardar post
            else:
                # Ya existe, usamos el título existente
                pass

            # --- GESTIÓN COMENTARIOS ---
            submission.comments.replace_more(limit=0) # Evitar árboles de comentarios profundos que ralentizan
            comments_batch = submission.comments[:comment_limit]
            
            nuevos_comentarios_post = 0

            for comment in comments_batch:
                try:
                    if not hasattr(comment, 'body') or not comment.body:
                        continue

                    comment_text = comment.body
                    comment_author = str(comment.author) if comment.author else "[deleted]"

                    # Verificar duplicados
                    # Buscamos por ID de publicación + Autor + Texto original
                    existing_comment = session.query(Comment).filter_by(
                        publication_id=str(post_id),
                        author=comment_author,
                        text_original=comment_text
                    ).first()

                    if existing_comment:
                        continue

                    # Procesamiento IA
                    text_translated = comment_text
                    text_para_analisis = comment_text

                    # Intento de traducción
                    if translator:
                        try:
                            trans_res = translator(comment_text, max_length=512)
                            if trans_res:
                                text_translated = trans_res[0]['translation_text']
                        except:
                            pass # Fallback al original

                    # Análisis de Sentimiento 

                    if sentiment_analyzer:
                        try:
                            # Analizamos el texto (traducido o no, según convenga al modelo)
                            # Si tu modelo es multilingüe usa el original, si es en inglés usa el traducido.
                            # Asumiremos modelo en inglés por defecto:
                            s_res = sentiment_analyzer(text_translated[:512])[0]
                            sentiment_label = _mapear_sentimiento_reddit(s_res['label'])
                            sentiment_score = str(round(s_res.get('score', 0.0), 4))
                        except:
                            sentiment_label = 'neutral'
                            sentiment_score = '0.0'
                    else:
                        sentiment_label = 'neutral'
                        sentiment_score = '0.0'

                    # Crear objeto
                    new_comment = Comment(
                        publication_id=str(post_id),
                        author=comment_author,
                        text_original=comment_text,
                        text_translated=text_translated,
                        sentiment_label=sentiment_label,
                        sentiment_score=sentiment_score
                    )
                    session.add(new_comment)
                    nuevos_comentarios_post += 1

                except Exception as e_comm:
                    # Error en un comentario no detiene el post
                    continue
            
            # Commit por publicación
            if nuevos_comentarios_post > 0:
                session.commit()
                nuevos_comentarios_totales += nuevos_comentarios_post
                progress_callback(f"  └ +{nuevos_comentarios_post} comentarios guardados.")

    except Exception as e:
        session.rollback()
        progress_callback(f"❌ Error general en Reddit Scraper: {e}")
    finally:
        session.close()
        progress_callback(f"\n--- ✅ Pipeline de Reddit finalizado. Total nuevos: {nuevos_comentarios_totales} ---")