import flet as ft
from backend.database import SessionLocal, Publication, Comment
from flet import Colors, Icons
from typing import Dict, List, Any
import os
from backend.report_generator import PDFReportGenerator
from frontend.utils import show_snackbar

# --- Configuración Visual ---
SOCIAL_CONFIG = {
    "Facebook": {"icon": Icons.FACEBOOK, "color": "#1877F2"},
    "Reddit":   {"icon": Icons.REDDIT, "color": "#FF4500"},
    "Mastodon": {"icon": Icons.ROCKET_LAUNCH, "color": "#6364FF"}, 
    "Default":  {"icon": Icons.PUBLIC, "color": "#3399ff"}
}

def get_network_style(network_name: str):
    key = network_name if network_name in SOCIAL_CONFIG else "Default"
    return SOCIAL_CONFIG[key]

# --- UI Helpers ---

def get_sentiment_badge(sentiment_label: str) -> ft.Container:
    """
    Crea una etiqueta visual para el sentimiento.
    CORRECCIÓN: Usamos colores directos (RED/GREEN) para asegurar visibilidad.
    """
    # Normalizar etiqueta
    raw_label = sentiment_label.upper() if sentiment_label else "NEUTRAL"
    
    # Mapeo robusto que busca palabras clave
    if "POS" in raw_label: # Para POSITIVE o POSITIVO
        label = "POSITIVO"
        icon = Icons.THUMB_UP
        # Usamos una opacidad del color principal para el fondo
        bg_color = ft.Colors.with_opacity(0.2, ft.Colors.GREEN)
        text_color = ft.Colors.GREEN
    elif "NEG" in raw_label: # Para NEGATIVE o NEGATIVO
        label = "NEGATIVO"
        icon = Icons.THUMB_DOWN
        bg_color = ft.Colors.with_opacity(0.2, ft.Colors.RED)
        text_color = ft.Colors.RED
    else:
        label = "NEUTRAL"
        icon = Icons.REMOVE
        bg_color = ft.Colors.with_opacity(0.2, ft.Colors.GREY)
        text_color = ft.Colors.GREY

    return ft.Container(
        content=ft.Row([
            ft.Icon(icon, size=14, color=text_color),
            ft.Text(label, size=11, weight=ft.FontWeight.BOLD, color=text_color)
        ], spacing=4, alignment=ft.MainAxisAlignment.CENTER),
        bgcolor=bg_color,
        padding=ft.padding.symmetric(horizontal=8, vertical=4),
        border_radius=12,
        border=ft.border.all(1, color=ft.Colors.with_opacity(0.3, text_color))
    )

def generate_avatar(author_name: str) -> ft.CircleAvatar:
    name = author_name if author_name else "?"
    initial = name[0].upper() if name else "?"
    return ft.CircleAvatar(
        content=ft.Text(initial, weight=ft.FontWeight.BOLD, color="onPrimaryContainer"),
        bgcolor="primaryContainer", 
        radius=18
    )

def generate_single_pdf_report(page: ft.Page, publication: Publication, comments: List[Comment]):
    try:
        generator = PDFReportGenerator()
        file_path = generator.generate_single_publication_report(publication, comments)
        show_snackbar(page, f"✅ Reporte generado: {os.path.basename(file_path)}")
        try:
            os.startfile(os.path.dirname(file_path))
        except:
            pass
    except Exception as e:
        show_snackbar(page, f"❌ Error PDF: {str(e)}", is_error=True)

# --- Componentes de Tarjeta ---

def create_main_post_card(pub: Publication, network_style: dict) -> ft.Container:
    """Tarjeta de la Publicación Principal"""
    # Detectar si hay traducción real
    has_translation = bool(pub.title_translated and pub.title_original and pub.title_translated != pub.title_original)
    
    # TEXTO PRINCIPAL: Preferimos el traducido (Español)
    main_text = pub.title_translated or pub.title_original or "Sin contenido"

    return ft.Container(
        content=ft.Column([
            # Cabecera
            ft.Row([
                ft.Icon(network_style["icon"], color=network_style["color"], size=30),
                ft.Column([
                    ft.Text(pub.red_social, color=network_style["color"], weight=ft.FontWeight.BOLD, size=12),
                    ft.Text("Publicación Principal", color="outline", size=10)
                ], spacing=0)
            ]),
            ft.Divider(color=ft.Colors.TRANSPARENT, height=10),
            
            # --- ESPAÑOL (Principal) ---
            ft.Text(
                main_text,
                size=18,
                color="onSurface", 
                weight=ft.FontWeight.W_500,
                selectable=True
            ),
            
            # --- INGLÉS / ORIGINAL (Secundario) ---
            ft.Container(
                visible=has_translation,
                content=ft.Column([
                    ft.Divider(height=10, color="outlineVariant"),
                    ft.Text("Original (Inglés):", size=10, color="outline", weight="bold"),
                    ft.Text(pub.title_original or "", italic=True, color="onSurfaceVariant", size=14),
                ]),
                bgcolor="surfaceVariant", 
                padding=10,
                border_radius=8,
                margin=ft.margin.only(top=5)
            )
        ]),
        bgcolor="surface", 
        padding=20,
        border_radius=15,
        border=ft.border.all(1, ft.Colors.with_opacity(0.3, network_style["color"])), 
        shadow=ft.BoxShadow(blur_radius=5, color="shadow", offset=ft.Offset(0, 2))
    )

