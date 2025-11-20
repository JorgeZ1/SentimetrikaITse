from mastodon import Mastodon, MastodonError
import os
from pathlib import Path
from dotenv import load_dotenv
from .database import SessionLocal, Publication, Comment
import re

# --- CONFIGURACIÓN GPS ---
current_dir = Path(__file__).resolve().parent
env_path = current_dir.parent / '.env'
load_dotenv(dotenv_path=env_path)

# RUTA AL ARCHIVO TXT
IDS_FILE_PATH = current_dir / 'mastodon_ids.txt'

API_BASE_URL = os.getenv("MASTODON_API_BASE_URL", "https://mastodon.social")
ACCESS_TOKEN = os.getenv("MASTODON_ACCESS_TOKEN")

def _limpiar_html(texto_html):
    if not texto_html: return ""
    try:
        clean = re.compile('<.*?>')
        return re.sub(clean, '', str(texto_html))
    except:
        return ""

def _extraer_id_seguro(texto):
    """
    Validación estricta. Si no es un ID válido, devuelve None.
    """
    if not texto: return None
    texto = str(texto).strip()
    
    # 1. Si es basura corta o texto, ignorar (ej: "sq", "hola")
    # Los IDs de Mastodon suelen ser largos (más de 10 dígitos) o numéricos
    if not texto.isdigit(): 
        # Intentamos ver si es una URL
        try:
            match = re.search(r'/(\d+)$', texto)
            if match: return match.group(1)
        except: pass
        return None 
    
    # 2. Si es numérico, es válido
    return texto

def _mapear_sentimiento(label_original: str) -> str:
    if not label_original: return 'neutral'
    label = label_original.upper()
    if label in ['POSITIVE', 'LABEL_2', 'POS']: return 'positive'
    if label in ['NEGATIVE', 'LABEL_0', 'NEG']: return 'negative'
    return 'neutral'

