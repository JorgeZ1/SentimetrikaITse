import flet as ft
from flet import Colors, Icons
from typing import List, Dict, Tuple
import os
import threading
from pathlib import Path

# --- Imports de tu proyecto ---
from backend.database import SessionLocal, Publication, Comment, delete_publication_by_id, delete_publications_by_network
from backend.mastodon_scraper import run_mastodon_scrape_opt
from frontend.theme import *
from frontend.utils import show_snackbar
from backend.report_generator import PDFReportGenerator

# --- BLOQUE DE SEGURIDAD DE COLORES ---
try:
    MASTODON_COLOR  # Intentamos acceder a la variable importada
except NameError:
    MASTODON_COLOR = "#6364FF" # Color oficial Mastodon

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
BG_COLOR = "#F0F2F5"
CARD_BG = "#FFFFFF"
TEXT_MAIN = "#050505"
TEXT_SUB = "#65676B"
SHADOW_CARD = ft.BoxShadow(
    spread_radius=1,
    blur_radius=5,
    color=ft.Colors.with_opacity(0.1, ft.Colors.BLACK),
    offset=ft.Offset(0, 2),
)

def generate_pdf_report(page: ft.Page, publications: List[Publication], comments_map: Dict[str, List[Comment]]):
    if not publications:
        show_snackbar(page, "⚠️ No hay publicaciones para generar el reporte.", is_error=True)
        return
    try:
        show_snackbar(page, "📄 Generando PDF...", is_error=False)
        generator = PDFReportGenerator()
        file_path = generator.generate_report("Mastodon", publications, comments_map)
        show_snackbar(page, f"✅ Reporte guardado: {os.path.basename(file_path)}")
        try:
            os.startfile(os.path.dirname(file_path))
        except:
            pass 
    except Exception as e:
        print(f"Error PDF: {e}")
        show_snackbar(page, f"❌ Error generando reporte: {str(e)}", is_error=True)

