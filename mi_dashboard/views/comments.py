import flet as ft
import json

# --- Paleta de colores (sin cambios) ---
BACKGROUND_COLOR = "#1f2630"
CARD_COLOR = "#2c3440"
PRIMARY_TEXT_COLOR = ft.Colors.WHITE
SECONDARY_TEXT_COLOR = ft.Colors.GREY_400
ACCENT_COLOR = "#3399ff"

# --- AÑADIDO: Función para obtener ícono y texto del sentimiento ---
def get_sentiment_display(sentiment_data: dict):
    """Devuelve un ft.Row con un ícono y texto para el sentimiento."""
    etiqueta = sentiment_data.get("etiqueta", "NEUTRAL").upper()
    
    colores = {
        "POSITIVE": "green",
        "NEGATIVE": "red",
        "NEUTRAL": "grey"
    }
    iconos = {
        "POSITIVE": ft.Icons.THUMB_UP,
        "NEGATIVE": ft.Icons.THUMB_DOWN,
        "NEUTRAL": ft.Icons.CIRCLE_OUTLINED
    }
    
    color = colores.get(etiqueta, "grey")
    icono = iconos.get(etiqueta, ft.Icons.HELP)
    
    return ft.Row(
        [
            ft.Icon(name=icono, color=color, size=16),
            ft.Text(etiqueta.capitalize(), color=color, size=12, weight="bold")
        ],
        spacing=5,
    )

# --- Función para cargar datos (sin cambios) ---
def cargar_datos():
    try:
        # Ajusta esta ruta si es necesario para tu estructura
        with open('resultados_analisis.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

# --- Vista de comentarios (CON MODIFICACIONES) ---
def create_comments_view(page: ft.Page, pub_id: str):
    datos_completos = cargar_datos()
    publicacion_actual = next((pub for pub in datos_completos if pub.get("id_publicacion") == pub_id), None)
            
    lista_de_comentarios = []
    
    if publicacion_actual:
        # --- MODIFICADO: Lógica para encontrar el título correcto ---
        titulo_texto = publicacion_actual.get("titulo_traducido", publicacion_actual.get("titulo_publicacion", "Título no encontrado"))
        titulo_publicacion = ft.Text(
            titulo_texto,
            size=20, # Tamaño ajustado
            weight="bold",
            color=PRIMARY_TEXT_COLOR,
            text_align=ft.TextAlign.CENTER # Centrado
        )

        for comentario in publicacion_actual.get("comentarios", []):
            tarjeta_comentario = ft.Container(
                content=ft.Column([
                    # --- MODIFICADO: Fila para Autor y Sentimiento ---
                    ft.Row(
                        [
                            ft.Text(f"Autor: {comentario.get('autor', 'Anónimo')}", weight="bold", color=SECONDARY_TEXT_COLOR),
                            get_sentiment_display(comentario.get("analisis_sentimiento", {}))
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                    ),
                    ft.Divider(height=5, color=ft.Colors.GREY_800),
                    ft.Text(
                        comentario.get('texto_traducido', 'Texto no disponible.'),
                        size=15,
                        color=PRIMARY_TEXT_COLOR
                    )
                ]),
                padding=15,
                border_radius=8,
                bgcolor=CARD_COLOR,
            )
            lista_de_comentarios.append(tarjeta_comentario)
    else:
        titulo_publicacion = ft.Text(f"Error: No se encontró la publicación con ID {pub_id}", color="red")

    # --- El resto de la vista no cambia ---
    return ft.View(
        f"/comments/{pub_id}",
        bgcolor=BACKGROUND_COLOR,
        scroll=ft.ScrollMode.ADAPTIVE,
        appbar=ft.AppBar(
            title=ft.Text("Detalles de Publicación", color=PRIMARY_TEXT_COLOR),
            bgcolor=BACKGROUND_COLOR,
            leading=ft.IconButton(
                icon=ft.Icons.ARROW_BACK,
                icon_color=PRIMARY_TEXT_COLOR,
                on_click=lambda _: page.go("/dashboard")
            )
        ),
        controls=[
            ft.Container( # Contenedor para el título con padding
                content=titulo_publicacion,
                padding=ft.padding.symmetric(horizontal=10, vertical=5)
            ),
            ft.Divider(height=10, color=ACCENT_COLOR, thickness=1),
            ft.Column(
                controls=lista_de_comentarios,
                spacing=10 # Espaciado entre comentarios
            )
        ],
        padding=10
    )