def run_mastodon_scraper(progress_callback, lista_ids_nuevos=None, translator=None, sentiment_analyzer=None):
    """
    Scraper blindado: 
    1. Filtra IDs inválidos ("sq").
    2. Salta IDs que ya existen en la DB (Optimización).
    3. Usa Timeouts para no congelar la app.
    """
    
    # --- PASO 1: GESTIÓN DEL ARCHIVO TXT ---
    if lista_ids_nuevos:
        try:
            ids_existentes = set()
            if IDS_FILE_PATH.exists():
                with open(IDS_FILE_PATH, 'r', encoding='utf-8', errors='ignore') as f:
                    ids_existentes = set(line.strip() for line in f if line.strip())
            
            ids_validos_nuevos = []
            # FILTRADO ESTRICTO
            for raw_id in lista_ids_nuevos:
                clean_id = _extraer_id_seguro(raw_id) 
                if clean_id:
                    if clean_id not in ids_existentes:
                        ids_validos_nuevos.append(clean_id)
                        ids_existentes.add(clean_id)
                else:
                    print(f"Ignorando ID inválido: {raw_id}") # Debug interno

            if ids_validos_nuevos:
                with open(IDS_FILE_PATH, 'a', encoding='utf-8') as f:
                    if IDS_FILE_PATH.exists() and IDS_FILE_PATH.stat().st_size > 0:
                        f.write("\n")
                    f.write("\n".join(ids_validos_nuevos))
                progress_callback(f"📝 {len(ids_validos_nuevos)} IDs válidos agregados.")
            elif len(lista_ids_nuevos) > 0:
                progress_callback("⚠️ IDs inválidos ignorados (basura detectada).")

        except Exception as e:
            progress_callback(f"⚠️ Error archivo txt: {e}")

    # --- PASO 2: LEER LA LISTA MAESTRA ---
    post_ids = []
    if IDS_FILE_PATH.exists():
        try:
            with open(IDS_FILE_PATH, 'r', encoding='utf-8', errors='ignore') as f:
                for line in f:
                    clean = _extraer_id_seguro(line) # Validamos también al leer
                    if clean: post_ids.append(clean)
        except Exception: pass
    
    if not post_ids:
        progress_callback("⚠️ Archivo vacío. Agrega IDs válidos.")
        return

    # --- PASO 3: CONEXIÓN ---
    progress_callback(f"📡 Conectando ({len(post_ids)} IDs)...")
    
    try:
        mastodon = Mastodon(
            access_token=ACCESS_TOKEN, 
            api_base_url=API_BASE_URL,
            request_timeout=10 # Timeout para no congelar
        )
    except Exception as e:
        progress_callback(f"❌ Error conexión: {e}")
        return

    session = SessionLocal()
    nuevos_totales = 0
    
    try:
        total = len(post_ids)
        for i, pid in enumerate(post_ids):
            try:
                # --- OPTIMIZACIÓN: VERIFICAR DB PRIMERO ---
                # Si ya existe en la base de datos, no gastamos tiempo en internet
                exists_in_db = session.query(Publication).filter_by(id=str(pid)).first()
                if exists_in_db:
                    # Opcional: Comentar el print para menos ruido
                    # progress_callback(f"⏩ ({i+1}/{total}) ID {pid} ya existe. Saltando...")
                    continue

                progress_callback(f"🔍 ({i+1}/{total}) Analizando ID: {pid}...")

                # Obtener Toot
                try:
                    toot = mastodon.status(pid)
                except Exception:
                    # Si falla (404, privado, etc), ignoramos y seguimos
                    continue

                content_clean = _limpiar_html(toot.content)
                
                # Guardar Publicación (Si pasamos el filtro de arriba, es nueva)
                title_trans = content_clean
                if translator:
                    try:
                        res = translator(content_clean, max_length=512)
                        title_trans = res[0]['translation_text']
                    except: pass

                new_pub = Publication(
                    id=str(pid),
                    red_social='Mastodon',
                    title_original=content_clean[:250],
                    title_translated=title_trans[:250]
                )
                session.add(new_pub)
                session.commit()

                # Guardar Comentarios
                try:
                    context = mastodon.status_context(pid)
                    replies = context['descendants'][:10]
                except: replies = []
                
                nuevos_en_post = 0
                for reply in replies:
                    try:
                        r_content = _limpiar_html(reply.content)
                        if not r_content: continue
                        
                        # Verificar duplicado de comentario
                        exists_c = session.query(Comment).filter_by(publication_id=str(pid), text_original=r_content).first()
                        if exists_c: continue

                        # IA
                        text_trans = r_content
                        s_label = 'neutral'
                        s_score = '0.0'
                        if translator:
                            try: text_trans = translator(r_content, max_length=512)[0]['translation_text']
                            except: pass
                        if sentiment_analyzer:
                            try:
                                res = sentiment_analyzer(text_trans[:512])[0]
                                s_label = _mapear_sentimiento(res['label'])
                                s_score = str(round(res.get('score', 0), 4))
                            except: pass

                        new_c = Comment(
                            publication_id=str(pid),
                            author=str(reply.account.username),
                            text_original=r_content,
                            text_translated=text_trans,
                            sentiment_label=s_label,
                            sentiment_score=s_score
                        )
                        session.add(new_c)
                        nuevos_en_post += 1
                    except: continue

                if nuevos_en_post > 0:
                    session.commit()
                    nuevos_totales += nuevos_en_post
                    progress_callback(f"   └ 💾 +{nuevos_en_post} respuestas.")
            
            except Exception as e_id:
                print(f"Error ID {pid}: {e_id}")
                continue

    except Exception as e:
        session.rollback()
        progress_callback(f"❌ Error crítico: {e}")
    finally:
        session.close()
        if nuevos_totales > 0:
            progress_callback(f"✨ Éxito: {nuevos_totales} nuevos.")
        else:
            progress_callback("💤 Terminado (No hubo datos nuevos).")