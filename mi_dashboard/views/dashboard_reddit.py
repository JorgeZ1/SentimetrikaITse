import flet as ft
from flet import Colors, Icons, FontWeight, TextThemeStyle
from Api.database import SessionLocal, Publication
from Api.reddit_scraper_opt import run_reddit_scraper 

def get_reddit_data():
    """Consulta a DB"""
    session = SessionLocal()
    publications = []
    comments_map = {} 
    try:
        # Traemos los posts invertidos (más nuevos primero)
        pubs_db = session.query(Publication).filter(Publication.red_social == 'Reddit').all()
        pubs_db.reverse() 
        for p in pubs_db:
            publications.append(p)
            comments_map[p.id] = [c for c in p.comments]
    except Exception as e:
        print(f"Error DB: {e}")
    finally:
        session.close()
    return publications, comments_map

def get_sentiment_color(sentiment):
    if sentiment == 'positive': return Colors.GREEN_600
    if sentiment == 'negative': return Colors.RED_600
    return Colors.BLUE_GREY_300

def get_sentiment_badge(sentiment, score):
    color = get_sentiment_color(sentiment)
    icon = Icons.ARROW_UPWARD if sentiment == 'positive' else (Icons.ARROW_DOWNWARD if sentiment == 'negative' else Icons.REMOVE)
    return ft.Container(
        content=ft.Row([
            ft.Icon(icon, size=14, color=Colors.WHITE),
            ft.Text(f"{score}", size=11, color=Colors.WHITE, weight=FontWeight.BOLD)
        ], spacing=2, alignment=ft.MainAxisAlignment.CENTER),
        bgcolor=color,
        padding=ft.padding.symmetric(horizontal=8, vertical=2),
        border_radius=4,
        tooltip=f"Sentimiento: {sentiment}"
    )

