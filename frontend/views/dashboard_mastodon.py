import flet as ft
from flet import Colors, Icons
from backend.database import SessionLocal, Publication, Comment, delete_publication_by_id, delete_publications_by_network
from backend.mastodon_scraper import run_mastodon_scrape_opt
from frontend.theme import *
from frontend.utils import show_snackbar
from typing import List, Dict
from pathlib import Path
from backend.report_generator import PDFReportGenerator
import os
import threading

def generate_pdf_report(page: ft.Page, publications: List[Publication], comments_map: Dict[str, List[Comment]]):
    """Genera el reporte PDF y notifica al usuario"""
    try:
        generator = PDFReportGenerator()
        file_path = generator.generate_report("Mastodon", publications, comments_map)
        
        show_snackbar(page, f"✅ Reporte generado: {os.path.basename(file_path)}")
        # os.startfile(os.path.dirname(file_path))
    except Exception as e:
        show_snackbar(page, f"❌ Error generando reporte: {str(e)}", is_error=True)

def get_mastodon_data() -> (List[Publication], Dict[str, List[Comment]]):
    """Consulta PostgreSQL y estructura los datos para la vista"""
    session = SessionLocal()
    publications: List[Publication] = []
    comments_map: Dict[str, List[Comment]] = {} 
    
    try:
        pubs_db = session.query(Publication).filter(Publication.red_social == 'Mastodon').all()
        
        for p in pubs_db:
            publications.append(p)
            comments_map[p.id] = [c for c in p.comments]
            
    except Exception as e:
        print(f"Error leyendo DB: {e}")
    finally:
        session.close()
        
    return publications, comments_map

def get_sentiment_icon(sentiment: str) -> ft.Icon:
    if sentiment == 'positive':
        return ft.Icon(Icons.SENTIMENT_VERY_SATISFIED, color=SENTIMENT_POSITIVE)
    elif sentiment == 'negative':
        return ft.Icon(Icons.SENTIMENT_VERY_DISSATISFIED, color=SENTIMENT_NEGATIVE)
    else: 
        return ft.Icon(Icons.SENTIMENT_NEUTRAL, color=SENTIMENT_NEUTRAL)