def get_mastodon_data() -> Tuple[List[Publication], Dict[str, List[Comment]]]:
    session = SessionLocal()
    pubs: List[Publication] = []
    c_map: Dict[str, List[Comment]] = {} 
    try:
        pubs_db = session.query(Publication).filter(Publication.red_social == 'Mastodon').all()
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
    
    # Input para IDs de Mastodon
    mastodon_ids_input = ft.TextField(
        label="IDs de Publicaciones",
        multiline=True,
        min_lines=3,
        max_lines=5,
        hint_text="Ej: 115465371158102856\n115466810391857392",
        text_size=12,
        bgcolor="white",
        border_radius=8
    )

    # --- 3. Lógica de Negocio ---
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
                        ft.Icon(Icons.SEARCH_OFF, size=60, color=Colors.GREY_300),
                        ft.Text("No hay toots guardados", color=Colors.GREY_500, size=16)
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
            show_snackbar(page, "✅ Toot eliminado")
        else:
            show_snackbar(page, "❌ Error al eliminar", is_error=True)

    # --- Lógica de Tarjeta (Estilo Mastodon) ---
    def create_post_card(post: Publication, comment_count: int):
        has_text = bool(post.title_translated or post.title_original)
        # URL aproximada (Mastodon es federado, así que esto es un best-guess o placeholder)
        post_url = f"https://mastodon.social/web/@user/{post.id}" 

        if has_text:
            main_content = ft.Text(
                post.title_translated or post.title_original, 
                size=15, color=TEXT_MAIN, weight=ft.FontWeight.W_500, selectable=True
            )
            original_content_block = ft.Container(
                content=ft.Column([
                    ft.Text("Original:", size=10, color=TEXT_SUB, weight="bold"),
                    ft.Text(post.title_original or "", size=12, color=TEXT_SUB, italic=True),
                ]),
                bgcolor="#F0F2F5", padding=10, border_radius=8,
                visible=bool(post.title_original and post.title_original != post.title_translated)
            )
        else:
            main_content = ft.Container(
                content=ft.Row([
                    ft.Icon(Icons.IMAGE, color=MASTODON_COLOR, size=30),
                    ft.Column([
                        ft.Text("Contenido Multimedia", weight="bold", color=TEXT_MAIN),
                        ft.Text("Imagen o video sin descripción.", size=12, color=TEXT_SUB)
                    ], spacing=2)
                ], alignment=ft.MainAxisAlignment.CENTER),
                bgcolor="#F0F2F5", padding=20, border_radius=8,
                border=ft.border.all(1, color="#E4E6EB"),
                alignment=ft.alignment.center
            )
            original_content_block = ft.Container()

        return ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Container(content=ft.Icon(Icons.ROCKET_LAUNCH, color=MASTODON_COLOR, size=24), padding=5, bgcolor="#E5E6FF", border_radius=50),
                    ft.Column([
                        ft.Text("Mastodon Toot", size=12, color=TEXT_SUB, weight=ft.FontWeight.BOLD),
                        ft.Text("Ver en instancia ↗", size=10, color=ACCENT_COLOR, weight="bold")
                    ], spacing=2)
                ], spacing=10),
                
                ft.Divider(height=10, color="transparent"),
                
                ft.Container(
                    content=main_content,
                    on_click=lambda _: page.launch_url(post_url),
                    ink=True,
                    border_radius=8
                ),
                
                ft.Divider(height=5, color="transparent"),
                original_content_block,
                ft.Divider(height=1, color="#E4E6EB"),
                
                ft.Row([
                    ft.Container(
                        content=ft.Row([ft.Icon(Icons.CHAT_BUBBLE_OUTLINE, size=16, color=TEXT_SUB), ft.Text(f"{comment_count}", color=TEXT_SUB, weight="bold")]),
                        on_click=lambda e: page.go(f"/comments/{post.id}"), padding=8, border_radius=5, ink=True
                    ),
                    ft.IconButton(Icons.DELETE_OUTLINE, icon_color=Colors.RED_300, icon_size=20, on_click=delete_publication_handler, data=post.id, tooltip="Eliminar")
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
            ]),
            padding=15, bgcolor=CARD_BG, border_radius=10, shadow=SHADOW_CARD
        )

    # --- 4. Eventos de Configuración (Drawer) ---
    
    def show_drawer(e):
        config_drawer.open = True
        config_drawer.update()

    def close_drawer():
        config_drawer.open = False
        config_drawer.update()

    def add_mastodon_ids_click(e):
        new_ids_text = mastodon_ids_input.value.strip()
        if not new_ids_text:
            show_snackbar(page, "⚠️ Ingresa al menos un ID", is_error=True)
            return
        
        # Parsear y Validar
        ids_list = [id.strip() for id in new_ids_text.replace(',', '\n').split('\n') if id.strip()]
        invalid_ids = [id for id in ids_list if not id.isdigit()]
        
        if invalid_ids:
            show_snackbar(page, f"❌ IDs inválidos (solo números): {', '.join(invalid_ids[:2])}...", is_error=True)
            return
        
        # Guardar en archivo
        ids_file = Path('backend/mastodon_ids.txt')
        existing_ids = set()
        if ids_file.exists():
            existing_ids = set(ids_file.read_text().strip().split('\n'))
        
        new_unique_ids = [id for id in ids_list if id not in existing_ids]
        
        if not new_unique_ids:
            show_snackbar(page, "ℹ️ Los IDs ya estaban guardados")
            return
            
        try:
            with open(ids_file, 'a') as f:
                for id in new_unique_ids:
                    f.write(f"{id}\n")
            
            show_snackbar(page, f"✅ {len(new_unique_ids)} IDs agregados")
            mastodon_ids_input.value = ""
            page.update()
        except Exception as ex:
            show_snackbar(page, f"Error guardando: {ex}", is_error=True)

    def run_scraper_click(e):
        close_drawer()
        show_snackbar(page, "🔄 Iniciando Scraper de Mastodon...")
        
        def _thread_target():
            try:
                translator = page.data.get("translator") if hasattr(page, 'data') and page.data else None
                sentiment = page.data.get("sentiment") if hasattr(page, 'data') and page.data else None
                
                run_mastodon_scrape_opt(
                    progress_callback=lambda msg: print(f"[Mastodon] {msg}"),
                    translator=translator,
                    sentiment_analyzer=sentiment
                )
                refresh_data_objects() 
                render_publications()
                show_snackbar(page, "✅ Datos actualizados")
            except Exception as ex:
                print(ex)
                show_snackbar(page, "❌ Error en scraper", is_error=True)
        threading.Thread(target=_thread_target, daemon=True).start()

    def clear_all_click(e):
        count = delete_publications_by_network("Mastodon")
        refresh_data_objects()
        render_publications()
        close_drawer()
        show_snackbar(page, f"✅ Vaciado ({count} eliminados)")

    # --- 5. Definición del Drawer (Menú Lateral) ---
    config_drawer = ft.NavigationDrawer(
        position=ft.NavigationDrawerPosition.END,
        controls=[
            ft.Container(
                padding=20,
                content=ft.Column([
                    ft.Row([ft.Icon(Icons.SETTINGS, color=PRIMARY), ft.Text("Configuración", size=20, weight="bold")]),
                    ft.Divider(),
                    
                    ft.Text("Agregar IDs de Toots", weight="bold", size=12, color=TEXT_SUB),
                    mastodon_ids_input,
                    ft.ElevatedButton("Agregar a la Lista", icon=Icons.ADD, on_click=add_mastodon_ids_click, bgcolor=ACCENT_COLOR, color="white", width=260),
                    
                    ft.Divider(height=20),
                    ft.Text("Herramientas", weight="bold", size=12, color=TEXT_SUB),
                    
                    ft.ElevatedButton("Ejecutar Scraper", icon=Icons.CLOUD_DOWNLOAD, on_click=run_scraper_click, bgcolor=MASTODON_COLOR, color="white", width=260),
                    ft.ElevatedButton("Generar PDF", icon=Icons.PICTURE_AS_PDF, on_click=lambda _: generate_pdf_report(page, publications, comments_map), bgcolor=ft.Colors.ORANGE_700, color="white", width=260),
                    
                    ft.Divider(),
                    ft.OutlinedButton("Borrar Todo", icon=Icons.DELETE_FOREVER, on_click=clear_all_click, style=ft.ButtonStyle(color=ERROR), width=260)
                ], spacing=15, scroll=ft.ScrollMode.AUTO)
            )
        ],
        bgcolor="white",
    )

    render_publications()

    # --- 6. Layout Principal ---
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
                bgcolor=BG_COLOR,
                padding=ft.padding.symmetric(horizontal=10, vertical=10),
                content=ft.Row(
                    controls=[
                        ft.Container(
                            content=ft.Column(
                                controls=[
                                    ft.Text("Feed de Toots", size=24, weight=ft.FontWeight.BOLD, color=TEXT_MAIN),
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
        bgcolor=BG_COLOR
    )