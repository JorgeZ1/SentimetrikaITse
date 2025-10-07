import praw
import json
import os

# --- 1. Configuración de Credenciales de Reddit ---
# Es una buena práctica leerlas desde variables de entorno.
# Asegúrate de haber configurado REDDIT_CLIENT_ID y REDDIT_CLIENT_SECRET
CLIENT_ID = os.getenv("REDDIT_CLIENT_ID")
CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET")
USER_AGENT = "python:DataScraper:v1.2 (by /u/TuNombreDeUsuario)"

# --- 2. Parámetros de la Extracción ---
nombre_subreddit = 'AskReddit' # Asegúrate de que el subreddit exista
limite_publicaciones = 20
limite_comentarios_por_post = 100
archivo_salida = "comentarios_estructurados.json"

# Verifica si las credenciales fueron cargadas
if CLIENT_ID == "TU_CLIENT_ID" or CLIENT_SECRET == "TU_CLIENT_SECRET":
    print("⚠️ ADVERTENCIA: No se encontraron las credenciales en las variables de entorno.")
    print("Usando valores de ejemplo. Por favor, actualízalos directamente en el script.")

# --- 3. Lógica de Extracción ---
print("Iniciando conexión con Reddit...")
try:
    reddit = praw.Reddit(
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        user_agent=USER_AGENT
    )
    print("✅ Conexión con Reddit exitosa.")
except Exception as e:
    print(f"❌ Error al conectar con Reddit: {e}")
    exit()

# La lista principal ahora contendrá objetos de publicación
publicaciones_extraidas = []
print(f"\nExtrayendo publicaciones y comentarios de r/{nombre_subreddit}...")

try:
    subreddit = reddit.subreddit(nombre_subreddit)
    for submission in subreddit.hot(limit=limite_publicaciones):
        print(f"  > Procesando publicación: \"{submission.title[:40]}...\"")
        
        # Creamos un diccionario para la publicación actual
        publicacion_actual = {
            "id_publicacion": submission.id,
            "titulo_publicacion": submission.title,
            "url_publicacion": f"https://reddit.com{submission.permalink}",
            "puntuacion_publicacion": submission.score,
            "comentarios": [] # Una lista para guardar sus comentarios
        }
        
        submission.comments.replace_more(limit=0)
        
        for comment in submission.comments[:limite_comentarios_por_post]:
            if hasattr(comment, 'body') and comment.body.strip():
                comentario_info = {
                    "id_comentario": comment.id,
                    "autor": str(comment.author),
                    "texto": comment.body,
                    "puntuacion_comentario": comment.score,
                }
                # Añadimos el comentario a la lista de la publicación actual
                publicacion_actual["comentarios"].append(comentario_info)
        
        # Añadimos la publicación (con todos sus comentarios) a la lista principal
        publicaciones_extraidas.append(publicacion_actual)

except Exception as e:
    print(f"\n❌ Ocurrió un error durante la extracción: {e}")
    exit()

# --- 4. Guardar los datos en el nuevo archivo JSON estructurado ---
try:
    with open(archivo_salida, 'w', encoding='utf-8') as f:
        json.dump(publicaciones_extraidas, f, ensure_ascii=False, indent=4)
    print(f"\n✅ ¡Éxito! Se guardaron {len(publicaciones_extraidas)} publicaciones en '{archivo_salida}'.")
except Exception as e:
    print(f"\n❌ Error al guardar el archivo JSON: {e}")