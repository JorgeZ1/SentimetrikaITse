import flet as ft
from Api.database import SessionLocal, Publication, Comment
from flet import Colors

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
        "POSITIVE": ft.colors.GREEN,
        "NEGATIVE": ft.colors.RED,
        "NEUTRAL": ft.colors.GREY
    }
    iconos = {
        "POSITIVE": ft.Icons.THUMB_UP,
        "NEGATIVE": ft.Icons.THUMB_DOWN,
        "NEUTRAL": ft.Icons.CIRCLE_OUTLINED
    }
    
    color = colores.get(etiqueta, ft.colors.GREY)
    icono = iconos.get(etiqueta, ft.Icons.HELP)
    
    return ft.Row(
        [
            ft.Icon(name=icono, color=color, size=16),
            ft.Text(etiqueta.capitalize(), style=ft.TextStyle(color=color, size=12, weight=ft.FontWeight.BOLD))
        ],
        spacing=5,
    )

# --- Vista de comentarios (CON MODIFICACIONES) ---
def create_comments_view(page: ft.Page, pub_id: str):
    session = SessionLocal()
    publicacion_actual = None
    comentarios_actuales = []
    
    try:
        # 1. Obtener los datos de la publicación específica desde PostgreSQL
        publicacion_actual = session.query(Publication).filter_by(id=pub_id).first()

        # 2. Obtener los comentarios de esa publicación desde PostgreSQL
        if publicacion_actual:
            comentarios_actuales = session.query(Comment).filter_by(publication_id=pub_id).all()
            
    except Exception as e:
        print(f"Error al obtener datos de la DB para comentarios: {e}")
    finally:
        session.close()

    lista_de_comentarios = []
    titulo_publicacion = ft.Text("Publicación no encontrada", style=ft.TextStyle(color=ft.colors.RED, text_align=ft.TextAlign.CENTER))

    if publicacion_actual:
        titulo_texto = publicacion_actual.title_translated or publicacion_actual.title_original or "Título no encontrado"
        titulo_publicacion = ft.Text(
            titulo_texto,
            style=ft.TextStyle(size=20, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE), 
            text_align=ft.TextAlign.CENTER
        )

        for comentario in comentarios_actuales:
            sentiment_dict = {"etiqueta": comentario.sentiment_label}

            tarjeta_comentario = ft.Container(
                content=ft.Column([
                    ft.Row(
                        [
                            ft.Text(
                                f"Autor: {comentario.author or 'Anónimo'}", 
                                style=ft.TextStyle(weight=ft.FontWeight.BOLD, color=ft.Colors.GREY_400)
                            ),
                            get_sentiment_display(sentiment_dict)
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                    ),
                    ft.Divider(height=5, color=ft.Colors.GREY_800),
                    ft.Text(
                        comentario.text_translated or 'Texto no disponible.',
                        style=ft.TextStyle(size=15, color=ft.Colors.WHITE)
                    )
                ]),
                padding=15,
                border_radius=8,
                bgcolor="#2c3440",
            )
            lista_de_comentarios.append(tarjeta_comentario)
    else:
        titulo_publicacion = ft.Text(f"Error: No se encontró la publicación con ID {pub_id}", style=ft.TextStyle(color=ft.colors.RED))

    return ft.View(
        f"/comments/{pub_id}",
        bgcolor=BACKGROUND_COLOR,
        scroll=ft.ScrollMode.ADAPTIVE,
        appbar=ft.AppBar(
            title=ft.Text("Detalles de Publicación", style=ft.TextStyle(color=PRIMARY_TEXT_COLOR)),
            bgcolor=BACKGROUND_COLOR,
            leading=ft.IconButton(
                icon=ft.Icons.ARROW_BACK,
                icon_color=PRIMARY_TEXT_COLOR,
                on_click=lambda _: page.go("/dashboard")
            )
        ),
        controls=[
            ft.Container(
                content=titulo_publicacion,
                padding=ft.padding.symmetric(horizontal=10, vertical=5)
            ),
            ft.Divider(height=10, color=ACCENT_COLOR, thickness=1),
            ft.Column(
                controls=lista_de_comentarios,
                spacing=10
            )
        ],
        padding=10
    )