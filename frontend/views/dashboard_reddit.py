import flet as ft
from flet import Colors, Icons
from typing import List, Dict, Tuple
import os
import threading
import time
from pathlib import Path

# --- Imports de tu proyecto ---
from backend.database import SessionLocal, Publication, Comment, delete_publication_by_id, delete_publications_by_network
from backend.reddit_scraper import run_reddit_scrape_opt
from frontend.theme import *
from frontend.utils import show_snackbar
from backend.report_generator import PDFReportGenerator

# --- BLOQUE DE SEGURIDAD DE COLORES ---
try:
    REDDIT_COLOR 
except NameError:
    REDDIT_COLOR = "#FF4500"

try:
    ACCENT_COLOR 
except NameError:
    try:
        ACCENT_COLOR = ACCENT 
    except NameError:
        ACCENT_COLOR = "#FF4500"
        ACCENT = "#FF4500"

try:
    PRIMARY
except NameError:
    PRIMARY = ft.Colors.BLUE

try:
    ERROR
except NameError:
    ERROR = ft.Colors.RED

# --- Constantes de Estilo Visual ---
BG_COLOR = "background"
CARD_BG = "surface"
TEXT_MAIN = "onSurface"
TEXT_SUB = "onSurfaceVariant"

SHADOW_CARD = ft.BoxShadow(
    spread_radius=1,
    blur_radius=3,
    color=ft.Colors.with_opacity(0.1, ft.Colors.BLACK),
    offset=ft.Offset(0, 2),
)

def generate_pdf_report(page: ft.Page, publications: List[Publication], comments_map: Dict[str, List[Comment]]):
    if not publications:
        show_snackbar(page, "No hay publicaciones para generar el reporte.", is_error=True)
        return
    try:
        show_snackbar(page, "Generando PDF...", is_error=False)
        generator = PDFReportGenerator()
        file_path = generator.generate_report("Reddit", publications, comments_map)
        show_snackbar(page, f"Reporte guardado: {os.path.basename(file_path)}")
        try:
            os.startfile(os.path.dirname(file_path))
        except:
            pass 
    except Exception as e:
        print(f"Error PDF: {e}")
        show_snackbar(page, f"Error generando reporte: {str(e)}", is_error=True)

def get_reddit_data() -> Tuple[List[Publication], Dict[str, List[Comment]]]:
    session = SessionLocal()
    pubs: List[Publication] = []
    c_map: Dict[str, List[Comment]] = {} 
    try:
        pubs_db = session.query(Publication).filter(Publication.red_social == 'Reddit').all()
        for p in pubs_db:
            pubs.append(p)
            c_map[p.id] = [c for c in p.comments]
    except Exception as e:
        print(f"Error leyendo DB: {e}")
    finally:
        session.close()
    return pubs, c_map

