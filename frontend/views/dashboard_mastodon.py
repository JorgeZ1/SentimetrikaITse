import flet as ft
from flet import Colors, Icons
from typing import List, Dict, Tuple
import os
import threading
import time
from pathlib import Path

# --- Imports de tu proyecto ---
from backend.database import SessionLocal, Publication, Comment, delete_publication_by_id, delete_publications_by_network
from backend.mastodon_scraper import run_mastodon_scrape_opt
from frontend.theme import *
from frontend.utils import show_snackbar
from backend.report_generator import PDFReportGenerator

# --- BLOQUE DE SEGURIDAD DE COLORES ---
try:
    MASTODON_COLOR  
except NameError:
    MASTODON_COLOR = "#6364FF" 

try:
    ACCENT_COLOR 
except NameError:
    try:
        ACCENT_COLOR = ACCENT 
    except NameError:
        ACCENT_COLOR = "#6364FF"
        ACCENT = "#6364FF"

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
    blur_radius=5,
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
        file_path = generator.generate_report("Mastodon", publications, comments_map)
        show_snackbar(page, f"Reporte guardado: {os.path.basename(file_path)}")
        try:
            os.startfile(os.path.dirname(file_path))
        except:
            pass 
    except Exception as e:
        print(f"Error PDF: {e}")
        show_snackbar(page, f"Error generando reporte: {str(e)}", is_error=True)

