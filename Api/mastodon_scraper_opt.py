import os
import re
import pathlib
from mastodon import Mastodon
# --- CAMBIO: Importamos la DB de Postgres ---
from .database import SessionLocal, Publication, Comment

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
        progress_callback(f"   Asegúrate de que 'user_token.secret' contenga tu token.")
        return None

def _leer_ids_de_archivo(progress_callback):
    """Lee los IDs desde el archivo de texto."""
    INPUT_FILE = pathlib.Path(__file__).parent / "mastodon_ids.txt"
    if not os.path.exists(INPUT_FILE):
        progress_callback(f"❌ Error: No se encuentra el archivo de IDs: {INPUT_FILE}")
        return []
    with open(INPUT_FILE, 'r') as f:
        ids = [line.strip() for line in f if line.strip()]
    progress_callback(f"Encontrados {len(ids)} IDs en {INPUT_FILE}")
    return ids

def _mapear_sentimiento(label_original: str) -> str:
    """Convierte las etiquetas del modelo a un formato estándar."""
    label = label_original.upper()
    if label in ['POSITIVE', 'LABEL_2', 'POS']: return 'positive'
    if label in ['NEGATIVE', 'LABEL_0', 'NEG']: return 'negative'
    return 'neutral'

def run_mastodon_scrape_opt(progress_callback, translator, sentiment_analyzer):
    """
    Versión PostgreSQL optimizada para Mastodon.
    """
    
    # 1. Conexión API
    mastodon = _conectar_api_mastodon(progress_callback)
    if not mastodon:
        progress_callback("Fallo en la inicialización de Mastodon. Abortando.")
        return

    # 2. Leer IDs
    post_ids = _leer_ids_de_archivo(progress_callback)
    if not post_ids:
        progress_callback("No hay IDs para procesar. Saliendo.")
        return

    # 3. Iniciar Sesión DB
    session = SessionLocal()
    nuevos_comentarios_totales = 0

    progress_callback(f"\n--- Iniciando pipeline de Mastodon para {len(post_ids)} publicaciones ---")

    try:
        for post_id in post_ids:
            progress_callback(f"Procesando publicación: {post_id}")
            try:
                # Obtener datos de la API
                post = mastodon.status(post_id)
                post_content_orig = _limpiar_html(post['content'])
                post_lang = post.get('language', 'und')
                
                # Preparar Título
                title_original = post_content_orig[:200] # Cortamos para el título si es muy largo
                title_translated = title_original

                # Traducción del Post (Título)
                if post_lang == 'en' and translator:
                    try:
                        trans_res = translator(title_original, max_length=512)
                        if trans_res:
                            title_translated = trans_res[0]['translation_text']
                    except:
                        pass # Fallback
                elif post_lang != 'es':
                    title_translated = f"[{post_lang}] {title_original}"

                # --- GESTIÓN DE PUBLICACIÓN (ORM) ---
                # Verificar si existe
                existing_pub = session.query(Publication).filter_by(id=str(post_id)).first()
                
                if not existing_pub:
                    new_pub = Publication(
                        id=str(post_id),
                        red_social='Mastodon',
                        title_original=title_original,
                        title_translated=title_translated
                    )
                    session.add(new_pub)
                    session.commit() # Guardar publicación
                else:
                    # Opcional: Actualizar si ya existe
                    pass

                # --- GESTIÓN DE COMENTARIOS ---
                context = mastodon.status_context(post_id)
                comments = context['descendants']
                
                nuevos_comentarios_post = 0
                
                if not comments:
                    progress_callback(f"  └ Publicación {post_id}: No hay comentarios.")
                    continue

                for comment in comments:
                    try:
                        comment_text_orig = _limpiar_html(comment['content'])
                        comment_lang = comment.get('language', 'und')
                        comment_author = comment['account']['username']
                        
                        if not comment_text_orig:
                            continue

                        # Verificar duplicados en DB (Buscamos por Post + Autor + Texto)
                        # Esto evita que se repitan si corres el script 2 veces
                        existing_comment = session.query(Comment).filter_by(
                            publication_id=str(post_id),
                            author=comment_author,
                            text_original=comment_text_orig
                        ).first()

                        if existing_comment:
                            continue

                        # Lógica de traducción
                        text_translated = comment_text_orig
                        text_para_analisis = comment_text_orig

                        if comment_lang == 'es':
                            pass
                        elif comment_lang == 'en' and translator:
                            try:
                                trans_res = translator(comment_text_orig, max_length=512)
                                if trans_res:
                                    text_translated = trans_res[0]['translation_text']
                                    text_para_analisis = comment_text_orig # Analizamos el original en inglés si el modelo lo soporta, o el traducido
                            except:
                                pass
                        
                        # Análisis de Sentimiento
                        if sentiment_analyzer:
                            sentiment_result = sentiment_analyzer(text_para_analisis[:512])[0]
                            sentiment_label = _mapear_sentimiento(sentiment_result['label'])
                            sentiment_score = str(round(sentiment_result.get('score', 0.0), 4))
                        else:
                            sentiment_label = 'neutral'
                            sentiment_score = '0.0'
                        
                        # Crear Comentario
                        new_comment = Comment(
                            publication_id=str(post_id),
                            author=comment_author,
                            text_original=comment_text_orig,
                            text_translated=text_translated,
                            sentiment_label=sentiment_label,
                            sentiment_score=sentiment_score
                        )
                        session.add(new_comment)
                        nuevos_comentarios_post += 1

                    except Exception as e_comment:
                        # Errores puntuales en un comentario no detienen el proceso
                        pass

                if nuevos_comentarios_post > 0:
                    session.commit()
                    nuevos_comentarios_totales += nuevos_comentarios_post
                    progress_callback(f"  └ +{nuevos_comentarios_post} comentarios guardados.")

            except Exception as e_post:
                session.rollback()
                progress_callback(f"\nError procesando publicación {post_id}: {e_post}")
                
    except Exception as e_main:
        progress_callback(f"Error general en pipeline Mastodon: {e_main}")
        
    finally:
        session.close() # Cerrar conexión
        progress_callback(f"\n--- ✅ Pipeline de Mastodon finalizado. Total nuevos: {nuevos_comentarios_totales} ---")