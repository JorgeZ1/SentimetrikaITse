import praw
import os
from dotenv import load_dotenv
from .database import SessionLocal, Publication, Comment
from typing import List, Dict, Any

load_dotenv()

# Configuración
CLIENT_ID = os.getenv("REDDIT_CLIENT_ID")
CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET")
USER_AGENT = "python:SentimentApp:v2.0 (by /u/TuUsuario)"

from Api.sentiment_utils import _mapear_sentimiento

def run_reddit_scrape_opt(progress_callback, translator, sentiment_analyzer, subreddit_name, post_limit, comment_limit):
    """
    Versión PostgreSQL optimizada para Reddit con procesamiento por lotes.
    """
    if not CLIENT_ID or not CLIENT_SECRET:
        progress_callback("⚠️ ADVERTENCIA: Faltan credenciales de Reddit en el .env")
        return

    progress_callback(f"Conectando a Reddit para analizar r/{subreddit_name}...")

    try:
        reddit = praw.Reddit(client_id=CLIENT_ID, client_secret=CLIENT_SECRET, user_agent=USER_AGENT)
        reddit.user.me()
    except Exception as e:
        progress_callback(f"ℹ️ Could not log in with user. Operating in read-only mode. Error: {e}")


    session = SessionLocal()
    nuevos_comentarios_totales = 0
    nuevas_publicaciones_totales = 0

    try:
        subreddit = reddit.subreddit(subreddit_name)
        progress_callback(f"Descargando {post_limit} publicaciones de r/{subreddit_name}...")
        
        posts = list(subreddit.hot(limit=post_limit))
        post_ids = [post.id for post in posts]

        # --- GESTIÓN DE PUBLICACIONES (BATCH) ---
        progress_callback("Verificando publicaciones existentes en la base de datos...")
        existing_pubs_query = session.query(Publication.id).filter(Publication.id.in_(post_ids))
        existing_pub_ids = {pub_id[0] for pub_id in existing_pubs_query}
        
        new_pubs_to_add: List[Publication] = []
        titles_to_translate = []
        pub_id_to_title = {}

        for post in posts:
            if post.id not in existing_pub_ids:
                titles_to_translate.append(post.title)
                pub_id_to_title[post.id] = post.title
        
        translated_titles: Dict[str, str] = {}
        if translator and titles_to_translate:
            progress_callback(f"Traduciendo {len(titles_to_translate)} títulos...")
            try:
                # El modelo de Helsinki-NLP es más eficiente con lotes
                results = translator(titles_to_translate, max_length=512, batch_size=16) 
                for i, res in enumerate(results):
                    original_title = titles_to_translate[i]
                    translated_titles[original_title] = res['translation_text']
            except Exception as e:
                progress_callback(f"❌ Error al traducir títulos en lote: {e}")

        for post_id, original_title in pub_id_to_title.items():
            translated = translated_titles.get(original_title, original_title)
            new_pub = Publication(
                id=str(post_id),
                red_social='Reddit',
                title_original=original_title,
                title_translated=translated
            )
            new_pubs_to_add.append(new_pub)

        if new_pubs_to_add:
            session.bulk_save_objects(new_pubs_to_add)
            nuevas_publicaciones_totales = len(new_pubs_to_add)
            progress_callback(f"  └ +{nuevas_publicaciones_totales} publicaciones nuevas agregadas.")
        
        # --- GESTIÓN DE COMENTARIOS (BATCH) ---
        all_comments_to_process: List[Dict[str, Any]] = []
        
        progress_callback("Descargando comentarios...")
        for post in posts:
            post.comments.replace_more(limit=0)
            comments_batch = post.comments[:comment_limit]
            for comment in comments_batch:
                if hasattr(comment, 'body') and comment.body:
                    all_comments_to_process.append({
                        'publication_id': post.id,
                        'author': str(comment.author) if comment.author else "[deleted]",
                        'text_original': comment.body,
                        'comment_obj': comment 
                    })
        
        if not all_comments_to_process:
            progress_callback("No se encontraron comentarios para procesar.")
            return

        # Optimización de duplicados: buscar todos los comentarios existentes de una vez
        progress_callback("Verificando comentarios duplicados...")
        existing_comment_tuples = set()
        if post_ids:
            query = session.query(Comment.publication_id, Comment.author, Comment.text_original).filter(Comment.publication_id.in_(post_ids))
            for p_id, author, text in query:
                existing_comment_tuples.add((p_id, author, text))

        
        unique_comments = []
        for c in all_comments_to_process:
            if (c['publication_id'], c['author'], c['text_original']) not in existing_comment_tuples:
                unique_comments.append(c)

        if not unique_comments:
            progress_callback("No hay comentarios nuevos para analizar.")
            return

        progress_callback(f"Procesando {len(unique_comments)} comentarios únicos...")
        
        # Traducción en lote
        texts_to_translate = [c['text_original'] for c in unique_comments]
        translated_texts = {}
        if translator and texts_to_translate:
            progress_callback(f"Traduciendo {len(texts_to_translate)} comentarios...")
            try:
                results = translator(texts_to_translate, max_length=512, batch_size=16)
                for i, res in enumerate(results):
                    translated_texts[texts_to_translate[i]] = res['translation_text']
            except Exception as e:
                progress_callback(f"❌ Error traduciendo comentarios: {e}")
        
        # Análisis de sentimiento en lote
        texts_for_sentiment = [translated_texts.get(c['text_original'], c['text_original']) for c in unique_comments]
        sentiments = []
        if sentiment_analyzer and texts_for_sentiment:
            progress_callback(f"Analizando sentimiento de {len(texts_for_sentiment)} comentarios...")
            try:
                # Usar `truncation=True` para manejar textos largos sin errores
                results = sentiment_analyzer(texts_for_sentiment, batch_size=16, truncation=True)
                sentiments = results
            except Exception as e:
                progress_callback(f"❌ Error analizando sentimientos: {e}")

        # Crear objetos Comment en lote
        new_comments_to_add: List[Comment] = []
        for i, comment_data in enumerate(unique_comments):
            sentiment_label = 'neutral'
            sentiment_score = '0.0'
            
            if i < len(sentiments):
                s_res = sentiments[i]
                sentiment_label = _mapear_sentimiento(s_res['label'])
                sentiment_score = str(round(s_res.get('score', 0.0), 4))
            
            text_translated = translated_texts.get(comment_data['text_original'], comment_data['text_original'])
            
            new_comment = Comment(
                publication_id=comment_data['publication_id'],
                author=comment_data['author'],
                text_original=comment_data['text_original'],
                text_translated=text_translated,
                sentiment_label=sentiment_label,
                sentiment_score=sentiment_score
            )
            new_comments_to_add.append(new_comment)

        if new_comments_to_add:
            session.bulk_save_objects(new_comments_to_add)
            nuevos_comentarios_totales = len(new_comments_to_add)
            progress_callback(f"  └ +{nuevos_comentarios_totales} comentarios nuevos guardados.")

        # Commit final
        progress_callback("Guardando todos los cambios en la base de datos...")
        session.commit()

    except Exception as e:
        session.rollback()
        progress_callback(f"❌ Error general en Reddit Scraper: {e}")
    finally:
        session.close()
        progress_callback(f"\n--- ✅ Pipeline de Reddit finalizado. Nuevas publicaciones: {nuevas_publicaciones_totales}, Nuevos comentarios: {nuevos_comentarios_totales} ---")