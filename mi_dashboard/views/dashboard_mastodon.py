import flet as ft
import threading 
from flet import Colors, Icons, FontWeight, TextThemeStyle, BoxShadow, Offset
from Api.database import SessionLocal, Publication
from Api.mastodon_scraper_opt import run_mastodon_scraper 

# --- VARIABLES GLOBALES DE LA VISTA (Almacenan los datos de Postgres) ---
# Se usan globales para que las funciones internas (como el hilo) puedan
# modificar los datos de la lista de posts y el dashboard se recargue.
PUBLICATIONS = []
COMMENTS_MAP = {}

# --- UTILITIES & LÓGICA DE DATOS ---

def get_mastodon_data_and_sync():
    """Consulta a DB, actualiza las variables globales (PUBLICATIONS, COMMENTS_MAP) y retorna la cuenta de posts."""
    global PUBLICATIONS, COMMENTS_MAP
    session = SessionLocal()
    PUBLICATIONS.clear()
    COMMENTS_MAP.clear()
    
    try:
        pubs_db = session.query(Publication).filter(Publication.red_social == 'Mastodon').all()
        pubs_db.reverse() 
        for p in pubs_db:
            PUBLICATIONS.append(p)
            COMMENTS_MAP[p.id] = [c for c in p.comments]
    except Exception as e:
        print(f"Error DB: {e}")
    finally:
        session.close()
    
    return len(PUBLICATIONS)

def get_sentiment_color(sentiment):
    if sentiment == 'positive': return Colors.TEAL_400
    if sentiment == 'negative': return Colors.PINK_400 
    return Colors.BLUE_GREY_400

def get_sentiment_badge(sentiment, score):
    """Etiqueta visual de sentimiento"""
    color = get_sentiment_color(sentiment)
    icon = Icons.TRENDING_UP if sentiment == 'positive' else (Icons.TRENDING_DOWN if sentiment == 'negative' else Icons.REMOVE)
    return ft.Container(
        content=ft.Row([
            ft.Icon(icon, size=14, color=Colors.WHITE),
            ft.Text(f"{score}", size=11, color=Colors.WHITE, weight=FontWeight.BOLD)
        ], spacing=2, alignment=ft.MainAxisAlignment.CENTER),
        bgcolor=color,
        padding=ft.padding.symmetric(horizontal=8, vertical=2),
        border_radius=12,
        tooltip=f"Sentimiento: {sentiment}"
    )

# --- COMPONENTE DE DIÁLOGO ---

