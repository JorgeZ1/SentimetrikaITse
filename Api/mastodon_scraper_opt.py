import os
import re
import pathlib
from mastodon import Mastodon
from .database import SessionLocal, Publication, Comment
from typing import List, Dict, Any

def _limpiar_html(html_content):
    """Elimina etiquetas HTML simples del contenido de un toot."""
    if not html_content:
        return ""
    cleanr = re.compile('<.*?>')
    cleantext = re.sub(cleanr, '', html_content)
    cleantext = cleantext.replace("</p>", " ").replace("<br>", " ")
    return " ".join(cleantext.split())

def _conectar_api_mastodon(progress_callback):
    """Conecta a la API de Mastodon usando el token."""
    TOKEN_FILE = pathlib.Path(__file__).parent / "user_token.secret"
    INSTANCE_URL = "https://mastodon.social"

    if not os.path.exists(TOKEN_FILE):
        progress_callback(f"❌ Error: {TOKEN_FILE} no encontrado.")
        return None
    try:
        mastodon = Mastodon(
            access_token=TOKEN_FILE.read_text().strip(),
            api_base_url=INSTANCE_URL
        )
        mastodon.account_verify_credentials()
        progress_callback("✅ Conexión exitosa a Mastodon.")
        return mastodon
    except Exception as e:
        progress_callback(f"❌ Error al conectar a Mastodon: {e}")
        return None

def _leer_ids_de_archivo(progress_callback):
    """Lee los IDs desde el archivo de texto y devuelve una lista de IDs únicos."""
    INPUT_FILE = pathlib.Path(__file__).parent / "mastodon_ids.txt"
    if not os.path.exists(INPUT_FILE):
        progress_callback(f"❌ Error: No se encuentra el archivo de IDs: {INPUT_FILE}")
        return []
    with open(INPUT_FILE, 'r') as f:
        ids = [line.strip() for line in f if line.strip()]
    
    unique_ids = list(set(ids))
    
    if len(unique_ids) < len(ids):
        progress_callback(f"Se encontraron {len(ids) - len(unique_ids)} IDs duplicados y se han eliminado.")
        
    progress_callback(f"Encontrados {len(unique_ids)} IDs únicos en {INPUT_FILE}")
    return unique_ids

from Api.sentiment_utils import _mapear_sentimiento

