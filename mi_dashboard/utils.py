import flet as ft
import json
import pathlib
from collections import Counter

# --- ESTA FUNCIÓN NO CAMBIA ---
def get_impact_icon(impact: str):
    """Devuelve un ícono según el tipo de impacto."""
    icons = {
        "positivo": ft.Icon(ft.Icons.SENTIMENT_SATISFIED, color="green"),
        "negativo": ft.Icon(ft.Icons.SENTIMENT_DISSATISFIED, color="red"),
        "neutral": ft.Icon(ft.Icons.SENTIMENT_NEUTRAL, color="gray"),
    }
    return icons.get(impact, ft.Icon(ft.Icons.HELP))

# --- ESTA FUNCIÓN TIENE LA CORRECCIÓN ---
def cargar_datos_analizados():
    """
    Carga los resultados del análisis de sentimientos desde 'resultados_analisis.json'.
    """
    try:
        # --- LA CORRECCIÓN ESTÁ AQUÍ ---
        # Desde 'utils.py', subimos 3 niveles para llegar a la carpeta raíz 'APP-AI'
        # mi_dashboard -> SentimetrikaITse -> APP-AI
        ruta_base = pathlib.Path(__file__).parent.parent.parent
        ruta_json = ruta_base / "resultados_analisis.json"
        
        if not ruta_json.is_file():
            print(f"ADVERTENCIA: No se encontró el archivo en la ruta esperada: '{ruta_json}'.")
            return []
            
        with open(ruta_json, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"ERROR: No se pudo cargar o decodificar el archivo JSON: {e}")
        return []

def procesar_y_agrupar_publicaciones():
    """
    Toma la lista de comentarios, los agrupa por publicación y calcula el impacto general.
    """
    # MODIFICADO: Ahora el nombre de la variable es más claro.
    datos_analizados = cargar_datos_analizados()
    publicaciones = {}

    # MODIFICADO: El nombre del iterador es más claro.
    for publicacion_data in datos_analizados:
        pub_id = publicacion_data.get("id_publicacion", "desconocido")
        
        if pub_id not in publicaciones:
            publicaciones[pub_id] = {
                "id": pub_id,
                # --- MODIFICACIÓN CLAVE ---
                # Intenta obtener el título traducido, si no existe, usa el original.
                "titulo": publicacion_data.get("titulo_traducido", publicacion_data.get("titulo_publicacion", "Publicación Desconocida")),
                "comentarios": [],
                "sentimientos": []
            }
        
        publicaciones[pub_id]["comentarios"].append(publicacion_data)
        etiqueta = publicacion_data.get("analisis_sentimiento", {}).get("etiqueta", "NEUTRAL").lower()
        publicaciones[pub_id]["sentimientos"].append(etiqueta)

    for pub_id, data in publicaciones.items():
        if not data["sentimientos"]:
            data["impacto_general"] = "neutral"
            continue
        
        conteo = Counter(data["sentimientos"])
        data["impacto_general"] = conteo.most_common(1)[0][0]
        
    return list(publicaciones.values())