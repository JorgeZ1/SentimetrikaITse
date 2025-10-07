import flet as ft
import sqlite3
from collections import Counter

DB_NAME = "sentiment_analysis.db"

# La función get_impact_icon no cambia
def get_impact_icon(impact: str):
    icons = {
        "positive": ft.Icon(ft.Icons.SENTIMENT_SATISFIED, color="green"),
        "negative": ft.Icon(ft.Icons.SENTIMENT_DISSATISFIED, color="red"),
        "neutral": ft.Icon(ft.Icons.SENTIMENT_NEUTRAL, color="gray"),
    }
    # Aseguramos que la comparación sea en minúsculas
    return icons.get(impact.lower(), ft.Icon(ft.Icons.HELP))

# --- FUNCIÓN TOTALMENTE REESCRITA ---
def procesar_y_agrupar_publicaciones():
    """
    Obtiene las publicaciones desde la base de datos y calcula su impacto general.
    """
    con = sqlite3.connect(DB_NAME)
    # Esto permite acceder a los resultados como diccionarios (ej: row['id'])
    con.row_factory = sqlite3.Row
    cur = con.cursor()

    # 1. Obtenemos todas las publicaciones
    cur.execute("SELECT * FROM publications")
    publications = cur.fetchall()

    lista_procesada = []
    for pub in publications:
        # 2. Por cada publicación, obtenemos sus sentimientos
        cur.execute("SELECT sentiment_label FROM comments WHERE publication_id = ?", (pub['id'],))
        sentiments = [row['sentiment_label'] for row in cur.fetchall() if row['sentiment_label']]
        
        impacto_general = "neutral"
        if sentiments:
            # 3. Calculamos el impacto más común
            conteo = Counter(sentiments)
            impacto_general = conteo.most_common(1)[0][0]
        
        lista_procesada.append({
            "id": pub['id'],
            # Usa el título traducido, si no, el original
            "titulo": pub['title_translated'] or pub['title_original'] or "Título Desconocido",
            "impacto_general": impacto_general
        })

    con.close()
    return lista_procesada