def create_comment_card(comment: Comment) -> ft.Container:
    """Burbuja de comentario"""
    # Detectar si hay traducción
    has_translation = bool(comment.text_translated and comment.text_original and comment.text_translated != comment.text_original)
    
    # TEXTO PRINCIPAL = TRADUCCIÓN (Español)
    main_text = comment.text_translated or comment.text_original or "..."

    return ft.Container(
        content=ft.Row([
            # Avatar
            ft.Column([
                generate_avatar(comment.author),
                ft.Container(expand=True) 
            ], alignment=ft.MainAxisAlignment.START),
            
            # Contenido
            ft.Container(
                content=ft.Column([
                    # Cabecera del comentario
                    ft.Row([
                        ft.Text(comment.author or "Anónimo", weight=ft.FontWeight.BOLD, color="onSurfaceVariant", size=14),
                        get_sentiment_badge(comment.sentiment_label)
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    
                    ft.Divider(height=5, color=ft.Colors.TRANSPARENT),
                    
                    # --- 1. ESPAÑOL / TRADUCIDO (Grande) ---
                    ft.Text(main_text, color="onSurface", size=15, selectable=True),

                    # --- 2. INGLÉS / ORIGINAL (Pequeño) ---
                    ft.Container(
                        visible=has_translation,
                        content=ft.Column([
                            ft.Divider(height=5, color="outlineVariant"),
                            ft.Text("Original:", size=9, color="outline", weight="bold"),
                            ft.Text(comment.text_original or "", size=12, color="onSurfaceVariant", italic=True, selectable=True)
                        ]),
                        padding=ft.padding.only(top=2)
                    )
                ]),
                # Fondo burbuja
                bgcolor="surfaceContainerHighest",
                border_radius=ft.border_radius.only(top_right=15, bottom_left=15, bottom_right=15),
                padding=15,
                expand=True
            )
        ], 
        vertical_alignment=ft.CrossAxisAlignment.START),
        padding=ft.padding.only(bottom=10)
    )

# --- Vista Principal ---

def create_comments_view(page: ft.Page, pub_id: str) -> ft.View:
    session = SessionLocal()
    publicacion_actual: Publication = None
    comentarios_actuales: List[Comment] = []
    
    try:
        publicacion_actual = session.query(Publication).filter_by(id=pub_id).first()
        if publicacion_actual:
            comentarios_actuales = session.query(Comment).filter_by(publication_id=pub_id).all()
    except Exception as e:
        print(f"Error DB: {e}")
    finally:
        session.close()

    if not publicacion_actual:
        network_name = "Default"
    else:
        network_name = publicacion_actual.red_social
        
    network_style = get_network_style(network_name)

    content_controls = []
    
    if publicacion_actual:
        content_controls.append(create_main_post_card(publicacion_actual, network_style))
        
        content_controls.append(
            ft.Container(
                content=ft.Row([
                    ft.Icon(Icons.CHAT_BUBBLE, color="outline", size=16),
                    ft.Text(f"{len(comentarios_actuales)} Comentarios", color="outline", weight="bold")
                ]),
                padding=ft.padding.symmetric(vertical=15)
            )
        )
        
        if not comentarios_actuales:
            content_controls.append(
                ft.Container(
                    content=ft.Column([
                        ft.Icon(Icons.COMMENTS_DISABLED_OUTLINED, color="outline", size=50),
                        ft.Text("No hay comentarios registrados", color="outline")
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    alignment=ft.alignment.center,
                    padding=30
                )
            )
        else:
            for comment in comentarios_actuales:
                content_controls.append(create_comment_card(comment))
    else:
        content_controls.append(
            ft.Container(
                content=ft.Text("⚠️ Publicación no encontrada o eliminada", color="error", size=20),
                alignment=ft.alignment.center,
                padding=50
            )
        )

    def go_back(e):
        if publicacion_actual:
            target = f"/dashboard/{publicacion_actual.red_social.lower()}"
            page.go(target)
        else:
            page.go("/social_select")

    # --- Lógica de Cambio de Tema ---
    
    # Definir el icono inicial basado en el estado actual
    initial_icon = Icons.DARK_MODE if page.theme_mode == ft.ThemeMode.LIGHT else Icons.LIGHT_MODE
    
    theme_icon = ft.IconButton(
        icon=initial_icon,
        icon_color="onSurface",
        tooltip="Cambiar Tema (Día/Noche)"
    )

    def toggle_theme(e):
        if page.theme_mode == ft.ThemeMode.LIGHT:
            page.theme_mode = ft.ThemeMode.DARK
            theme_icon.icon = Icons.LIGHT_MODE
            show_snackbar(page, "🌙 Modo Oscuro Activado")
        else:
            page.theme_mode = ft.ThemeMode.LIGHT
            theme_icon.icon = Icons.DARK_MODE 
            show_snackbar(page, "☀️ Modo Claro Activado")
        
        page.update()

    theme_icon.on_click = toggle_theme

    return ft.View(
        f"/comments/{pub_id}",
        bgcolor="background", 
        appbar=ft.AppBar(
            title=ft.Text("Detalle de la Conversación", style=ft.TextStyle(color="onSurface", weight="bold", size=18)),
            bgcolor="surface", 
            center_title=True,
            elevation=0,
            leading=ft.IconButton(
                icon=Icons.ARROW_BACK,
                icon_color="onSurface",
                on_click=go_back,
                tooltip="Volver"
            ),
            actions=[
                theme_icon,
                ft.Container(
                    content=ft.IconButton(
                        icon=Icons.PICTURE_AS_PDF,
                        icon_color="onSurface",
                        on_click=lambda _: generate_single_pdf_report(page, publicacion_actual, comentarios_actuales),
                        tooltip="Exportar PDF"
                    ),
                    padding=ft.padding.only(right=10)
                )
            ]
        ),
        controls=[
            ft.Container(
                content=ft.ListView(
                    controls=content_controls,
                    padding=20,
                    spacing=0, 
                ),
                expand=True 
            )
        ],
        padding=0
    )