def create_dashboard_view(page: ft.Page) -> ft.View:
    selected_post_id = None
    posts_column = ft.Column(spacing=8, scroll=ft.ScrollMode.AUTO, expand=True)
    comments_column = ft.Column(spacing=10, scroll=ft.ScrollMode.AUTO, expand=True)
    header_comments = ft.Text("Selecciona un Hilo", style=TextThemeStyle.TITLE_MEDIUM, color=Colors.GREY_500)
    
    txt_search = ft.TextField(
        hint_text="Tema (ej: Python)", height=35, text_size=12, content_padding=10,
        bgcolor=Colors.WHITE, border_radius=8, color=Colors.BLACK, width=200,
        on_submit=lambda e: run_search(e)
    )

    publications, comments_map = get_reddit_data()

    def render_comments(post_id):
        comments_column.controls.clear()
        comments = comments_map.get(post_id, [])
        if not comments:
            comments_column.controls.append(ft.Text("Sin comentarios.", color=Colors.GREY_400))
        else:
            for c in comments:
                comments_column.controls.append(
                    ft.Container(
                        content=ft.Column([
                            ft.Row([
                                ft.Row([ft.Icon(Icons.ANDROID, size=16, color=Colors.ORANGE_800), ft.Text(f"u/{c.author}", weight=FontWeight.BOLD, size=12, color=Colors.BLACK87)], spacing=5),
                                get_sentiment_badge(c.sentiment_label, c.sentiment_score)
                            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                            ft.Container(height=5),
                            ft.Text(c.text_translated or "...", size=13, color=Colors.BLACK87),
                        ]),
                        padding=15, bgcolor=Colors.WHITE, border_radius=5,
                        border=ft.border.only(left=ft.BorderSide(3, Colors.GREY_300), bottom=ft.BorderSide(1, Colors.GREY_100))
                    )
                )
        page.update()

    def render_posts_list():
        posts_column.controls.clear()
        if not publications:
            posts_column.controls.append(ft.Text("No hay resultados.", italic=True, color=Colors.GREY_400))
            page.update()
            return

        for p in publications:
            total = len(comments_map.get(p.id, []))
            is_sel = (p.id == selected_post_id)
            posts_column.controls.append(
                ft.Container(
                    content=ft.Row([
                        ft.Container(width=4, bgcolor=Colors.ORANGE_900 if is_sel else Colors.TRANSPARENT),
                        ft.Column([
                            ft.Text(p.title_translated[:60] + "...", weight=FontWeight.BOLD if is_sel else FontWeight.NORMAL, color=Colors.BLACK if is_sel else Colors.BLACK87, size=14),
                            ft.Text(f"ID: {p.id[:10]}...", size=11, color=Colors.GREY_500)
                        ], spacing=2, expand=True),
                        ft.Container(content=ft.Row([ft.Icon(Icons.FORUM_OUTLINED, size=12, color=Colors.ORANGE_800), ft.Text(str(total), size=11, color=Colors.ORANGE_900, weight=FontWeight.BOLD)], spacing=2), padding=4, bgcolor=Colors.ORANGE_50, border_radius=10)
                    ]),
                    padding=10, bgcolor=Colors.ORANGE_50 if is_sel else Colors.WHITE, border_radius=5,
                    on_click=lambda e, pid=p.id, ti=p.title_translated: on_select_post(pid, ti), ink=True
                )
            )
            posts_column.controls.append(ft.Divider(height=1, color=Colors.GREY_200))
        page.update()

    def on_select_post(pid, title):
        nonlocal selected_post_id
        selected_post_id = pid
        header_comments.value = f"{title[:40]}..."
        render_posts_list()
        render_comments(pid)

    def run_search(e):
        topic = txt_search.value
        if not topic: return
        
        # --- AQUÍ OBTENEMOS LOS MODELOS DEL MAIN ---
        translator = page.data.get("translator")
        sentiment = page.data.get("sentiment")

        if not translator or not sentiment:
             page.snack_bar = ft.SnackBar(ft.Text("⚠️ Modelos cargando... intenta en 10 segundos"), bgcolor=Colors.AMBER_800)
             page.snack_bar.open = True
             page.update()
             return

        page.snack_bar = ft.SnackBar(ft.Row([ft.ProgressRing(width=20, height=20, color=Colors.WHITE), ft.Text(f"Analizando '{topic}'...")]), bgcolor=Colors.ORANGE_900, duration=5000)
        page.snack_bar.open = True
        page.update()

        def print_progress(msg): print(f"[Reddit UI] {msg}")

        try:
            # PASAMOS LOS MODELOS AL SCRAPER
            run_reddit_scraper(
                progress_callback=print_progress, 
                search_query=topic, 
                translator=translator,        # <--- CEREBRO
                sentiment_analyzer=sentiment, # <--- CORAZÓN
                limit=5
            )
            
            publications.clear()
            comments_map.clear()
            new_pubs, new_comms = get_reddit_data()
            publications.extend(new_pubs)
            comments_map.update(new_comms)
            
            render_posts_list()
            page.snack_bar = ft.SnackBar(ft.Text(f"✅ Análisis de '{topic}' completado"), bgcolor=Colors.GREEN_700)
            page.snack_bar.open = True
            page.update()

        except Exception as ex:
            page.snack_bar = ft.SnackBar(ft.Text(f"Error: {ex}"), bgcolor=Colors.RED_700)
            page.snack_bar.open = True
            page.update()

    render_posts_list()

    return ft.View(
        "/dashboard/reddit",
        [
            ft.AppBar(
                leading=ft.IconButton(Icons.ARROW_BACK, icon_color=Colors.WHITE, on_click=lambda _: page.go("/social_select")),
                title=ft.Row([ft.Icon(Icons.REDDIT, color=Colors.WHITE), ft.Text("Reddit Trends", color=Colors.WHITE, weight=FontWeight.BOLD)], spacing=10),
                actions=[ft.Container(content=ft.Row([txt_search, ft.IconButton(Icons.SEARCH, icon_color=Colors.WHITE, tooltip="Buscar", on_click=run_search)]), padding=ft.padding.only(right=20))],
                bgcolor=Colors.DEEP_ORANGE_ACCENT_700, elevation=0,
            ),
            ft.Container(content=ft.Row([
                    ft.Container(content=ft.Column([ft.Container(content=ft.Text("HILOS ENCONTRADOS", size=11, weight=FontWeight.BOLD, color=Colors.GREY_500), padding=ft.padding.only(left=10, top=15, bottom=5)), posts_column], expand=True), expand=4, bgcolor=Colors.WHITE, border=ft.border.only(right=ft.BorderSide(1, Colors.GREY_200))),
                    ft.Container(content=ft.Column([ft.Container(content=ft.Column([ft.Text("ANÁLISIS DE SENTIMIENTOS", size=11, weight=FontWeight.BOLD, color=Colors.ORANGE_300), ft.Container(height=5), header_comments]), padding=20, bgcolor=Colors.GREY_50, border=ft.border.only(bottom=ft.BorderSide(1, Colors.GREY_200))), ft.Container(content=comments_column, padding=20, expand=True)]), expand=7, bgcolor=Colors.GREY_50)
                ], spacing=0, expand=True), expand=True)
        ], padding=0
    )