from mastodon import Mastodon
import sqlite3
import os
import re # Para limpiar el HTML

# --- Configuración ---
USER_TOKEN_FILE = 'user_token.secret' 
INSTANCIA_URL = 'https://mastodon.social' # ¡Tu instancia!
DB_NAME = "sentiment_analysis.db"

def _conectar_api_mastodon():
    """Conecta a la API de Mastodon usando el token."""
    if not os.path.exists(USER_TOKEN_FILE):
        print(f"Error: {USER_TOKEN_FILE} no encontrado.")
        return None
    try:
        mastodon = Mastodon(
            access_token = USER_TOKEN_FILE,
            api_base_url = INSTANCIA_URL
        )
        mastodon.account_verify_credentials()
        print("Conexión exitosa a Mastodon")
        return mastodon
    except Exception as e:
        print(f"Error al conectar a Mastodon: {e}")
        return None

def _limpiar_html(html_content):
    """Elimina etiquetas HTML simples del contenido de un toot."""
    # <p>Hola</p> -> Hola
    cleanr = re.compile('<.*?>')
    cleantext = re.sub(cleanr, '', html_content)
    return cleantext

def recolectar_comentarios_mastodon():
    """
    Función principal:
    1. Lee las publicaciones de Mastodon desde nuestra DB.
    2. Va a la API de Mastodon por los comentarios (respuestas).
    3. Guarda los nuevos comentarios en nuestra DB.
    """
    
    mastodon = _conectar_api_mastodon()
    if not mastodon:
        return 0 # 0 comentarios añadidos

    try:
        con = sqlite3.connect(DB_NAME)
        # Esto permite acceder a los resultados como diccionarios
        con.row_factory = sqlite3.Row
        cur = con.cursor()

        # 1. Obtener las publicaciones que SON de Mastodon
        cur.execute("SELECT id, source_id FROM publications WHERE red_social = 'Mastodon'")
        publicaciones_db = cur.fetchall()
        
        print(f"Encontradas {len(publicaciones_db)} publicaciones de Mastodon para revisar...")
        
        nuevos_comentarios_count = 0
        
        # 2. Por cada publicación, buscar sus comentarios en la API
        for pub in publicaciones_db:
            pub_id_local = pub['id']
            pub_id_api = pub['source_id']

            if not pub_id_api:
                print(f"Saltando publicación local ID {pub_id_local} (sin source_id)")
                continue

            print(f"Buscando respuestas para la publicación: {pub_id_api}")
            
            # 3. 'status_context' nos da las respuestas (descendants)
            contexto = mastodon.status_context(pub_id_api)
            respuestas = contexto['descendants'] # 'descendants' son las respuestas

            # 4. Guardar cada respuesta en nuestra DB
            for respuesta in respuestas:
                try:
                    # Datos que nos interesan
                    comment_id_api = respuesta['id']
                    comment_text = _limpiar_html(respuesta['content'])
                    comment_lang = respuesta.get('language', 'es') # Asumir 'es' si no viene
                    
                    # 5. Insertar en la DB
                    # "ON CONFLICT(source_comment_id) DO NOTHING"
                    # evita duplicados si ya existe.
                    cur.execute(
                        """
                        INSERT INTO comments (
                            publication_id, 
                            comment_text, 
                            lang, 
                            source_comment_id,
                            sentiment_label -- Opcional, si tu pipeline lo hace luego
                        ) 
                        VALUES (?, ?, ?, ?, ?)
                        ON CONFLICT(source_comment_id) DO NOTHING
                        """,
                        (pub_id_local, comment_text, comment_lang, comment_id_api, None)
                    )
                    
                    if cur.rowcount > 0:
                        nuevos_comentarios_count += 1
                        
                except Exception as e:
                    # Ignorar si un comentario falla, ej. "UNIQUE constraint failed"
                    # (si no usamos "ON CONFLICT")
                    pass 

        con.commit() # Guardar todos los cambios
        con.close()
        
        print(f"¡Proceso completado! Se añadieron {nuevos_comentarios_count} nuevos comentarios.")
        return nuevos_comentarios_count

    except Exception as e:
        print(f"Error general en la recolección: {e}")
        return 0

# Si ejecutas este archivo directamente, que se pruebe
if __name__ == "__main__":
    recolectar_comentarios_mastodon()