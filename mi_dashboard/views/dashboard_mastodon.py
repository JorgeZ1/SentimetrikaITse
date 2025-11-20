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
    
    global PUBLICATIONS, COMMENTS_MAP
    selected_post_id = None
    
    posts_column = ft.Column(spacing=8, scroll=ft.ScrollMode.AUTO, expand=True)
    comments_column = ft.Column(spacing=10, scroll=ft.ScrollMode.AUTO, expand=True)
    header_comments = ft.Text("Selecciona un Toot para analizar", style=TextThemeStyle.TITLE_MEDIUM, color=Colors.GREY_500)

    # Carga inicial y SINCRONIZACIÓN
    get_mastodon_data_and_sync() 

    def render_comments(post_id):
        comments_column.controls.clear()
        comments = COMMENTS_MAP.get(post_id, []) 
        if not comments:
            comments_column.controls.append(ft.Text("Sin respuestas.", color=Colors.GREY_400))
        else:
            for c in comments:
                comments_column.controls.append(
                    ft.Container(
                        content=ft.Column([
                            ft.Row([
                                ft.Row([
                                    ft.Icon(Icons.ACCOUNT_CIRCLE, size=16, color=Colors.PURPLE_300),
                                    ft.Text(f"@{c.author}", weight=FontWeight.BOLD, size=13, color=Colors.PURPLE_900),
                                ], spacing=5),
                                get_sentiment_badge(c.sentiment_label, c.sentiment_score)
                            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                            ft.Container(height=5),
                            ft.Text(c.text_translated or "...", size=14, color=Colors.BLACK87),
                        ]),
                        padding=15, bgcolor=Colors.WHITE, border_radius=8,
                        border=ft.border.all(1, Colors.PURPLE_50),
                        shadow=ft.BoxShadow(blur_radius=4, color=Colors.with_opacity(0.05, Colors.PURPLE_900), offset=ft.Offset(0, 2))
                    )
                )
        page.update()

    def render_posts_list():
        # Esta función recarga el contenido visual usando las listas globales (PUBLICATIONS, COMMENTS_MAP)
        posts_column.controls.clear()
        if not PUBLICATIONS: 
            posts_column.controls.append(
                ft.Container(
                    content=ft.Column([
                        ft.Icon(Icons.DNS, size=40, color=Colors.GREY_300),
                        ft.Text("No hay Toots guardados.", italic=True, color=Colors.GREY_400),
                        ft.Text("Usa el botón 'Gestionar IDs' arriba para añadir.", size=12, color=Colors.PURPLE_700, weight=FontWeight.BOLD)
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    padding=20, alignment=ft.alignment.center
                )
            )
            page.update() 
            return

        for p in PUBLICATIONS: 
            total = len(COMMENTS_MAP.get(p.id, []))
            is_sel = (p.id == selected_post_id)
            
            # --- Contenido del Post ---
            post_content_item = ft.Container(
                content=ft.Row([
                    ft.Container(width=4, bgcolor=Colors.PURPLE_700 if is_sel else Colors.TRANSPARENT, border_radius=2),
                    ft.Container(width=10),
                    ft.Column([
                        ft.Text(p.title_translated[:50] + "...", weight=FontWeight.BOLD if is_sel else FontWeight.NORMAL, color=Colors.PURPLE_900 if is_sel else Colors.BLACK87, size=14),
                        ft.Text(f"ID: {p.id[:10]}...", size=11, color=Colors.GREY_500, italic=True)
                    ], spacing=2, expand=True),
                    ft.Container(content=ft.Text(str(total), size=10, color=Colors.WHITE), bgcolor=Colors.PURPLE_300 if not is_sel else Colors.PURPLE_700, padding=6, border_radius=10)
                ]),
                padding=10, bgcolor=Colors.PURPLE_50 if is_sel else Colors.WHITE, border_radius=5,
            )

            posts_column.controls.append(
                ft.ListTile(
                    # El on_click llama a on_select_post para manejar la lógica
                    on_click=lambda e, pid=p.id, ti=p.title_translated: on_select_post(e, pid, ti),
                    title=post_content_item,
                    content_padding=ft.padding.only(left=0, right=0),
                    selected=is_sel,
                    selected_tile_color=Colors.PURPLE_100, 
                    hover_color=Colors.PURPLE_50,
                )
            )
            posts_column.controls.append(ft.Divider(height=1, color=Colors.GREY_100))
        page.update()

    def on_select_post(e, pid, title):
        nonlocal selected_post_id
        
        # Lógica de Toggle (Si haces clic en el mismo, lo deselecciona)
        if selected_post_id == pid:
            selected_post_id = None # Deseleccionar
            comments_to_render = None
        else:
            selected_post_id = pid # Seleccionar nuevo
            comments_to_render = pid

        header_comments.value = f"{title[:40]}..." if selected_post_id else "Selecciona un Toot para analizar"
        
        render_posts_list() # Redibuja la lista para actualizar el color del post seleccionado
        render_comments(comments_to_render)

    render_posts_list()

    # Creamos el diálogo aquí (usando la función componente)
    mastodon_dialog = create_mastodon_id_dialog(page, render_posts_list)

    # --- FUNCIÓN SEGURA PARA ABRIR DIÁLOGO ---
    def open_dlg_safe(e):
        # Accediendo al TextField dentro del diálogo para limpiarlo
        txt_input_control = mastodon_dialog.content.content.controls[2] 
        txt_input_control.value = ""
        
        try:
            # Abrir usando el método nativo del diálogo
            page.dialog = mastodon_dialog
            mastodon_dialog.open = True
            page.update()
        except Exception as ex:
            print(f"Error abriendo diálogo: {ex}")


    return ft.View(
        "/dashboard/mastodon",
        [
            ft.AppBar(
                leading=ft.IconButton(Icons.ARROW_BACK, icon_color=Colors.WHITE, on_click=lambda _: page.go("/social_select")),
                title=ft.Row([
                    ft.Icon(Icons.HUB, color=Colors.WHITE),
                    ft.Text("Mastodon Fediverse", color=Colors.WHITE, weight=FontWeight.BOLD)
                ], spacing=10),
                actions=[
                    ft.TextButton(
                        "Gestionar IDs", 
                        icon=Icons.EDIT_DOCUMENT, 
                        icon_color=Colors.WHITE, 
                        style=ft.ButtonStyle(color=Colors.WHITE), 
                        on_click=open_dlg_safe 
                    ),
                    ft.Container(width=10)
                ],
                bgcolor=Colors.PURPLE_800,
                elevation=0,
            ),
            ft.Container(content=ft.Row([
                    ft.Container(content=ft.Column([ft.Container(content=ft.Text("TIMELINE LOCAL", size=11, weight=FontWeight.BOLD, color=Colors.GREY_500), padding=ft.padding.only(left=10, top=15, bottom=5)), posts_column], expand=True), expand=4, bgcolor=Colors.WHITE, border=ft.border.only(right=ft.BorderSide(1, Colors.GREY_200))),
                    ft.Container(content=ft.Column([ft.Container(content=ft.Column([ft.Text("RESPUESTAS Y SENTIMIENTO", size=11, weight=FontWeight.BOLD, color=Colors.PURPLE_200), ft.Container(height=5), header_comments]), padding=20, bgcolor=Colors.GREY_50, border=ft.border.only(bottom=ft.BorderSide(1, Colors.GREY_200))), ft.Container(content=comments_column, padding=20, expand=True)]), expand=7, bgcolor=Colors.GREY_50)
                ], spacing=0, expand=True), expand=True)
        ], padding=0
    )