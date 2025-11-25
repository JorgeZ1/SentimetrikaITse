import flet as ft
from backend.database import SessionLocal, Publication, Comment
from flet import Colors
from typing import Dict, List, Any
import os
from backend.report_generator import PDFReportGenerator
from frontend.utils import show_snackbar

# --- Paleta de colores (sin cambios) ---
BACKGROUND_COLOR: str = "#1f2630"
CARD_COLOR: str = "#2c3440"
PRIMARY_TEXT_COLOR: str = ft.Colors.WHITE
SECONDARY_TEXT_COLOR: str = ft.Colors.GREY_400
ACCENT_COLOR: str = "#3399ff"

# --- AÑADIDO: Función para obtener ícono y texto del sentimiento ---
def get_sentiment_display(sentiment_data: Dict[str, Any]) -> ft.Row:
    """Devuelve un ft.Row con un ícono y texto para el sentimiento."""
    etiqueta: str = sentiment_data.get("etiqueta", "NEUTRAL").upper()
    
    colores: Dict[str, str] = {
        "POSITIVE": ft.Colors.GREEN,
        "NEGATIVE": ft.Colors.RED,
        "NEUTRAL": ft.Colors.GREY
    }
    iconos: Dict[str, str] = {
        "POSITIVE": ft.Icons.THUMB_UP,
        "NEGATIVE": ft.Icons.THUMB_DOWN,
        "NEUTRAL": ft.Icons.CIRCLE_OUTLINED
    }
    
    color: str = colores.get(etiqueta, ft.Colors.GREY)
    icono: str = iconos.get(etiqueta, ft.Icons.HELP)
    
    return ft.Row(
        [
            ft.Icon(name=icono, color=color, size=16),
            ft.Text(etiqueta.capitalize(), style=ft.TextStyle(color=color, size=12, weight=ft.FontWeight.BOLD))
        ],
        spacing=5,
    )

def generate_single_pdf_report(page: ft.Page, publication: Publication, comments: List[Comment]):
    """Genera el reporte PDF para una sola publicación y notifica al usuario"""
    try:
        generator = PDFReportGenerator()
        file_path = generator.generate_single_publication_report(publication, comments)
        
        show_snackbar(page, f"✅ Reporte generado: {os.path.basename(file_path)}")
    except Exception as e:
        show_snackbar(page, f"❌ Error generando reporte: {str(e)}", is_error=True)

# --- Vista de comentarios (CON MODIFICACIONES) ---
def create_comments_view(page: ft.Page, pub_id: str) -> ft.View:
    session = SessionLocal()
    publicacion_actual: Publication = None
    comentarios_actuales: List[Comment] = []
    
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

    lista_de_comentarios: List[ft.Container] = []
    titulo_publicacion: ft.Text = ft.Text("Publicación no encontrada", style=ft.TextStyle(color=ft.Colors.RED), text_align=ft.TextAlign.CENTER)

    if publicacion_actual:
        titulo_texto: str = publicacion_actual.title_translated or publicacion_actual.title_original or "Título no encontrado"
        titulo_publicacion = ft.Text(
            titulo_texto,
            style=ft.TextStyle(size=20, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
            text_align=ft.TextAlign.CENTER
        )

        for comentario in comentarios_actuales:
            sentiment_dict: Dict[str, str] = {"etiqueta": comentario.sentiment_label}

            tarjeta_comentario: ft.Container = ft.Container(
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
        titulo_publicacion = ft.Text(f"Error: No se encontró la publicación con ID {pub_id}", style=ft.TextStyle(color=ft.Colors.RED))

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
                on_click=lambda _: page.go(f"/dashboard/{publicacion_actual.red_social.lower()}") if publicacion_actual else page.go("/social_select") # Volver al dashboard anterior
            ),
            actions=[
                ft.IconButton(
                    icon=ft.Icons.PICTURE_AS_PDF,
                    icon_color=PRIMARY_TEXT_COLOR,
                    on_click=lambda _: generate_single_pdf_report(page, publicacion_actual, comentarios_actuales),
                    tooltip="Generar Reporte PDF"
                )
            ]
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