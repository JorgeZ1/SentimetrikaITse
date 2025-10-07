import flet as ft
import sqlite3

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
DB_NAME = "sentiment_analysis.db"
# --- Vista de comentarios (CON MODIFICACIONES) ---
def create_comments_view(page: ft.Page, pub_id: str):
    con = sqlite3.connect(DB_NAME)
    con.row_factory = sqlite3.Row
    cur = con.cursor()

    # 1. Obtener los datos de la publicación específica
    cur.execute("SELECT * FROM publications WHERE id = ?", (pub_id,))
    publicacion_actual = cur.fetchone()

    # 2. Obtener los comentarios de esa publicación
    cur.execute("SELECT * FROM comments WHERE publication_id = ?", (pub_id,))
    comentarios_actuales = cur.fetchall()
    
    con.close()

    lista_de_comentarios = []
    
    if publicacion_actual:
        titulo_texto = publicacion_actual['title_translated'] or publicacion_actual['title_original'] or "Título no encontrado"
        titulo_publicacion = ft.Text(
            titulo_texto,
            size=20, weight="bold", color=ft.Colors.WHITE, text_align=ft.TextAlign.CENTER
        )

        for comentario in comentarios_actuales:
            # Creamos un diccionario de sentimiento para la función auxiliar
            sentiment_dict = {"etiqueta": comentario['sentiment_label']}

            tarjeta_comentario = ft.Container(
                content=ft.Column([
                    ft.Row(
                        [
                            ft.Text(f"Autor: {comentario['author'] or 'Anónimo'}", weight="bold", color=ft.Colors.GREY_400),
                            get_sentiment_display(sentiment_dict)
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                    ),
                    ft.Divider(height=5, color=ft.Colors.GREY_800),
                    ft.Text(
                        comentario['text_translated'] or 'Texto no disponible.',
                        size=15,
                        color=ft.Colors.WHITE
                    )
                ]),
                padding=15,
                border_radius=8,
                bgcolor="#2c3440",
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