def create_dashboard_view(page: ft.Page) -> ft.View:
    
    # --- 1. Gestión de Estado ---
    initial_pubs, initial_comments = get_reddit_data()
    publications = list(initial_pubs)     
    comments_map = dict(initial_comments) 

    # --- 2. Componentes UI ---
    publications_column = ft.Column(spacing=10, scroll=ft.ScrollMode.HIDDEN)
    
    subreddit_input = ft.TextField(
        label="Subreddit",
        value="Python",
        hint_text="Ej: technology",
        text_size=12,
        bgcolor="surfaceVariant",
        border_radius=8,
        prefix_text="r/",
        height=40,
        content_padding=10
    )

    # Controles para límites del scraper (tuerca)
    post_limit_slider = ft.Slider(min=1, max=30, value=20, divisions=29, label="Posts: 20", width=260)
    comment_limit_slider = ft.Slider(min=1, max=30, value=10, divisions=29, label="Comentarios: 10", width=260)

    def on_post_limit_change(e):
        v = int(e.control.value)
        post_limit_slider.label = f"Posts: {v}"
        try: page.update()
        except: pass

    def on_comment_limit_change(e):
        v = int(e.control.value)
        comment_limit_slider.label = f"Comentarios: {v}"
        try: page.update()
        except: pass

    post_limit_slider.on_change = on_post_limit_change
    comment_limit_slider.on_change = on_comment_limit_change

    # Control para detener la ejecución del scraper
    reddit_stop_event = None

    start_button = ft.ElevatedButton("Ejecutar Scraper", icon=Icons.CLOUD_DOWNLOAD, on_click=None, bgcolor=REDDIT_COLOR, color="white", width=260)
    stop_button = ft.ElevatedButton("Detener", icon=Icons.STOP, on_click=None, bgcolor=ft.Colors.RED_600, color="white", width=260, disabled=True)

    # --- 3. Componente de Progreso (Integrado) ---
    progress_text = ft.Text("Iniciando...", size=12, color="primary", italic=True)
    progress_bar = ft.ProgressBar(width=None, color=REDDIT_COLOR, bgcolor="surfaceVariant") 
    
    progress_container = ft.Container(
        content=ft.Column([
            ft.Row([
                ft.Text("Sincronizando con Reddit...", weight="bold", size=14, color="onSurface"),
                ft.Container(content=ft.ProgressRing(width=16, height=16, stroke_width=2), padding=5)
            ], alignment=ft.MainAxisAlignment.START),
            progress_bar,
            progress_text
        ], spacing=5),
        bgcolor="surfaceContainerHighest",
        padding=15,
        border_radius=10,
        margin=ft.margin.only(bottom=10),
        visible=False, 
        animate_opacity=300, 
    )

    # --- 4. Lógica de Negocio ---
    def refresh_data_objects():
        new_pubs, new_comments = get_reddit_data()
        publications.clear()       
        publications.extend(new_pubs)
        comments_map.clear()
        comments_map.update(new_comments)

    def render_publications():
        publications_column.controls.clear()
        if not publications:
            publications_column.controls.append(
                ft.Container(
                    content=ft.Column([
                        ft.Icon(Icons.SEARCH_OFF, size=60, color="outline"),
                        ft.Text("No hay hilos guardados", color="outline", size=16)
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    alignment=ft.alignment.center,
                    padding=50
                )
            )
        else:
            for post in publications:
                count = len(comments_map.get(post.id, []))
                card = create_post_card(post, count)
                publications_column.controls.append(card)
        page.update()

    def delete_publication_handler(e):
        post_id = e.control.data
        if delete_publication_by_id(post_id):
            refresh_data_objects()
            render_publications()
            show_snackbar(page, "Hilo eliminado")
        else:
            show_snackbar(page, "Error al eliminar", is_error=True)

    # --- Lógica de Tarjeta REDDIT (Solo link pequeño) ---
    def create_post_card(post: Publication, comment_count: int):
        post_url = f"https://www.reddit.com/comments/{post.id}/"
        
        main_text = post.title_translated or post.title_original or "Sin contenido"
        has_translation = bool(post.title_translated and post.title_original and post.title_translated != post.title_original)
        content_text = post.title_translated or post.title_original
        
        # Verificar si tiene texto largo
        has_body = content_text and len(content_text) > 50

        if has_body:
            # Texto Normal
            main_content = ft.Text(
                main_text, 
                size=14, 
                color="onSurface", 
                weight=ft.FontWeight.W_500,
                selectable=True,
                max_lines=6, 
                overflow=ft.TextOverflow.ELLIPSIS
            )
            original_content_block = ft.Container(
                content=ft.Column([
                    ft.Text("Original:", size=10, color="outline", weight="bold"),
                    ft.Text(post.title_original or "", size=11, color="onSurfaceVariant", italic=True, max_lines=3, overflow=ft.TextOverflow.ELLIPSIS),
                ], spacing=2),
                bgcolor="surfaceVariant", 
                padding=8, 
                border_radius=6,
                visible=has_translation,
                margin=ft.margin.only(top=5)
            )
        else:
            # Link/Multimedia
            main_content = ft.Container(
                content=ft.Row([
                    ft.Icon(Icons.LINK, color=REDDIT_COLOR, size=30),
                    ft.Column([
                        ft.Text(main_text, weight="bold", color="onSurface"),
                        ft.Text("Enlace o imagen externa", size=12, color="outline")
                    ], spacing=2)
                ], alignment=ft.MainAxisAlignment.CENTER),
                bgcolor="surfaceVariant", 
                padding=15, border_radius=8,
                border=ft.border.all(1, "outlineVariant"),
                alignment=ft.alignment.center,
                # Este bloque sí puede ser clickeable porque es explícitamente un enlace
                on_click=lambda _: page.launch_url(post_url), 
                ink=True
            )
            original_content_block = ft.Container()

        return ft.Container(
            content=ft.Column([
                # Cabecera
                ft.Row([
                    ft.Container(content=ft.Icon(Icons.REDDIT, color=REDDIT_COLOR, size=20), padding=5, bgcolor="surfaceContainerHighest", border_radius=50),
                    ft.Column([
                        ft.Text("Reddit Thread", size=11, color="outline", weight=ft.FontWeight.BOLD),
                        # OPCIÓN PEQUEÑA PARA IR A LA WEB
                        ft.Container(
                            content=ft.Text("Ver en web", size=10, color=ACCENT_COLOR, weight="bold"),
                            on_click=lambda _: page.launch_url(post_url),
                            padding=ft.padding.symmetric(horizontal=4, vertical=2),
                            border_radius=4,
                            ink=True
                        )
                    ], spacing=0)
                ], spacing=8),
                
                ft.Divider(height=8, color="transparent"),
                
                # Cuerpo (Ya NO tiene on_click global)
                ft.Container(
                    content=main_content,
                    border_radius=8
                ),
                
                ft.Divider(height=5, color="transparent"),
                original_content_block,
                ft.Divider(height=1, color="outlineVariant"),
                
                # Pie de página
                ft.Row([
                    ft.Container(
                        content=ft.Row([
                            ft.Icon(Icons.ARROW_UPWARD, size=14, color="onSurfaceVariant"),
                            ft.Text("Vote", size=11, color="onSurfaceVariant", weight="bold"),
                            ft.Icon(Icons.ARROW_DOWNWARD, size=14, color="onSurfaceVariant"),
                        ], spacing=5),
                        bgcolor="surfaceContainerHighest", padding=ft.padding.symmetric(horizontal=6, vertical=4), border_radius=15
                    ),
                    ft.Container(
                        content=ft.Row([ft.Icon(Icons.CHAT_BUBBLE_OUTLINE, size=14, color="onSurfaceVariant"), ft.Text(f"{comment_count}", size=11, color="onSurfaceVariant", weight="bold")]),
                        on_click=lambda e: page.go(f"/comments/{post.id}"), 
                        padding=ft.padding.symmetric(horizontal=8, vertical=4), 
                        border_radius=5, ink=True
                    ),
                    ft.Container(expand=True),
                    ft.IconButton(Icons.DELETE_OUTLINE, icon_color=Colors.RED_300, icon_size=18, on_click=delete_publication_handler, data=post.id, tooltip="Eliminar")
                ], alignment=ft.MainAxisAlignment.START, spacing=5)
            ], spacing=2),
            
            padding=12, 
            bgcolor="surface", 
            border_radius=8, 
            shadow=SHADOW_CARD,
            # Se eliminó on_click=lambda... de aquí
        )

    # --- 5. Eventos ---
    def show_drawer(e):
        config_drawer.open = True
        config_drawer.update()

    def close_drawer():
        config_drawer.open = False
        config_drawer.update()

    # --- Lógica de Tema ---
    def toggle_theme(e):
        if page.theme_mode == ft.ThemeMode.LIGHT:
            page.theme_mode = ft.ThemeMode.DARK
            theme_icon.icon = Icons.LIGHT_MODE
            show_snackbar(page, "Modo Oscuro")
        else:
            page.theme_mode = ft.ThemeMode.LIGHT
            theme_icon.icon = Icons.DARK_MODE 
            show_snackbar(page, "Modo Claro")
        page.update()

    initial_icon = Icons.DARK_MODE if page.theme_mode == ft.ThemeMode.LIGHT else Icons.LIGHT_MODE
    theme_icon = ft.IconButton(icon=initial_icon, icon_color="onSurface", on_click=toggle_theme, tooltip="Cambiar Tema")

    def run_scraper_click(e):
        target_sub = subreddit_input.value.strip()
        if not target_sub:
            show_snackbar(page, "Escribe un subreddit", is_error=True)
            return

        close_drawer()
        
        # Mostrar progreso
        progress_container.visible = True
        progress_bar.color = REDDIT_COLOR
        progress_text.color = "primary"
        progress_text.value = f"Analizando r/{target_sub}..."
        page.update()
        
        nonlocal reddit_stop_event

        # Preparar y activar el Event de detención
        reddit_stop_event = threading.Event()
        start_button.disabled = True
        stop_button.disabled = False
        try:
            page.update()
        except:
            pass

        def _thread_target():
            status = {"has_error": False, "last_message": ""}
            
            def on_progress_update(msg):
                print(f"[Reddit] {msg}")
                progress_text.value = msg
                if "Error" in msg:
                    status["has_error"] = True
                    progress_bar.color = ft.Colors.RED
                    progress_text.color = ft.Colors.RED
                
                try:
                    page.update()
                except:
                    pass

            try:
                translator = page.data.get("translator") if hasattr(page, 'data') and page.data else None
                sentiment = page.data.get("sentiment") if hasattr(page, 'data') and page.data else None
                run_reddit_scrape_opt(
                    progress_callback=on_progress_update,
                    translator=translator,
                    sentiment_analyzer=sentiment,
                    subreddit_name=target_sub,
                    post_limit=int(post_limit_slider.value),
                    comment_limit=int(comment_limit_slider.value),
                    stop_event=reddit_stop_event
                )
                refresh_data_objects() 
                render_publications()
                
            except Exception as ex:
                print(ex)
                status["has_error"] = True
                status["last_message"] = str(ex)
            
            finally:
                # Restaurar estado de botones y UI usando idle callback
                def restore_ui():
                    nonlocal start_button, stop_button
                    start_button.disabled = False
                    stop_button.disabled = True
                    progress_container.visible = False
                    
                    if status["has_error"]:
                        show_snackbar(page, "Proceso terminado con errores", is_error=True)
                    else:
                        show_snackbar(page, f"Datos de r/{target_sub} actualizados")
                    
                    page.update()
                
                # Esperar un poco si hubo error
                if status["has_error"]:
                    time.sleep(2)
                
                # Ejecutar restauración en el hilo principal de Flet
                try:
                    page.run_task(restore_ui)
                except:
                    # Fallback si run_task no está disponible
                    restore_ui()

        threading.Thread(target=_thread_target, daemon=True).start()

    def clear_all_click(e):
        count = delete_publications_by_network("Reddit")
        refresh_data_objects()
        render_publications()
        close_drawer()
        show_snackbar(page, f"Vaciado ({count} eliminados)")

    # --- 6. Definición del Drawer ---
    # Acción para detener desde UI
    def stop_scraper_click(e):
        nonlocal reddit_stop_event
        if reddit_stop_event is not None:
            reddit_stop_event.set()
            progress_text.value = "Detención solicitada..." 
            try: page.update()
            except: pass

    # Asignar handlers a botones
    start_button.on_click = run_scraper_click
    stop_button.on_click = stop_scraper_click
    config_drawer = ft.NavigationDrawer(
        position=ft.NavigationDrawerPosition.END,
        controls=[
            ft.Container(
                padding=20,
                content=ft.Column([
                    ft.Row([ft.Icon(Icons.SETTINGS, color=PRIMARY), ft.Text("Configuración", size=20, weight="bold")]),
                    ft.Divider(),
                    ft.Text("Subreddit Objetivo", weight="bold", size=12, color="onSurfaceVariant"),
                    subreddit_input,
                    ft.Divider(height=10),
                    ft.Text("Límites del Scraper", weight="bold", size=12, color="onSurfaceVariant"),
                    post_limit_slider,
                    comment_limit_slider,
                    ft.Divider(height=20),
                    start_button,
                    stop_button,
                    ft.ElevatedButton("Generar PDF", icon=Icons.PICTURE_AS_PDF, on_click=lambda _: generate_pdf_report(page, publications, comments_map), bgcolor=ft.Colors.ORANGE_700, color="white", width=260),
                    ft.Divider(),
                    ft.OutlinedButton("Borrar Todo", icon=Icons.DELETE_FOREVER, on_click=clear_all_click, style=ft.ButtonStyle(color=ERROR), width=260)
                ], spacing=15, scroll=ft.ScrollMode.AUTO)
            )
        ],
        bgcolor="surface",
    )

    render_publications()

    # --- 7. Layout Principal ---
    return ft.View(
        "/dashboard/reddit",
        end_drawer=config_drawer, 
        controls=[
            ft.AppBar(
                title=ft.Text("Dashboard Reddit", weight=ft.FontWeight.BOLD, color="white"),
                bgcolor=REDDIT_COLOR,
                elevation=0,
                leading=ft.IconButton(Icons.ARROW_BACK, icon_color="white", on_click=lambda _: page.go("/social_select")),
                actions=[
                    theme_icon,
                    ft.IconButton(
                        icon=Icons.SETTINGS, 
                        icon_color="white", 
                        tooltip="Configuración",
                        on_click=show_drawer 
                    ),
                    ft.Container(width=10)
                ]
            ),
            
            ft.Container(
                expand=True,
                bgcolor="background",
                padding=ft.padding.symmetric(horizontal=10, vertical=10),
                content=ft.Row(
                    controls=[
                        ft.Container(
                            content=ft.Column(
                                controls=[
                                    ft.Text("Hilos Populares", size=24, weight=ft.FontWeight.BOLD, color="onSurface"),
                                    progress_container,
                                    ft.Container(content=publications_column, expand=True)
                                ],
                                spacing=10,
                                expand=True
                            ),
                            width=800,
                            expand=True
                        )
                    ],
                    alignment=ft.MainAxisAlignment.CENTER, 
                    vertical_alignment=ft.CrossAxisAlignment.START, 
                    expand=True
                )
            )
        ],
        padding=0,
        bgcolor="background"
    )