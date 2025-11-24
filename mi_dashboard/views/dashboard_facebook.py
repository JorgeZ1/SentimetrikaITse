import flet as ft
import threading 
from flet import Colors, Icons, FontWeight, TextThemeStyle, Offset, BoxShadow
from Api.database import SessionLocal, Publication
from Api.facebook_scraper_opt import run_facebook_scrape_opt 

# --- LÓGICA DE DATOS (Sin cambios) ---
def get_facebook_data():
    """Consulta optimizada a DB"""
    session = SessionLocal()
    publications = []
    comments_map = {} 
    try:
        pubs_db = session.query(Publication).filter(Publication.red_social == 'Facebook').all()
        pubs_db.reverse() 
        for p in pubs_db:
            publications.append(p)
            comments_map[p.id] = [c for c in p.comments]
    except Exception as e:
        print(f"Error DB: {e}")
    finally:
        session.close()
    return publications, comments_map

# --- UTILIDADES DE DISEÑO ---
def get_sentiment_color(sentiment):
    if sentiment == 'positive': return Colors.GREEN_600
    if sentiment == 'negative': return Colors.RED_500
    return Colors.GREY_500

def get_sentiment_badge(sentiment, score):
    """Muestra la etiqueta de sentimiento (ej: POSITIVE), eliminando el score numérico."""
    color = get_sentiment_color(sentiment)
    
    # Usamos un texto limpio para el badge
    sentiment_display = sentiment.upper() 
    
    return ft.Container(
        content=ft.Row([
            # 🚨 ICONO Y TEXTO DEL SENTIMIENTO LITERAL
            ft.Text(sentiment_display, size=11, color=Colors.WHITE, weight=FontWeight.BOLD)
        ], spacing=2, alignment=ft.MainAxisAlignment.CENTER),
        bgcolor=color,
        padding=ft.padding.symmetric(horizontal=8, vertical=2),
        border_radius=12,
        tooltip=f"Sentimiento: {sentiment_display}"
    )

# --- VISTA PRINCIPAL ---
def create_dashboard_view(page: ft.Page) -> ft.View:
    
    selected_post_id = None
    
    posts_column = ft.Column(spacing=8, scroll=ft.ScrollMode.AUTO, expand=True)
    comments_column = ft.Column(spacing=10, scroll=ft.ScrollMode.AUTO, expand=True)
    
    header_comments = ft.Text("Selecciona una publicación", style=TextThemeStyle.TITLE_MEDIUM, color=Colors.GREY_500)

    publications, comments_map = get_facebook_data()

    if not publications:
        publications_list_view.controls.append(
            ft.Text("No se encontraron datos de Facebook en PostgreSQL.")
        )

    # --- Eventos ---
    def on_post_click(e):
        post_id = e.control.data 
        
        selected_post = next((p for p in publications if p.id == post_id), None)
        if selected_post:
            # Accedemos con punto (.) porque ahora son objetos
            title_text = selected_post.title_translated or "Sin título"
            selected_post_title.value = f"Comentarios de: {title_text[:50]}..."
        
        comments_list_view.controls.clear()
        comments_for_post = comments_map.get(post_id, [])
        
        if not comments_for_post:
            comments_list_view.controls.append(
                ft.ListTile(title=ft.Text("No se encontraron comentarios."))
            )
        else:
            for comment in comments_for_post:
                # Accedemos con punto (.)
                comments_list_view.controls.append(
                    ft.Card(
                        ft.ListTile(
                            leading=get_sentiment_icon(comment.sentiment_label),
                            title=ft.Text(f"@{comment.author}", weight=ft.FontWeight.BOLD),
                            subtitle=ft.Text(comment.text_translated or "")
                        ),
                        elevation=2
                    )
                )
        page.update()

    # --- Llenar Lista Publicaciones ---
    for post in publications:
        comment_count = len(comments_map.get(post.id, []))
        publications_list_view.controls.append(
            ft.Card(
                content=ft.Container(
                    ft.ListTile(
                        title=ft.Text(post.title_translated or "Sin texto", weight=ft.FontWeight.BOLD),
                        subtitle=ft.Text(post.title_original or "", italic=True, color=Colors.GREY_500),
                        trailing=ft.Text(f"{comment_count} Comentarios", color=Colors.BLUE_800),
                        on_click=on_post_click,
                        data=post.id
                    ),
                    padding=10
                ),
                elevation=4,
            )
        )

    return ft.View(
        "/dashboard/facebook",
        [
            # 1. Barra Superior
            ft.AppBar(
                title=ft.Text("📘 Dashboard de Facebook"),
                bgcolor=Colors.BLUE_800,
                actions=[
                    ft.IconButton(
                        icon=Icons.REFRESH,
                        icon_color=Colors.WHITE,
                        tooltip="Actualizar datos de Facebook",
                        on_click=run_update_process 
                    ),
                    ft.Container(width=10)
                ]
            ),
            
            # 2. Cuerpo dividido
            ft.Container(
                content=ft.Row([
                    # COLUMNA IZQUIERDA (Lista de Posts)
                    ft.Container(
                        content=ft.Column([
                            ft.Container(
                                content=ft.Text("PUBLICACIONES", size=11, weight=FontWeight.BOLD, color=Colors.GREY_500),
                                padding=ft.padding.only(left=10, top=15, bottom=5)
                            ),
                            posts_column 
                        ]),
                        expand=4, # 40% del ancho
                        bgcolor=Colors.WHITE,
                        border=ft.border.only(right=ft.BorderSide(1, Colors.GREY_200))
                    ),
                    
                    # COLUMNA DERECHA (Detalle y Comentarios)
                    ft.Container(
                        content=ft.Column([
                            ft.Container(
                                content=ft.Column([
                                    ft.Text("ANÁLISIS DE COMENTARIOS", size=11, weight=FontWeight.BOLD, color=Colors.BLUE_GREY_400),
                                    ft.Container(height=5),
                                    header_comments,
                                ]),
                                padding=20,
                                bgcolor=Colors.GREY_50,
                                border=ft.border.only(bottom=ft.BorderSide(1, Colors.GREY_200))
                            ),
                            ft.Container(
                                content=comments_column,
                                padding=20,
                                expand=True
                            )
                        ]),
                        expand=7, # 60% del ancho
                        bgcolor=Colors.GREY_50
                    )
                ], spacing=0, expand=True),
                expand=True
            )
        ],
        padding=0
    )