def create_mastodon_id_dialog(page, render_posts_list):
    """
    Crea el componente de diálogo para la gestión de IDs.
    Retorna un ft.AlertDialog configurado y pulido.
    """
    
    txt_ids_input = ft.TextField(
        multiline=True,
        min_lines=4,
        max_lines=8,
        hint_text="Ej: 11045234... (Uno por línea)",
        hint_style=ft.TextStyle(size=12, color=Colors.GREY_400),
        text_size=13,
        bgcolor=Colors.GREY_50,
        border_color=Colors.PURPLE_100,
        focused_border_color=Colors.PURPLE_500,
        border_radius=8,
        content_padding=15,
        autofocus=True,
        expand=True
    )
    
    dlg_add_ids = ft.AlertDialog()

    def close_dlg(e):
        # Limpieza estándar del AlertDialog
        dlg_add_ids.open = False
        page.update()

    def process_ids(e):
        raw_text = txt_ids_input.value
        
        # CERRAR Y LIMPIAR INMEDIATAMENTE
        dlg_add_ids.open = False
        page.update() 
        
        id_list = [line.strip() for line in raw_text.split("\n") if line.strip()]
        
        if not id_list:
            page.snack_bar = ft.SnackBar(ft.Text("⚠️ La lista estaba vacía."), bgcolor=Colors.ORANGE)
            page.snack_bar.open = True
            page.update()
            return

        # Notificar inicio
        page.snack_bar = ft.SnackBar(
            content=ft.Row([
                ft.ProgressRing(width=20, height=20, stroke_width=2, color=Colors.WHITE),
                ft.Text(f"Analizando {len(id_list)} IDs en segundo plano...")
            ]),
            bgcolor=Colors.PURPLE_700,
            duration=5000 
        )
        page.snack_bar.open = True
        page.update()

        # Obtener modelos
        translator = page.data.get("translator")
        sentiment = page.data.get("sentiment")
        
        # --- HILO DE TRABAJO (No bloquea la UI) ---
        def _bg_process():
            def print_progress(msg): 
                print(f"[Mastodon BG] {msg}")
            
            try:
                run_mastodon_scraper(print_progress, id_list, translator, sentiment)
                
                # Recarga de datos y SINCRONIZACIÓN
                get_mastodon_data_and_sync() 
                
                # Actualización visual
                render_posts_list() 
                
                page.snack_bar = ft.SnackBar(ft.Text("✅ Análisis completado con éxito"), bgcolor=Colors.GREEN_600)
                page.snack_bar.open = True
                page.update()

            except Exception as ex:
                print(f"ERROR THREAD: {ex}")
                page.snack_bar = ft.SnackBar(ft.Text(f"Error interno: {ex}"), bgcolor=Colors.RED_600)
                page.snack_bar.open = True
                page.update()

        threading.Thread(target=_bg_process, daemon=True).start()

    # --- DEFINICIÓN DEL DIÁLOGO PULIDO ---
    dlg_add_ids.content = ft.Container(
        width=450,
        height=250, 
        content=ft.Column([
            ft.Text("Ingresa los IDs o enlaces de los Toots (uno por línea).", size=12, color=Colors.GREY_600),
            ft.Container(height=10),
            txt_ids_input
        ])
    )
    
    dlg_add_ids.title = ft.Row([
        ft.Icon(Icons.ADD_LINK, color=Colors.PURPLE_700),
        ft.Text("Gestionar Toots", weight=FontWeight.BOLD, color=Colors.PURPLE_900, size=18)
    ], alignment=ft.MainAxisAlignment.START)
    
    dlg_add_ids.actions = [
        # Botón CANCELAR (Izquierda - Jerarquía baja)
        ft.TextButton(
            "Cancelar", 
            on_click=close_dlg,
            style=ft.ButtonStyle(color=Colors.GREY_600)
        ),
        ft.Container(expand=True), # Espaciador
        # Botón ANALIZAR (Derecha - Jerarquía alta)
        ft.ElevatedButton(
            content=ft.Row([
                ft.Icon(Icons.ANALYTICS_OUTLINED, size=18, color=Colors.WHITE), 
                ft.Text("Analizar", weight=FontWeight.BOLD)
            ], spacing=5),
            on_click=process_ids,
            style=ft.ButtonStyle(
                bgcolor={"": Colors.PURPLE_600, "hover": Colors.PURPLE_700},
                color=Colors.WHITE,
                elevation=0,
                shape=ft.RoundedRectangleBorder(radius=8),
                padding=ft.padding.symmetric(horizontal=20, vertical=12)
            )
        )
    ]
    
    # Propiedades del Diálogo (Para el diseño pulido)
    dlg_add_ids.actions_alignment = ft.MainAxisAlignment.START 
    dlg_add_ids.actions_padding = ft.padding.only(right=10, bottom=10)
    dlg_add_ids.shape = ft.RoundedRectangleBorder(radius=12)
    dlg_add_ids.modal = True
    
    return dlg_add_ids

# --- VISTA PRINCIPAL ---
def create_dashboard_view(page: ft.Page) -> ft.View:
    # UI Controls
    publications_list_view = ft.ListView(expand=True, spacing=10, padding=20)
    comments_list_view = ft.ListView(expand=True, spacing=10, padding=10)
    selected_post_title = ft.Text("Selecciona un Toot", style=ft.TextThemeStyle.TITLE_MEDIUM)

    # Load Data
    publications, comments_map = get_mastodon_data()

    if not publications:
        publications_list_view.controls.append(ft.Text("No hay datos de Mastodon."))

    def on_post_click(e):
        post_id = e.control.data 
        selected_post = next((p for p in publications if p.id == post_id), None)
        if selected_post:
            selected_post_title.value = f"Comentarios de: {selected_post.title_translated[:50]}..."
        
        comments_list_view.controls.clear()
        comments_for_post = comments_map.get(post_id, [])
        
        if not comments_for_post:
            comments_list_view.controls.append(ft.ListTile(title=ft.Text("Sin comentarios.")))
        else:
            for comment in comments_for_post:
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

    for post in publications:
        comment_count = len(comments_map.get(post.id, []))
        publications_list_view.controls.append(
            ft.Card(
                content=ft.Container(
                    ft.ListTile(
                        title=ft.Text(post.title_translated or "", weight=ft.FontWeight.BOLD),
                        subtitle=ft.Text(post.title_original or "", italic=True, color=Colors.GREY_500),
                        trailing=ft.Text(f"{comment_count}", color=Colors.PURPLE_500),
                        on_click=on_post_click,
                        data=post.id
                    ),
                    padding=10
                ),
                elevation=4,
            )
        )

    return ft.View(
        "/dashboard/mastodon",
        [
            ft.AppBar(title=ft.Text("🐘 Mastodon"), bgcolor=Colors.PURPLE_700, actions=[ft.IconButton(Icons.ARROW_BACK, on_click=lambda _: page.go("/social_select"))]),
            ft.Row(
                [
                    ft.Column([ft.Text("Publicaciones"), ft.Divider(), publications_list_view], expand=3),
                    ft.VerticalDivider(width=1),
                    ft.Column([selected_post_title, ft.Divider(), comments_list_view], expand=2)
                ],
                expand=True
            )
        ],
        padding=0
    )