def run_mastodon_scrape_opt(progress_callback, translator, sentiment_analyzer):
    """
    Versión PostgreSQL optimizada para Mastodon con procesamiento por lotes.
    """
    mastodon = _conectar_api_mastodon(progress_callback)
    if not mastodon:
        progress_callback("Fallo en la inicialización de Mastodon. Abortando.")
        return

    post_ids = _leer_ids_de_archivo(progress_callback)
    if not post_ids:
        progress_callback("No hay IDs para procesar. Saliendo.")
        return

    session = SessionLocal()
    nuevos_comentarios_totales = 0
    nuevas_publicaciones_totales = 0

    progress_callback(f"\n--- Iniciando pipeline de Mastodon para {len(post_ids)} publicaciones ---")

    try:
        # --- GESTIÓN DE PUBLICACIONES (BATCH) ---
        progress_callback("Verificando publicaciones existentes...")
        existing_pubs_query = session.query(Publication.id).filter(Publication.id.in_(post_ids))
        existing_pub_ids = {pub_id[0] for pub_id in existing_pubs_query}
        
        new_post_ids = [pid for pid in post_ids if pid not in existing_pub_ids]
        
        new_pubs_to_add: List[Publication] = []
        titles_to_translate: Dict[str, str] = {}

        if new_post_ids:
            progress_callback(f"Descargando {len(new_post_ids)} publicaciones nuevas...")
            for post_id in new_post_ids:
                try:
                    post = mastodon.status(post_id)
                    title_original = _limpiar_html(post['content'])[:200]
                    lang = post.get('language', 'und')
                    
                    if lang == 'en' and translator:
                        titles_to_translate[title_original] = post_id
                    
                    new_pubs_to_add.append(Publication(
                        id=str(post_id),
                        red_social='Mastodon',
                        title_original=title_original,
                        title_translated=title_original 
                    ))
                except Exception as e:
                    progress_callback(f"Error descargando post {post_id}: {e}")

        if titles_to_translate:
            progress_callback(f"Traduciendo {len(titles_to_translate)} títulos...")
            try:
                results = translator(list(titles_to_translate.keys()), max_length=512, batch_size=16)
                for i, res in enumerate(results):
                    original_title = list(titles_to_translate.keys())[i]
                    post_id_to_update = titles_to_translate[original_title]
                    for pub in new_pubs_to_add:
                        if pub.id == post_id_to_update:
                            pub.title_translated = res['translation_text']
                            break
            except Exception as e:
                progress_callback(f"❌ Error al traducir títulos en lote: {e}")

        if new_pubs_to_add:
            session.bulk_save_objects(new_pubs_to_add)
            nuevas_publicaciones_totales = len(new_pubs_to_add)
            progress_callback(f"  └ +{nuevas_publicaciones_totales} publicaciones nuevas agregadas.")

        # --- GESTIÓN DE COMENTARIOS (BATCH) ---
        progress_callback("Descargando comentarios...")
        all_comments_to_process: List[Dict[str, Any]] = []
        for post_id in post_ids:
            try:
                context = mastodon.status_context(post_id)
                for comment in context['descendants']:
                    text = _limpiar_html(comment['content'])
                    if text:
                        all_comments_to_process.append({
                            'publication_id': post_id,
                            'author': comment['account']['username'],
                            'text_original': text,
                            'lang': comment.get('language', 'und')
                        })
            except Exception as e:
                progress_callback(f"Error descargando comentarios para {post_id}: {e}")

        if not all_comments_to_process:
            progress_callback("No se encontraron comentarios nuevos para procesar.")
            return

        progress_callback("Verificando comentarios duplicados...")
        query = session.query(Comment.publication_id, Comment.author, Comment.text_original).filter(Comment.publication_id.in_(post_ids))
        existing_comment_tuples = {(p_id, author, text) for p_id, author, text in query}
        
        unique_comments = [c for c in all_comments_to_process if (c['publication_id'], c['author'], c['text_original']) not in existing_comment_tuples]

        if not unique_comments:
            progress_callback("No hay comentarios nuevos para analizar.")
            return
            
        progress_callback(f"Procesando {len(unique_comments)} comentarios únicos...")
        
        texts_to_translate = [c['text_original'] for c in unique_comments if c['lang'] == 'en' and translator]
        translated_texts = {}
        if texts_to_translate:
            try:
                results = translator(texts_to_translate, max_length=512, batch_size=16)
                for i, res in enumerate(results):
                    translated_texts[texts_to_translate[i]] = res['translation_text']
            except Exception as e:
                progress_callback(f"❌ Error traduciendo comentarios: {e}")

        texts_for_sentiment = [translated_texts.get(c['text_original'], c['text_original']) for c in unique_comments]
        sentiments = []
        if sentiment_analyzer and texts_for_sentiment:
            try:
                sentiments = sentiment_analyzer(texts_for_sentiment, batch_size=16, truncation=True)
            except Exception as e:
                progress_callback(f"❌ Error analizando sentimientos: {e}")

        new_comments_to_add: List[Comment] = []
        for i, comment_data in enumerate(unique_comments):
            sentiment_label = 'neutral'
            sentiment_score = '0.0'
            
            if i < len(sentiments):
                s_res = sentiments[i]
                sentiment_label = _mapear_sentimiento(s_res['label'])
                sentiment_score = str(round(s_res.get('score', 0.0), 4))
            
            text_translated = translated_texts.get(comment_data['text_original'], comment_data['text_original'])
            
            new_comments_to_add.append(Comment(
                publication_id=comment_data['publication_id'],
                author=comment_data['author'],
                text_original=comment_data['text_original'],
                text_translated=text_translated,
                sentiment_label=sentiment_label,
                sentiment_score=sentiment_score
            ))

        if new_comments_to_add:
            session.bulk_save_objects(new_comments_to_add)
            nuevos_comentarios_totales = len(new_comments_to_add)
            progress_callback(f"  └ +{nuevos_comentarios_totales} comentarios nuevos guardados.")

        progress_callback("Guardando todos los cambios en la base de datos...")
        session.commit()

    except Exception as e:
        session.rollback()
        progress_callback(f"❌ Error general en pipeline Mastodon: {e}")
    finally:
        session.close()
        progress_callback(f"\n--- ✅ Pipeline de Mastodon finalizado. Nuevas publicaciones: {nuevas_publicaciones_totales}, Nuevos comentarios: {nuevos_comentarios_totales} ---")