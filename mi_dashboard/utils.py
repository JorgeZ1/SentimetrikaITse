import flet as ft
import sqlite3
from collections import Counter
# Importar para la versión de Flet del usuario
from flet import Icons, Colors 

DB_NAME = "sentiment_analysis.db"

def get_impact_icon(impact: str):
    """
    Devuelve un icono de Flet basado en la cadena de impacto.
    Adaptado para la versión de Flet del usuario.
    """
    icons = {
        # Usamos ft.Icon(name=...) y Colors
        "positive": ft.Icon(name=Icons.SENTIMENT_SATISFIED, color=Colors.GREEN),
        "negative": ft.Icon(name=Icons.SENTIMENT_DISSATISFIED, color=Colors.RED),
        "neutral": ft.Icon(name=Icons.SENTIMENT_NEUTRAL, color=Colors.GREY),
    }
    # Aseguramos que la comparación sea en minúsculas
    return icons.get(impact.lower(), ft.Icon(name=Icons.HELP))

# --- FUNCIÓN PRINCIPAL (ACTUALIZADA) ---
def procesar_y_agrupar_publicaciones():
    """
    Obtiene TODAS las publicaciones. 
    1. Calcula el impacto basado en 'sentiment_label' (la emoción).
    2. Si no hay comentarios con emoción, asigna 'neutral' por defecto.
    """
    con = sqlite3.connect(DB_NAME)
    con.row_factory = sqlite3.Row # Para acceder como diccionarios
    cur = con.cursor()

    try:
        cur.execute("SELECT id, title_translated, title_original, red_social FROM publications")
        publications = cur.fetchall()
    except sqlite3.OperationalError as e:
        print(f"ERROR: ¿Faltan columnas en la DB? {e}")
        con.close()
        return [] 

    lista_procesada = []
    for pub in publications:
        
        # --- ¡AQUÍ ESTÁ LA CORRECCIÓN! ---
        # 
        # Buscamos por la EMOCIÓN ('sentiment_label')
        # en lugar de por 'text_translated'.
        cur.execute(
            "SELECT sentiment_label FROM comments WHERE publication_id = ? AND sentiment_label IS NOT NULL", 
            (pub['id'],)
        )
        # --- FIN DE LA CORRECCIÓN ---
        
        sentiments = [row['sentiment_label'] for row in cur.fetchall() if row['sentiment_label']]
        
        impacto_general = "" # Inicializar

        if not sentiments:
            # Si NO hay comentarios con emoción, asignamos "neutral"
            # Esto asegura que la publicación aparezca.
            impacto_general = "neutral"
        else:
            # Si SÍ hay, calculamos el impacto real
            conteo = Counter(sentiments)
            impacto_general = conteo.most_common(1)[0][0]

        # 2. Añadimos la publicación a la lista (ahora se añaden todas)
        lista_procesada.append({
            "id": pub['id'],
            "titulo": pub['title_translated'] or pub['title_original'] or "Título Desconocido",
            "impacto_general": impacto_general, # Tendrá el impacto real o "neutral"
            "red_social": pub['red_social'] or "Desconocida" 
        })

    con.close()
    return lista_procesada