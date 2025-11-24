import facebook
import os
from pathlib import Path  # <--- El GPS
from dotenv import load_dotenv

# --- CAMBIO IMPORTANTE: Importamos la DB de Postgres ---
from .database import SessionLocal, Publication, Comment

# --- 1. CONFIGURACIÓN DEL GPS Y ENV ---
current_file = Path(__file__).resolve()
# Subimos 3 niveles: views -> mi_dashboard -> RAIZ
project_root = current_file.parent.parent.parent
env_path = project_root / '.env'

print(f"🔍 [System] Buscando .env en: {env_path}")
load_dotenv(dotenv_path=env_path)

# Verificación rápida en consola
if os.getenv("PAGE_ACCESS_TOKEN"):
    print("✅ [System] Token detectado en variables de entorno.")
else:
    print("❌ [System] ALERTA: El token sigue siendo None.")

# Credenciales
PAGE_ACCESS_TOKEN = os.getenv("PAGE_ACCESS_TOKEN")
PAGE_ID = os.getenv("PAGE_ID")

def _mapear_sentimiento_fb(label_original: str) -> str:
    """Convierte etiquetas del modelo a formato estándar"""
    label = label_original.upper()
    if label in ['POSITIVE', 'LABEL_2', 'POS']: return 'positive'
    if label in ['NEGATIVE', 'LABEL_0', 'NEG']: return 'negative'
    return 'neutral'

def run_facebook_scrape_opt(progress_callback, translator, sentiment_analyzer):
    """
    Versión PostgreSQL optimizada.
    """
    
    # Validaciones iniciales
    if not PAGE_ACCESS_TOKEN or not PAGE_ID:
        progress_callback("❌ Error: Faltan las credenciales PAGE_ACCESS_TOKEN o PAGE_ID en el archivo .env")
        return

    progress_callback("Iniciando conexión con la API Graph de Facebook...")
    
    # 1. Conexión a Facebook
    try:
        graph = facebook.GraphAPI(access_token=PAGE_ACCESS_TOKEN)
        # Prueba de conexión (pedimos nombre de la página)
        page_info = graph.get_object(id=PAGE_ID, fields='name')
        progress_callback(f"✅ Conectado a página: {page_info.get('name', 'Desconocida')}")
    except facebook.GraphAPIError as e:
        progress_callback(f"❌ Error API Facebook: {e.message}")
        return
    except Exception as e:
        progress_callback(f"❌ Error de Red/Conexión: {e}")
        return

    # 2. Iniciar Sesión de Base de Datos (PostgreSQL)
    session = SessionLocal()
    nuevos_comentarios_totales = 0
    nuevas_publicaciones_totales = 0

    try:
        progress_callback(f"Obteniendo feed de la página {PAGE_ID}...")
        posts = graph.get_connections(id=PAGE_ID, connection_name='feed', fields='id,message,created_time')
        
        if 'data' not in posts:
            progress_callback("⚠️ No se encontraron publicaciones.")
            return

        for post in posts['data']:
            post_id = post['id']
            # Si no hay mensaje, usamos un placeholder
            post_content = post.get('message', 'Publicación multimedia/sin texto')
            
            progress_callback(f"Procesando Post ID: {post_id}...")

            # --- GESTIÓN DE PUBLICACIÓN (ORM) ---
            # Verificamos si el post ya existe en Postgres
            existing_pub = session.query(Publication).filter_by(id=post_id).first()
            
            if not existing_pub:
                # Crear nueva publicación
                new_pub = Publication(
                    id=post_id,
                    red_social="Facebook",
                    title_original=post_content,
                    title_translated=post_content # Asumimos mismo título si no se traduce el post
                )
                session.add(new_pub)
                # Hacemos commit parcial para asegurar que la ID exista antes de meter comentarios
                session.commit() 
            else:
                # Opcional: Actualizar contenido si cambió (aquí lo omitimos por velocidad)
                pass

            # --- GESTIÓN DE COMENTARIOS ---
            nuevos_comentarios_post = 0
            comments = graph.get_connections(id=post_id, connection_name='comments', fields='id,message,from', summary=True)
            
            for comment in comments.get('data', []):
                try:
                    comment_text_orig = comment.get('message', '')
                    comment_author = comment.get('from', {}).get('name', 'Anónimo')

                    if not comment_text_orig:
                        continue

                    # Verificamos duplicados en DB
                    # Buscamos si ya existe un comentario con el mismo texto, autor y post_id
                    # (Postgres es muy rápido haciendo esto)
                    existing_comment = session.query(Comment).filter_by(
                        publication_id=post_id,
                        text_original=comment_text_orig,
                        author=comment_author
                    ).first()

                    if existing_comment:
                        continue # Ya existe, saltamos

                    # --- TRADUCCIÓN Y ANÁLISIS ---
                    text_translated = comment_text_orig
                    
                    # Intento de traducción
                    try:
                        trans_res = translator(comment_text_orig, max_length=512)
                        if trans_res and 'translation_text' in trans_res[0]:
                            text_translated = trans_res[0]['translation_text']
                    except Exception:
                        pass # Fallback al original si falla traducción

                    # Análisis de sentimiento
                    sentiment_res = sentiment_analyzer(text_translated[:512])[0]
                    sentiment_label = _mapear_sentimiento_fb(sentiment_res['label'])
                    sentiment_score = str(round(sentiment_res.get('score', 0.0), 4))

                    # Crear objeto Comentario
                    new_comment = Comment(
                        publication_id=post_id,
                        author=comment_author,
                        text_original=comment_text_orig,
                        text_translated=text_translated,
                        sentiment_label=sentiment_label,
                        sentiment_score=sentiment_score
                    )
                    
                    session.add(new_comment)
                    nuevos_comentarios_post += 1

                except Exception as e_comm:
                    print(f"Error en comentario individual: {e_comm}")
                    continue

            # Commit de los comentarios de ESTE post
            if nuevos_comentarios_post > 0:
                session.commit()
                nuevos_comentarios_totales += nuevos_comentarios_post
                progress_callback(f"  └ +{nuevos_comentarios_post} comentarios guardados.")
            
    except Exception as e:
        session.rollback()
        progress_callback(f"❌ Error crítico durante el proceso: {e}")
    finally:
        session.close() # IMPORTANTE: Cerrar conexión
        progress_callback(f"\n✅ Finalizado. Total comentarios nuevos: {nuevos_comentarios_totales}")  