def create_dashboard_view(page: ft.Page) -> ft.View:
    
    # --- Controles UI ---
    publications_list_view = ft.ListView(expand=True, spacing=10, padding=20)
    
    # --- Control de Configuración: IDs de Mastodon ---
    mastodon_ids_input = ft.TextField(
        label="IDs de publicaciones (separados por comas o saltos de línea)",
        multiline=True,
        min_lines=2,
        max_lines=4,
        hint_text="Ej: 115465371158102856, 115466810391857392",
        width=400,
        border_color=PRIMARY
    )
    
    def add_mastodon_ids(e):
        new_ids_text = mastodon_ids_input.value.strip()
        
        if not new_ids_text:
            show_snackbar(page, "⚠️ Ingresa al menos un ID", is_error=True)
            return
        
        # Parsear IDs (separados por comas o saltos de línea)
        ids_list = [id.strip() for id in new_ids_text.replace(',', '\n').split('\n') if id.strip()]
        
        # Validar que sean numéricos
        invalid_ids = [id for id in ids_list if not id.isdigit()]
        if invalid_ids:
            show_snackbar(page, f"❌ IDs inválidos (deben ser numéricos): {', '.join(invalid_ids[:3])}", is_error=True)
            return
        
        # Leer IDs existentes
        ids_file = Path('backend/mastodon_ids.txt')
        existing_ids = set()
        if ids_file.exists():
            existing_ids = set(ids_file.read_text().strip().split('\n'))
        
        # Filtrar IDs duplicados
        new_unique_ids = [id for id in ids_list if id not in existing_ids]
        
        if not new_unique_ids:
            show_snackbar(page, "ℹ️ Todos los IDs ya existen en el archivo")
            return
        
        # Agregar al archivo
        try:
            with open(ids_file, 'a') as f:
                for id in new_unique_ids:
                    f.write(f"{id}\n")
            
            show_snackbar(page, f"✅ {len(new_unique_ids)} IDs agregados correctamente")
            mastodon_ids_input.value = ""  # Limpiar campo
            page.update()
            
        except Exception as ex:
            show_snackbar(page, f"❌ Error al guardar: {str(ex)}", is_error=True)

    # --- Funciones de Eliminación ---
    def clear_all_data(e):
        def close_dlg(e):
            confirm_dialog.open = False
            page.update()

        def confirm_delete(e):
            count = delete_publications_by_network("Mastodon")
            confirm_dialog.open = False
            
            # Recargar datos
            publications.clear()
            comments_map.clear()
            publications_list_view.controls.clear()
            comments_list_view.controls.clear()
            selected_post_title.value = "Selecciona un Toot para ver sus comentarios"
            
            publications_list_view.controls.append(
                ft.Text("No se encontraron datos de Mastodon en PostgreSQL.", style=ft.TextStyle(color=TEXT_SECONDARY))
            )
            
            show_snackbar(page, f"✅ Se eliminaron {count} publicaciones de Mastodon")

        confirm_dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("⚠️ Confirmar eliminación"),
            content=ft.Text("¿Estás seguro de que quieres vaciar TODA la base de datos de Mastodon? Esta acción no se puede deshacer."),
            actions=[
                ft.TextButton("Cancelar", on_click=close_dlg),
                ft.TextButton("Sí, eliminar todo", on_click=confirm_delete, style=ft.ButtonStyle(color=ERROR)),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        page.dialog = confirm_dialog
        confirm_dialog.open = True
        page.update()

    def delete_publication(e):
        post_id = e.control.data
        if delete_publication_by_id(post_id):
            nonlocal publications
            publications = [p for p in publications if p.id != post_id]
            
            control_to_remove = None
            for control in publications_list_view.controls:
                if isinstance(control, ft.Card) and \
                   isinstance(control.content, ft.Container) and \
                   isinstance(control.content.content, ft.ListTile) and \
                   control.content.content.data == post_id:
                    control_to_remove = control
                    break
            
            if control_to_remove:
                publications_list_view.controls.remove(control_to_remove)
                
            comments_list_view.controls.clear()
            selected_post_title.value = "Selecciona un Toot para ver sus comentarios"

            show_snackbar(page, "✅ Publicación eliminada")
        else:
            show_snackbar(page, "❌ Error al eliminar publicación", is_error=True)

    # --- Carga de Datos ---
    publications, comments_map = get_mastodon_data()

    # --- Eventos ---
    def on_post_click(e: ft.ControlEvent) -> None:
        post_id: str = e.control.data 
        page.go(f"/comments/{post_id}")


    # --- Llenar Lista Publicaciones ---
    def load_publications(pubs, comm_map):
        for post in pubs:
            comment_count: int = len(comm_map.get(post.id, []))
            publications_list_view.controls.append(
                ft.Card(
                    content=ft.Container(
                        ft.ListTile(
                            title=ft.Text(post.title_translated or "Sin texto", style=ft.TextStyle(weight=ft.FontWeight.BOLD)),
                            subtitle=ft.Text(post.title_original or "", style=ft.TextStyle(italic=True, color=TEXT_SECONDARY)),
                            trailing=ft.Container(
                                ft.Row([
                                    ft.Text(f"{comment_count}", style=ft.TextStyle(color=MASTODON_COLOR)),
                                    ft.IconButton(
                                        Icons.DELETE, 
                                        icon_color=ERROR, 
                                        tooltip="Eliminar publicación",
                                        on_click=delete_publication,
                                        data=post.id
                                    )
                                ], alignment=ft.MainAxisAlignment.END),
                                width=100
                            ),
                            on_click=on_post_click,
                            data=post.id
                        ),
                        padding=10
                    ),
                    elevation=4,
                )
            )
    
    if not publications:
        publications_list_view.controls.append(
            ft.Text("No se encontraron datos de Mastodon en PostgreSQL.", style=ft.TextStyle(color=TEXT_SECONDARY))
        )
    else:
        load_publications(publications, comments_map)

    # --- Ejecutar Scraper ---
    def run_scraper(e):
        show_snackbar(page, "🔄 Ejecutando scraper de Mastodon... (revisa la terminal)")
        
        def _bg_scrape():
            def progress(msg: str):
                print(f"[Mastodon Config] {msg}")
            
            translator = page.data.get("translator")
            sentiment = page.data.get("sentiment")
            
            try:
                run_mastodon_scrape_opt(
                    progress_callback=progress,
                    translator=translator,
                    sentiment_analyzer=sentiment
                )
                
                # Recargar datos
                nonlocal publications, comments_map
                publications, comments_map = get_mastodon_data()
                
                # Actualizar UI
                publications_list_view.controls.clear()
                if not publications:
                    publications_list_view.controls.append(
                        ft.Text("No se encontraron datos de Mastodon en PostgreSQL.", style=ft.TextStyle(color=TEXT_SECONDARY))
                    )
                else:
                    load_publications(publications, comments_map)
                
                show_snackbar(page, "✅ Datos de Mastodon actualizados")
                page.update()
                
            except Exception as ex:
                show_snackbar(page, f"❌ Error: {str(ex)}", is_error=True)
        
        threading.Thread(target=_bg_scrape, daemon=True).start()

    return ft.View(
        "/dashboard/mastodon",
        [
            ft.AppBar(
                title=ft.Text("🐘 Mastodon", style=ft.TextStyle(color=TEXT_ON_PRIMARY)), 
                bgcolor=MASTODON_COLOR, 
                actions=[
                    ft.IconButton(Icons.ARROW_BACK, on_click=lambda _: page.go("/social_select"))
                ]
            ),
            # Sección de Configuración (Collapsible)
            ft.Card(
                content=ft.ExpansionTile(
                    title=ft.Text("Configuración & Herramientas", style=ft.TextStyle(weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY)),
                    leading=ft.Icon(Icons.SETTINGS, color=PRIMARY),
                    initially_expanded=False,
                    controls=[
                        ft.Container(
                            content=ft.Column([
                                ft.Row([
                                    mastodon_ids_input,
                                    ft.ElevatedButton(
                                        "Agregar IDs",
                                        icon=Icons.ADD,
                                        on_click=add_mastodon_ids,
                                        bgcolor=ACCENT,
                                        color=TEXT_ON_PRIMARY
                                    )
                                ], spacing=15, vertical_alignment=ft.CrossAxisAlignment.START),
                                ft.Divider(),
                                ft.Row([
                                    ft.Icon(Icons.CLOUD_DOWNLOAD, color=PRIMARY, size=20),
                                    ft.Text("Acciones de Datos", style=ft.TextStyle(size=16, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY)),
                                ], spacing=10),
                                ft.ElevatedButton(
                                    "Ejecutar Scraper",
                                    icon=Icons.REFRESH,
                                    on_click=run_scraper,
                                    bgcolor=MASTODON_COLOR,
                                    color=TEXT_ON_PRIMARY
                                ),
                                ft.Divider(),
                                ft.Row([
                                    ft.Icon(Icons.PICTURE_AS_PDF, color=PRIMARY, size=20),
                                    ft.Text("Reportes", style=ft.TextStyle(size=16, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY)),
                                ], spacing=10),
                                ft.ElevatedButton(
                                    "Generar Reporte PDF",
                                    icon=Icons.DOWNLOAD,
                                    on_click=lambda _: generate_pdf_report(page, publications, comments_map),
                                    bgcolor=ft.Colors.ORANGE_700,
                                    color=TEXT_ON_PRIMARY
                                ),
                                ft.Divider(),
                                ft.Row([
                                    ft.Icon(Icons.DELETE_FOREVER, color=ERROR, size=20),
                                    ft.Text("Zona de Peligro", style=ft.TextStyle(size=16, weight=ft.FontWeight.BOLD, color=ERROR)),
                                ], spacing=10),
                                ft.ElevatedButton(
                                    "Vaciar Base de Datos (Mastodon)",
                                    icon=Icons.DELETE_SWEEP,
                                    on_click=clear_all_data,
                                    bgcolor=ERROR,
                                    color=TEXT_ON_PRIMARY
                                )
                            ], spacing=10),
                            padding=15,
                        )
                    ],
                    bgcolor=BG_CARD,
                ),
                elevation=2,
                margin=ft.margin.only(left=10, right=10, top=10, bottom=5)
            ),
            ft.Row(
                [
                    ft.Column(
                        [
                            ft.Text("Publicaciones", style=ft.TextThemeStyle.HEADLINE_SMALL),
                            ft.Divider(),
                            publications_list_view
                        ],
                        expand=3
                    ),
                ],
                expand=True
            )
        ],
        padding=0
    )