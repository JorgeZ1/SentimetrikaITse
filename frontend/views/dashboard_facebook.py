import flet as ft
from flet import Colors, Icons
from typing import List, Dict, Tuple
import os
import threading
import time # Necesario para la pausa en caso de error
from pathlib import Path

# --- Imports de tu proyecto ---
from backend.database import SessionLocal, Publication, Comment, delete_publication_by_id, delete_publications_by_network
from backend.facebook_scraper import run_facebook_scrape_opt
from frontend.theme import *
from frontend.utils import show_snackbar
from backend.report_generator import PDFReportGenerator

# --- BLOQUE DE SEGURIDAD DE COLORES ---
try:
    FACEBOOK_COLOR  
except NameError:
    FACEBOOK_COLOR = "#1877F2"

try:
    ACCENT_COLOR 
except NameError:
    try:
        ACCENT_COLOR = ACCENT 
    except NameError:
        ACCENT_COLOR = "#1877F2" 
        ACCENT = "#1877F2"

try:
    PRIMARY
except NameError:
    PRIMARY = ft.Colors.BLUE

try:
    ERROR
except NameError:
    ERROR = ft.Colors.RED

# --- Constantes de Estilo Visual ---
FB_BG_COLOR = "background" 
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
        file_path = generator.generate_report("Facebook", publications, comments_map)
        show_snackbar(page, f"Reporte guardado: {os.path.basename(file_path)}")
        try:
            os.startfile(os.path.dirname(file_path))
        except:
            pass 
    except Exception as e:
        print(f"Error PDF: {e}")
        show_snackbar(page, f"Error generando reporte: {str(e)}", is_error=True)

