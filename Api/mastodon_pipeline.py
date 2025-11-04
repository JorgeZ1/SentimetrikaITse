import sqlite3
import os
import re
from mastodon import Mastodon
from transformers import pipeline
from tqdm import tqdm # Para barras de progreso

# --- 1. CONFIGURACIÓN ---
DB_NAME = "sentiment_analysis.db"
TOKEN_FILE = "user_token.secret"
INSTANCE_URL = "https://mastodon.social" # ¡Tu instancia!
INPUT_FILE = "SentimetrikaITse/Api/mastodon_ids.txt" # Ruta corregida

def _limpiar_html(html_content):
    """Elimina etiquetas HTML simples del contenido de un toot."""
    if not html_content:
        return ""
    cleanr = re.compile('<.*?>')
    cleantext = re.sub(cleanr, '', html_content)
    cleantext = cleantext.replace("</p>", " ").replace("<br>", " ")
    return " ".join(cleantext.split())

def cargar_modelos_ia():
    """Carga los modelos de IA una sola vez."""
    print("Cargando modelos de IA (esto puede tardar)...")
    try:
        translator = pipeline("translation_en_to_es", model="Helsinki-NLP/opus-mt-en-es") # type: ignore
        sentiment_analyzer = pipeline("sentiment-analysis", model="cardiffnlp/twitter-xlm-roberta-base-sentiment") # type: ignore
        print("✅ Modelos de IA cargados.")
        return translator, sentiment_analyzer
    except Exception as e:
        print(f"❌ Error fatal al cargar modelos de IA: {e}")
        return None, None

def conectar_api_mastodon():
    """Conecta a la API de Mastodon usando el token."""
    if not os.path.exists(TOKEN_FILE):
        print(f"❌ Error: {TOKEN_FILE} no encontrado.")
        return None
    try:
        mastodon = Mastodon(
            access_token = TOKEN_FILE,
            api_base_url = INSTANCE_URL
        )
        mastodon.account_verify_credentials()
        print("✅ Conexión exitosa a Mastodon.")
        return mastodon
    except Exception as e:
        print(f"❌ Error al conectar a Mastodon: {e}")
        return None

def leer_ids_de_archivo(filepath):
    """Lee los IDs desde el archivo de texto."""
    if not os.path.exists(filepath):
        print(f"❌ Error: No se encuentra el archivo de IDs: {filepath}")
        return []
    with open(filepath, 'r') as f:
        ids = [line.strip() for line in f if line.strip()]
    print(f"Encontrados {len(ids)} IDs en {filepath}")
    return ids

def mapear_sentimiento(label_original: str) -> str:
    """Convierte las etiquetas del modelo a un formato estándar."""
    label = label_original.upper()
    if label == 'POSITIVE' or label == 'LABEL_2':
        return 'positive'
    if label == 'NEUTRAL' or label == 'LABEL_1':
        return 'neutral'
    if label == 'NEGATIVE' or label == 'LABEL_0':
        return 'negative'
    return 'neutral'

def run_mastodon_pipeline():
    """
    Función principal que ejecuta todo el proceso.
    """
    
    translator, sentiment_analyzer = cargar_modelos_ia()
    mastodon = conectar_api_mastodon()
    if not mastodon or not translator or not sentiment_analyzer:
        print("Fallo en la inicialización. Abortando.")
        return

    post_ids = leer_ids_de_archivo(INPUT_FILE)
    if not post_ids:
        print("No hay IDs para procesar. Saliendo.")
        return

    con = sqlite3.connect(DB_NAME)
    cur = con.cursor()
    
    print(f"\n--- Iniciando pipeline para {len(post_ids)} publicaciones ---")

    for post_id in tqdm(post_ids, desc="Total Publicaciones"):
        try:
            # --- A. OBTENER Y GUARDAR LA PUBLICACIÓN PRINCIPAL ---
            post = mastodon.status(post_id)
            post_content_orig = _limpiar_html(post['content'])
            post_lang = post.get('language', 'und')
            
            title_original = post_content_orig[:200]
            title_translated = title_original

            if post_lang == 'en':
                title_translated = translator(title_original, max_length=512)[0]['translation_text']
            elif post_lang != 'es':
                title_translated = f"[{post_lang}] {title_original}"

            cur.execute(
                """
                INSERT INTO publications (id, source_id, red_social, title_original, title_translated)
                VALUES (?, ?, 'Mastodon', ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    title_original = excluded.title_original,
                    title_translated = excluded.title_translated
                """,
                (post_id, post_id, title_original, title_translated)
            )

            # --- B. OBTENER Y PROCESAR COMENTARIOS ---
            context = mastodon.status_context(post_id)
            comments = context['descendants']
            
            nuevos_comentarios = 0
            if not comments:
                continue

            for comment in tqdm(comments, desc=f"Comentarios Post {post_id[:10]}", leave=False):
                try:
                    comment_id = comment['id']
                    comment_text_orig = _limpiar_html(comment['content'])
                    comment_lang = comment.get('language', 'und')
                    comment_author = comment['account']['username']
                    
                    if not comment_text_orig:
                        continue

                    # --- C. FILTRO DE IDIOMA Y ANÁLISIS ---
                    if comment_lang == 'es':
                        text_translated = comment_text_orig
                        text_para_analisis = comment_text_orig
                    elif comment_lang == 'en':
                        text_translated = translator(comment_text_orig, max_length=512)[0]['translation_text']
                        text_para_analisis = comment_text_orig
                    else:
                        continue 

                    sentiment_result = sentiment_analyzer(text_para_analisis)[0]
                    sentiment_label = mapear_sentimiento(sentiment_result['label'])
                    
                    # --- D. GUARDAR COMENTARIO EN DB (¡CAMBIO AQUÍ!) ---
                    # 
                    # Como ya no tenemos 'UNIQUE', no podemos usar 'ON CONFLICT'.
                    # Ahora hacemos la revisión manualmente:
                    
                    # 1. Verificamos si el 'source_comment_id' ya existe
                    cur.execute(
                        "SELECT 1 FROM comments WHERE source_comment_id = ?",
                        (comment_id,)
                    )
                    existe = cur.fetchone()
                    
                    # 2. Si NO existe (existe is None), lo insertamos.
                    if not existe:
                        cur.execute(
                            """
                            INSERT INTO comments (
                                publication_id, source_comment_id, lang, 
                                sentiment_label, text_translated, author
                            ) 
                            VALUES (?, ?, ?, ?, ?, ?)
                            """,
                            (post_id, comment_id, comment_lang, sentiment_label, text_translated, comment_author)
                        )
                        
                        if cur.rowcount > 0:
                            nuevos_comentarios += 1
                    
                    # Si 'existe', no hacemos nada (es un duplicado).

                except Exception as e_comment:
                    print(f"\nError procesando comentario {comment_id}: {e_comment}")

            tqdm.write(f"Publicación {post_id}: Se añadieron {nuevos_comentarios} comentarios.")
            con.commit() 

        except Exception as e_post:
            print(f"\nError fatal procesando publicación {post_id}: {e_post}")
            
    con.close()
    print("\n--- ✅ Pipeline de Mastodon finalizado ---")

if __name__ == "__main__":
    run_mastodon_pipeline()