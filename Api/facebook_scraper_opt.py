import facebook
import os
from pathlib import Path  # <--- El GPS
from dotenv import load_dotenv
from dateutil import parser # Para manejar las fechas de Facebook (pip install python-dateutil)
from Api.database import SessionLocal, Publication, Comment

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


# --- 2. FUNCIONES AUXILIARES ---
def _mapear_sentimiento_fb(label_original: str) -> str:
    """Normaliza la etiqueta que devuelve el modelo de IA"""
    label = label_original.upper()
    if label in ['POSITIVE', 'LABEL_2', 'POS']: return 'positive'
    if label in ['NEGATIVE', 'LABEL_0', 'NEG']: return 'negative'
    return 'neutral'

def run_facebook_scrape_opt(progress_callback, translator, sentiment_analyzer):
    """
    Scraper Maestro: Conecta a Graph API, descarga, analiza y guarda en Postgres.
    """
    
    # Validación inicial
    if not PAGE_ACCESS_TOKEN or not PAGE_ID:
        progress_callback("❌ Error: Faltan credenciales en el archivo .env")
        return

    progress_callback("📡 Iniciando conexión segura con Facebook API...")

    # Conexión a Facebook
    try:
        graph = facebook.GraphAPI(access_token=PAGE_ACCESS_TOKEN)
        # Prueba de conexión (pedimos nombre de la página)
        page_info = graph.get_object(id=PAGE_ID, fields='name')
        page_name = page_info.get('name', 'Página Desconocida')
        progress_callback(f"✅ Conectado exitosamente a: {page_name}")
    except facebook.GraphAPIError as e:
        progress_callback(f"❌ Error de Permisos de Facebook: {e.message}")
        return
    except Exception as e:
        progress_callback(f"❌ Error de Red/Conexión: {e}")
        return

    # Iniciar Sesión de Base de Datos
    session = SessionLocal()
    nuevos_comentarios_totales = 0

    try:
        progress_callback("📥 Descargando últimos 10 posts del Feed...")
        
        # Solicitud al API (Traemos ID, Mensaje y Fecha)
        posts = graph.get_connections(
            id=PAGE_ID, 
            connection_name='feed', 
            fields='id,message,created_time',
            limit=10
        )

        if 'data' not in posts or not posts['data']:
            progress_callback("⚠️ La página no tiene publicaciones recientes.")
            return

        # Iterar sobre los posts
        for post in posts['data']:
            post_id = post['id']
            post_content = post.get('message', 'Publicación multimedia (Foto/Video)')
            post_date_str = post.get('created_time')
            
            progress_callback(f"🔎 Procesando Post ID: {post_id}...")

            # --- A. GUARDAR PUBLICACIÓN ---
            existing_pub = session.query(Publication).filter_by(id=post_id).first()
            
            if not existing_pub:
                # ELIMINAMOS LA LÍNEA DE FECHA PORQUE TU BASE DE DATOS NO LA TIENE
                new_pub = Publication(
                    id=post_id,
                    red_social="Facebook",
                    title_original=post_content[:250],
                    title_translated=post_content[:250]
                    # created_at=fecha_obj  <--- ESTA LÍNEA LA BORRAMOS O COMENTAMOS
                )
                session.add(new_pub)
                session.commit()
            # --- B. DESCARGAR COMENTARIOS ---
            comments = graph.get_connections(
                id=post_id, 
                connection_name='comments', 
                fields='id,message,from', 
                summary=True,
                limit=50 # Límite de comentarios por post
            )
            
            nuevos_en_post = 0
            
            for comment in comments.get('data', []):
                try:
                    c_text = comment.get('message', '')
                    c_author = comment.get('from', {}).get('name', 'Anónimo')
                    
                    if not c_text: continue

                    # Verificar si ya existe en DB
                    exists = session.query(Comment).filter_by(
                        publication_id=post_id, 
                        text_original=c_text,
                        author=c_author
                    ).first()
                    
                    if exists: continue

                    # --- C. INTELIGENCIA ARTIFICIAL ---
                    # 1. Traducción
                    try:
                        # Si el texto es muy corto, no traducir
                        if len(c_text) < 3: 
                            c_trans = c_text
                        else:
                            trans = translator(c_text, max_length=512)
                            c_trans = trans[0]['translation_text']
                    except:
                        c_trans = c_text # Fallback

                    # 2. Sentimiento
                    sent = sentiment_analyzer(c_trans[:512])[0]
                    label = _mapear_sentimiento_fb(sent['label'])
                    score = str(round(sent.get('score', 0), 4))

                    # Guardar Comentario
                    new_comment = Comment(
                        publication_id=post_id,
                        author=c_author,
                        text_original=c_text,
                        text_translated=c_trans,
                        sentiment_label=label,
                        sentiment_score=score
                    )
                    session.add(new_comment)
                    nuevos_en_post += 1

                except Exception as e_comm:
                    print(f"Error saltando comentario: {e_comm}")
                    continue

            # Guardar lote de comentarios
            if nuevos_en_post > 0:
                session.commit()
                nuevos_comentarios_totales += nuevos_en_post
                progress_callback(f"   └ 💾 +{nuevos_en_post} comentarios guardados.")
            
    except Exception as e:
        session.rollback()
        progress_callback(f"❌ Error crítico durante el proceso: {e}")
    finally:
        session.close()
        if nuevos_comentarios_totales > 0:
            progress_callback(f"✨ ¡PROCESO TERMINADO! Se agregaron {nuevos_comentarios_totales} comentarios nuevos.")
        else:
            progress_callback("💤 Proceso terminado. No se encontraron comentarios nuevos.")