def get_facebook_data() -> Tuple[List[Publication], Dict[str, List[Comment]]]:
    session = SessionLocal()
    pubs: List[Publication] = []
    c_map: Dict[str, List[Comment]] = {} 
    try:
        pubs_db = session.query(Publication).filter(Publication.red_social == 'Facebook').all()
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
    initial_pubs, initial_comments = get_facebook_data()
    publications = list(initial_pubs)     
    comments_map = dict(initial_comments) 

    # --- 2. Componentes UI ---
    publications_column = ft.Column(spacing=15, scroll=ft.ScrollMode.HIDDEN)
    
    # Inputs
    token_input = ft.TextField(label="PAGE_ACCESS_TOKEN", password=True, can_reveal_password=True, text_size=12, bgcolor="surfaceVariant", border_radius=8)
    page_id_input = ft.TextField(label="PAGE_ID", text_size=12, bgcolor="surfaceVariant", border_radius=8)

    # --- 3. Componente de Progreso Integrado (INTELIGENTE) ---
    progress_text = ft.Text("Iniciando...", size=12, color="primary", italic=True)
    progress_bar = ft.ProgressBar(width=None, color=FACEBOOK_COLOR, bgcolor="surfaceVariant") 
    
    progress_container = ft.Container(
        content=ft.Column([
            ft.Row([
                ft.Text("Sincronizando con Facebook...", weight="bold", size=14, color="onSurface"),
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
        new_pubs, new_comments = get_facebook_data()
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
                        ft.Text("No hay publicaciones guardadas", color="outline", size=16)
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
            show_snackbar(page, "Publicación eliminada")
        else:
            show_snackbar(page, "Error al eliminar", is_error=True)

    # --- Lógica de Tarjeta ---
    def create_post_card(post: Publication, comment_count: int):
        has_text = bool(post.title_translated or post.title_original)
        post_url = f"https://www.facebook.com/{post.id}"

        if has_text:
            main_content = ft.Text(
                post.title_translated or post.title_original, 
                size=15, color="onSurface", weight=ft.FontWeight.W_500, selectable=True
            )
            original_content_block = ft.Container(
                content=ft.Column([
                    ft.Text("Original:", size=10, color="outline", weight="bold"),
                    ft.Text(post.title_original or "", size=12, color="onSurfaceVariant", italic=True),
                ]),
                bgcolor="surfaceVariant", padding=10, border_radius=8,
                visible=bool(post.title_original and post.title_original != post.title_translated)
            )
        else:
            main_content = ft.Container(
                content=ft.Row([
                    ft.Icon(Icons.IMAGE, color=FACEBOOK_COLOR, size=30),
                    ft.Column([
                        ft.Text("Contenido Multimedia", weight="bold", color="onSurface"),
                        ft.Text("Clic para ver en Facebook", size=12, color="outline")
                    ], spacing=2)
                ], alignment=ft.MainAxisAlignment.CENTER),
                bgcolor="surfaceVariant", padding=20, border_radius=8,
                border=ft.border.all(1, color="outlineVariant"),
                alignment=ft.alignment.center
            )
            original_content_block = ft.Container()

        return ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Container(content=ft.Icon(Icons.FACEBOOK, color=FACEBOOK_COLOR, size=24), padding=5, bgcolor="#E7F3FF", border_radius=50),
                    ft.Column([
                        ft.Text("Facebook Post", size=12, color="onSurfaceVariant", weight=ft.FontWeight.BOLD),
                        ft.Text("Ver original", size=10, color=ACCENT_COLOR, weight="bold") 
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
                ft.Divider(height=1, color="outlineVariant"),
                
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

    # --- 5. Eventos de Drawer ---
    def show_drawer(e):
        config_drawer.open = True
        config_drawer.update()

    def close_drawer():
        config_drawer.open = False
        config_drawer.update()

    # --- Guardado Limpio ---
    def update_credentials_click(e):
        new_token = token_input.value.strip()
        new_page_id = page_id_input.value.strip()
        
        if not new_token and not new_page_id:
            show_snackbar(page, "Ingresa datos para guardar", is_error=True)
            return

        env_path = Path('.env')
        if not env_path.exists(): env_path.touch()
        
        try:
            lines = env_path.read_text().splitlines()
            clean_lines = [
                line for line in lines 
                if not line.startswith("PAGE_ACCESS_TOKEN=") and not line.startswith("PAGE_ID=")
            ]
            
            if new_token:
                clean_lines.append(f"PAGE_ACCESS_TOKEN={new_token}")
                os.environ['PAGE_ACCESS_TOKEN'] = new_token
            if new_page_id:
                clean_lines.append(f"PAGE_ID={new_page_id}")
                os.environ['PAGE_ID'] = new_page_id
            
            env_path.write_text("\n".join(clean_lines))
            
            show_snackbar(page, "Credenciales guardadas y archivo limpiado.")
            token_input.value = ""
            page_id_input.value = ""
            page.update()
            
        except Exception as ex:
            show_snackbar(page, f"Error al guardar: {ex}", is_error=True)

    # --- Ejecución del Scraper INTELIGENTE ---
    def run_scraper_click(e):
        close_drawer()
        
        current_id = os.environ.get('PAGE_ID')
        current_token = os.environ.get('PAGE_ACCESS_TOKEN')
        
        if not current_id or not current_token:
             show_snackbar(page, "Faltan credenciales. Configura y guarda primero.", is_error=True)
             return

        # Reiniciar estado visual de la barra
        progress_container.visible = True
        progress_bar.color = FACEBOOK_COLOR # Color normal (Azul)
        progress_text.color = "primary"
        progress_text.value = "Inicializando..."
        page.update()
        
        def _thread_target():
            # Estado mutable para comunicar errores
            status = {"has_error": False, "last_message": ""}

            def on_progress_update(msg):
                print(f"[Scraper] {msg}") 
                
                # Actualizar texto
                progress_text.value = msg
                status["last_message"] = msg
                
                # DETECCIÓN VISUAL DE ERRORES
                # Si el mensaje contiene "Error" o el icono de cruz, cambiar a ROJO
                if "Error" in msg:
                    status["has_error"] = True
                    progress_bar.color = ft.Colors.RED
                    progress_text.color = ft.Colors.RED
                else:
                    # Si vuelve a la normalidad (ej: "Reintentando..."), restaurar color
                    if not status["has_error"]:
                        progress_bar.color = FACEBOOK_COLOR
                        progress_text.color = "primary"

                try:
                    page.update()
                except:
                    pass 

            try:
                translator = page.data.get("translator") if hasattr(page, 'data') and page.data else None
                sentiment = page.data.get("sentiment") if hasattr(page, 'data') and page.data else None
                
                run_facebook_scrape_opt(
                    progress_callback=on_progress_update,
                    translator=translator,
                    sentiment_analyzer=sentiment,
                    page_id=current_id,
                    token=current_token
                )
                
                refresh_data_objects() 
                render_publications()
                
            except Exception as ex:
                print(ex)
                status["has_error"] = True
                status["last_message"] = str(ex)
            
            finally:
                # SI HUBO ERROR: Pausar 4 segundos para que el usuario lea
                if status["has_error"]:
                    time.sleep(4)
                
                progress_container.visible = False
                try:
                    page.update()
                except:
                    pass
                
                if status["has_error"]:
                    show_snackbar(page, "El proceso terminó con errores. Revisa las credenciales.", is_error=True)
                else:
                    show_snackbar(page, "Datos actualizados exitosamente")
                
        threading.Thread(target=_thread_target, daemon=True).start()

    def clear_all_click(e):
        count = delete_publications_by_network("Facebook")
        refresh_data_objects()
        render_publications()
        close_drawer()
        show_snackbar(page, f"Vaciado ({count})")

    # --- 6. Definición del Drawer ---
    config_drawer = ft.NavigationDrawer(
        position=ft.NavigationDrawerPosition.END,
        controls=[
            ft.Container(
                padding=20,
                content=ft.Column([
                    ft.Row([ft.Icon(Icons.SETTINGS, color=PRIMARY), ft.Text("Configuración", size=20, weight="bold")]),
                    ft.Divider(),
                    ft.Text("Credenciales API", weight="bold", size=12, color=TEXT_SUB),
                    token_input,
                    page_id_input,
                    ft.ElevatedButton("Guardar Limpio", icon=Icons.SAVE, on_click=update_credentials_click, bgcolor=ACCENT_COLOR, color="white", width=260),
                    ft.Divider(height=20),
                    ft.Text("Herramientas", weight="bold", size=12, color=TEXT_SUB),
                    ft.ElevatedButton("Ejecutar Scraper", icon=Icons.CLOUD_DOWNLOAD, on_click=run_scraper_click, bgcolor=FACEBOOK_COLOR, color="white", width=260),
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
        "/dashboard/facebook",
        end_drawer=config_drawer, 
        controls=[
            ft.AppBar(
                title=ft.Text("Dashboard Facebook", weight=ft.FontWeight.BOLD, color="white"),
                bgcolor=FACEBOOK_COLOR,
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
                bgcolor="background", 
                padding=ft.padding.symmetric(horizontal=10, vertical=10),
                content=ft.Row(
                    controls=[
                        ft.Container(
                            content=ft.Column(
                                controls=[
                                    ft.Text("Feed de Publicaciones", size=24, weight=ft.FontWeight.BOLD, color=TEXT_MAIN),
                                    # AQUÍ INSERTAMOS LA BARRA DE PROGRESO DINÁMICA
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