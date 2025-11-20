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

    # --- FUNCIÓN DE ACTUALIZACIÓN (THREADING SEGURO) ---
    def run_update_process(e):
        
        page.snack_bar = ft.SnackBar(
            content=ft.Row([
                ft.ProgressRing(width=20, height=20, stroke_width=2, color=Colors.WHITE),
                ft.Text("Iniciando descarga de Facebook...")
            ]),
            bgcolor=Colors.BLUE_900,
            duration=4000
        )
        page.snack_bar.open = True
        page.update()
        
        translator = page.data.get("translator")
        sentiment = page.data.get("sentiment")
        
        if not translator or not sentiment:
            page.snack_bar = ft.SnackBar(ft.Text("⚠️ Modelos IA cargando. Espera 10s y reintenta."), bgcolor=Colors.AMBER_800)
            page.snack_bar.open = True
            page.update()
            return
            
        def update_ui_after_task(success=True, error_msg=None):
            if success:
                nonlocal selected_post_id
                selected_post_id = None
                header_comments.value = "Selecciona una publicación"
                
                publications.clear()
                comments_map.clear()
                new_pubs, new_comms = get_facebook_data()
                publications.extend(new_pubs)
                comments_map.update(new_comms) 
                
                render_posts_list() 
                render_comments(None)
                
                page.snack_bar = ft.SnackBar(ft.Text("✅ Datos de Facebook actualizados."), bgcolor=Colors.GREEN_600)
            else:
                page.snack_bar = ft.SnackBar(ft.Text(f"❌ Error en scraper: {error_msg}"), bgcolor=Colors.RED_600)
            
            page.snack_bar.open = True
            page.update()
            
        def _bg_task():
            def progress(msg): print(f"[Facebook BG] {msg}")
            
            try:
                run_facebook_scrape_opt(progress, translator, sentiment)
                page.run_thread(lambda: update_ui_after_task(True))
                
            except Exception as ex:
                page.run_thread(lambda: update_ui_after_task(False, ex))
        
        threading.Thread(target=_bg_task, daemon=True).start()

    # --- RENDERIZADO DE COMENTARIOS (INVERSIÓN DE ORDEN) ---
    def render_comments(post_id):
        comments_column.controls.clear()
        
        if not post_id:
             comments_column.controls.append(
                ft.Container(
                    content=ft.Column([
                        ft.Icon(Icons.COMMENT_OUTLINE, size=40, color=Colors.GREY_300),
                        ft.Text("Selecciona una publicación para ver los comentarios.", color=Colors.GREY_400)
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    alignment=ft.alignment.center,
                    padding=40
                )
            )
             page.update()
             return

        comments = comments_map.get(post_id, [])
        
        if not comments:
            comments_column.controls.append(
                ft.Container(
                    content=ft.Column([
                        ft.Icon(Icons.COMMENTS_DISABLED_OUTLINED, size=40, color=Colors.GREY_300),
                        ft.Text("Sin comentarios", color=Colors.GREY_400)
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    alignment=ft.alignment.center,
                    padding=40
                )
            )
        else:
            for c in comments:
                # Aseguramos que el texto a mostrar tenga contenido
                # 🚨 El texto traducido (ESPAÑOL) será el principal
                spanish_text = c.text_translated if c.text_translated and len(c.text_translated.strip()) > 0 else "Traducción no disponible"
                # 🚨 El texto original (INGLÉS) será el secundario
                original_text = c.text_original if c.text_original and len(c.text_original.strip()) > 0 else "Original no disponible"


                comments_column.controls.append(
                    ft.Container(
                        content=ft.Column([
                            ft.Row([
                                ft.Icon(Icons.PERSON, size=16, color=Colors.BLUE_GREY_300),
                                ft.Text(c.author or "Anónimo", weight=FontWeight.BOLD, size=13, color=Colors.BLUE_GREY_800),
                                ft.Container(expand=True),
                                get_sentiment_badge(c.sentiment_label, c.sentiment_score)
                            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                            ft.Container(height=5),
                            
                            # 🚨 1. TRADUCCIÓN (ESPAÑOL)
                            ft.Text(
                                spanish_text, 
                                size=14, 
                                color=Colors.BLACK87,
                                weight=FontWeight.NORMAL
                            ),
                            
                            # 🚨 2. ORIGINAL (INGLÉS, ITALIC)
                            ft.Text(
                                original_text,
                                size=11, 
                                color=Colors.GREY_600,
                                italic=True
                            ),
                        ]),
                        padding=15,
                        bgcolor=Colors.WHITE,
                        border=ft.border.all(1, Colors.GREY_200),
                        border_radius=8,
                        shadow=ft.BoxShadow(blur_radius=5, color=Colors.with_opacity(0.05, Colors.BLACK), offset=ft.Offset(0, 2))
                    )
                )
        page.update()

    # --- RENDERIZADO DE POSTS (IZQUIERDA) ---
    def render_posts_list():
        posts_column.controls.clear()
        
        if not publications:
            posts_column.controls.append(
                ft.Container(
                    content=ft.Column([
                        ft.Text("No hay datos descargados.", italic=True, color=Colors.GREY_400),
                        ft.Text("Usa el botón de actualizar (↻) arriba.", size=10, color=Colors.BLUE_400)
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    padding=20, alignment=ft.alignment.center
                )
            )
            page.update()
            return

        for p in publications:
            total_comms = len(comments_map.get(p.id, []))
            is_selected = (p.id == selected_post_id)
            
            posts_column.controls.append(
                ft.Container(
                    content=ft.Row([
                        ft.Container(width=4, bgcolor=Colors.BLUE_800 if is_selected else Colors.TRANSPARENT, border_radius=2),
                        ft.Container(width=10),
                        ft.Column([
                            ft.Text(
                                p.title_translated[:50] + "..." if p.title_translated else "Multimedia",
                                weight=FontWeight.BOLD if is_selected else FontWeight.NORMAL,
                                color=Colors.BLUE_900 if is_selected else Colors.BLACK87,
                                size=14
                            ),
                            ft.Text(f"ID: {p.id[:15]}...", size=11, color=Colors.GREY_500, italic=True)
                        ], spacing=2, expand=True),
                        
                        ft.Container(
                            content=ft.Text(str(total_comms), size=10, color=Colors.WHITE),
                            bgcolor=Colors.BLUE_GREY_400 if not is_selected else Colors.BLUE_600,
                            padding=ft.padding.symmetric(horizontal=6, vertical=2),
                            border_radius=10
                        )
                    ]),
                    padding=ft.padding.symmetric(vertical=12, horizontal=10),
                    bgcolor=Colors.BLUE_50 if is_selected else Colors.WHITE,
                    border_radius=5,
                    on_click=lambda e, pid=p.id, title=p.title_translated: on_select_post(pid, title),
                    ink=True,
                )
            )
            posts_column.controls.append(ft.Divider(height=1, color=Colors.GREY_100))
        page.update()

    # --- MANEJO DE EVENTOS (CON TOGGLE) ---
    def on_select_post(pid, title):
        nonlocal selected_post_id
        
        full_title = title or "Publicación sin texto"

        # Toggle (seleccionar o deseleccionar)
        if selected_post_id == pid:
            selected_post_id = None
            header_comments.value = "Selecciona una publicación"
            comments_to_render = None
        else:
            selected_post_id = pid
            header_comments.value = f"{full_title[:40]}..."
            header_comments.color = Colors.BLACK87
            header_comments.weight = FontWeight.BOLD
            comments_to_render = pid
            
        render_posts_list()
        render_comments(comments_to_render)

    render_posts_list()

    # --- LAYOUT FINAL ---
    return ft.View(
        "/dashboard/facebook",
        [
            # 1. Barra Superior
            ft.AppBar(
                leading=ft.IconButton(Icons.ARROW_BACK, icon_color=Colors.WHITE, on_click=lambda _: page.go("/social_select")),
                title=ft.Row([
                    ft.Icon(Icons.FACEBOOK, color=Colors.WHITE),
                    ft.Text("Facebook Insights", color=Colors.WHITE, weight=FontWeight.BOLD)
                ], spacing=10),
                bgcolor=Colors.BLUE_900,
                elevation=0,
                
                # --- BOTÓN DE ACTUALIZACIÓN ---
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