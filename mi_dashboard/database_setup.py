import sqlite3
import json

# Nombre del archivo de la base de datos
DB_NAME = "sentiment_analysis.db"
# Nombre de tu archivo JSON
JSON_FILE = "resultados_analisis.json"

def setup_database():
    """
    Lee los datos del JSON y los inserta en una base de datos SQLite.
    Este script está diseñado para ejecutarse una sola vez.
    """
    # 1. Conectar a la base de datos (se creará si no existe)
    con = sqlite3.connect(DB_NAME)
    cur = con.cursor()

    # 2. Crear las tablas si no existen
    # Tabla para las publicaciones
    cur.execute("""
        CREATE TABLE IF NOT EXISTS publications (
            id TEXT PRIMARY KEY,
            title_original TEXT,
            title_translated TEXT
        )
    """)

    # Tabla para los comentarios
    cur.execute("""
        CREATE TABLE IF NOT EXISTS comments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            publication_id TEXT,
            author TEXT,
            text_translated TEXT,
            sentiment_label TEXT,
            FOREIGN KEY (publication_id) REFERENCES publications (id)
        )
    """)

    # 3. Cargar los datos del archivo JSON
    try:
        with open(JSON_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"Error: No se encontró el archivo '{JSON_FILE}'. Asegúrate de que está en la misma carpeta.")
        return

    # 4. Insertar los datos en las tablas
    for publication in data:
        pub_id = publication.get("id_publicacion")
        if not pub_id:
            continue

        # Insertar en la tabla de publicaciones (ignorando si ya existe)
        cur.execute(
            "INSERT OR IGNORE INTO publications (id, title_original, title_translated) VALUES (?, ?, ?)",
            (
                pub_id,
                publication.get("titulo_publicacion"),
                publication.get("titulo_traducido")
            )
        )

        # Insertar los comentarios asociados
        for comment in publication.get("comentarios", []):
            cur.execute(
                "INSERT INTO comments (publication_id, author, text_translated, sentiment_label) VALUES (?, ?, ?, ?)",
                (
                    pub_id,
                    comment.get("autor"),
                    comment.get("texto_traducido"),
                    comment.get("analisis_sentimiento", {}).get("etiqueta")
                )
            )
    
    # 5. Guardar los cambios y cerrar la conexión
    con.commit()
    con.close()
    print(f"¡Base de datos '{DB_NAME}' creada y poblada con éxito!")

if __name__ == "__main__":
    setup_database()