def get_mastodon_data() -> Tuple[List[Publication], Dict[str, List[Comment]]]:
    session = SessionLocal()
    pubs: List[Publication] = []
    c_map: Dict[str, List[Comment]] = {} 
    try:
        pubs_db = session.query(Publication).filter(Publication.red_social == 'Mastodon').all()
        
        # CORRECCIÓN: Invertimos la lista para que las nuevas (últimas insertadas) salgan primero
        pubs_db.reverse()
        
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
    initial_pubs, initial_comments = get_mastodon_data()
    publications = list(initial_pubs)     
    comments_map = dict(initial_comments) 

    # --- 2. Componentes UI ---
    publications_column = ft.Column(spacing=15, scroll=ft.ScrollMode.HIDDEN)
    
    # Input para IDs (Memoria)
    mastodon_ids_input = ft.TextField(
        label="IDs de Publicaciones a Analizar",
        multiline=True,
        min_lines=3,
        max_lines=10,
        hint_text="Pega aquí los IDs (uno por línea o separados por comas)\nEj: 115465371158102856",
        text_size=12,
        bgcolor="surfaceVariant",
        border_radius=8
    )

    # --- 3. Componente de Progreso Integrado ---
    progress_text = ft.Text("Iniciando...", size=12, color="primary", italic=True)
    progress_bar = ft.ProgressBar(width=None, color=MASTODON_COLOR, bgcolor="surfaceVariant") 
    
    progress_container = ft.Container(
        content=ft.Column([
            ft.Row([
                ft.Text("Sincronizando con Mastodon...", weight="bold", size=14, color="onSurface"),
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
        new_pubs, new_comments = get_mastodon_data()
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
                        ft.Text("No hay toots guardados", color="outline", size=16)
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
            show_snackbar(page, "Toot eliminado")
        else:
            show_snackbar(page, "Error al eliminar", is_error=True)

    # --- Lógica de Tarjeta (Estilo Mastodon) ---
    def create_post_card(post: Publication, comment_count: int):
        # Detectar contenido
        content_text = post.title_translated or post.title_original
        has_text = bool(content_text)
        has_translation = bool(post.title_translated and post.title_original and post.title_translated != post.title_original)
        
        post_url = f"https://mastodon.social/web/@user/{post.id}" 

        if has_text:
            main_content = ft.Text(
                content_text, 
                size=15, color="onSurface", weight=ft.FontWeight.W_500, selectable=True
            )
            original_content_block = ft.Container(
                content=ft.Column([
                    ft.Text("Original:", size=10, color="outline", weight="bold"),
                    ft.Text(post.title_original or "", size=12, color="onSurfaceVariant", italic=True),
                ]),
                bgcolor="surfaceVariant", padding=10, border_radius=8,
                visible=has_translation
            )
        else:
            # Multimedia
            main_content = ft.Container(
                content=ft.Row([
                    ft.Icon(Icons.IMAGE, color=MASTODON_COLOR, size=30),
                    ft.Column([
                        ft.Text("Contenido Multimedia", weight="bold", color="onSurface"),
                        ft.Text("Imagen o video sin descripción.", size=12, color="outline")
                    ], spacing=2)
                ], alignment=ft.MainAxisAlignment.CENTER),
                bgcolor="surfaceVariant", padding=20, border_radius=8,
                border=ft.border.all(1, color="outlineVariant"),
                alignment=ft.alignment.center,
                on_click=lambda _: page.launch_url(post_url),
                ink=True
            )
            original_content_block = ft.Container()

        return ft.Container(
            content=ft.Column([
                # Cabecera
                ft.Row([
                    ft.Container(content=ft.Icon(Icons.ROCKET_LAUNCH, color=MASTODON_COLOR, size=24), padding=5, bgcolor="#E5E6FF", border_radius=50),
                    ft.Column([
                        ft.Text("Mastodon Toot", size=12, color="onSurfaceVariant", weight=ft.FontWeight.BOLD),
                        ft.Container(
                            content=ft.Text("Ver en instancia", size=10, color=ACCENT_COLOR, weight="bold"),
                            on_click=lambda _: page.launch_url(post_url),
                            padding=2,
                            border_radius=4,
                            ink=True
                        )
                    ], spacing=0)
                ], spacing=10),
                
                ft.Divider(height=10, color="transparent"),
                
                # Cuerpo
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
                        content=ft.Row([ft.Icon(Icons.CHAT_BUBBLE_OUTLINE, size=16, color="outline"), ft.Text(f"{comment_count}", color="outline", weight="bold")]),
                        on_click=lambda e: page.go(f"/comments/{post.id}"), padding=8, border_radius=5, ink=True
                    ),
                    ft.IconButton(Icons.DELETE_OUTLINE, icon_color=Colors.RED_300, icon_size=20, on_click=delete_publication_handler, data=post.id, tooltip="Eliminar")
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
            ]),
            padding=15, bgcolor="surface", border_radius=10, shadow=SHADOW_CARD
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

    # --- Ejecutar Scraper ---
    def run_scraper_click(e):
        close_drawer()
        
        # 1. Obtener IDs del campo de texto (Memoria)
        raw_text = mastodon_ids_input.value.strip()
        if not raw_text:
            show_snackbar(page, "Pega al menos un ID en la configuración.", is_error=True)
            show_drawer(None) # Abrir drawer para que vea dónde
            return

        # Parsear IDs
        target_ids_list = [
            id.strip() 
            for id in raw_text.replace(',', '\n').split('\n') 
            if id.strip().isdigit()
        ]

        if not target_ids_list:
            show_snackbar(page, "No se encontraron IDs numéricos válidos.", is_error=True)
            return

        # Mostrar Progreso
        progress_container.visible = True
        progress_bar.color = MASTODON_COLOR
        progress_text.color = "primary"
        progress_text.value = f"Analizando {len(target_ids_list)} IDs..."
        page.update()
        
        def _thread_target():
            status = {"has_error": False, "last_message": ""}
            
            def on_progress_update(msg):
                print(f"[Mastodon] {msg}")
                progress_text.value = msg
                if "Error" in msg:
                    status["has_error"] = True
                    progress_bar.color = ft.Colors.RED
                    progress_text.color = ft.Colors.RED
                try:
                    page.update()
                except: pass

            try:
                translator = page.data.get("translator") if hasattr(page, 'data') and page.data else None
                sentiment = page.data.get("sentiment") if hasattr(page, 'data') and page.data else None
                
                # PASO CLAVE: Enviar lista directa
                run_mastodon_scrape_opt(
                    progress_callback=on_progress_update,
                    translator=translator,
                    sentiment=sentiment, # Cambio: sentiment_analyzer -> sentiment
                    target_ids_list=target_ids_list 
                )
                refresh_data_objects() 
                render_publications()
                
            except Exception as ex:
                print(ex)
                status["has_error"] = True
                status["last_message"] = str(ex)
            
            finally:
                if status["has_error"]:
                    time.sleep(4)
                
                progress_container.visible = False
                try:
                    page.update()
                except:
                    pass
                
                if status["has_error"]:
                    show_snackbar(page, "Proceso terminado con errores", is_error=True)
                else:
                    show_snackbar(page, "Datos actualizados")

        threading.Thread(target=_thread_target, daemon=True).start()

    def clear_all_click(e):
        count = delete_publications_by_network("Mastodon")
        refresh_data_objects()
        render_publications()
        close_drawer()
        show_snackbar(page, f"Vaciado ({count} eliminados)")

    # --- 6. Definición del Drawer ---
    config_drawer = ft.NavigationDrawer(
        position=ft.NavigationDrawerPosition.END,
        controls=[
            ft.Container(
                padding=20,
                content=ft.Column([
                    ft.Row([ft.Icon(Icons.SETTINGS, color=PRIMARY), ft.Text("Configuración", size=20, weight="bold")]),
                    ft.Divider(),
                    
                    ft.Text("IDs de Publicaciones", weight="bold", size=12, color="onSurfaceVariant"),
                    mastodon_ids_input,
                    ft.Text("Ingresa los IDs numéricos aquí (memoria).", size=10, italic=True, color="outline"),
                    
                    ft.Divider(height=20),
                    ft.Text("Herramientas", weight="bold", size=12, color="onSurfaceVariant"),
                    ft.ElevatedButton("Ejecutar Scraper", icon=Icons.CLOUD_DOWNLOAD, on_click=run_scraper_click, bgcolor=MASTODON_COLOR, color="white", width=260),
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
        "/dashboard/mastodon",
        end_drawer=config_drawer, 
        controls=[
            ft.AppBar(
                title=ft.Text("Dashboard Mastodon", weight=ft.FontWeight.BOLD, color="white"),
                bgcolor=MASTODON_COLOR,
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
                                    ft.Text("Feed de Toots", size=24, weight=ft.FontWeight.BOLD, color=TEXT_MAIN),
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