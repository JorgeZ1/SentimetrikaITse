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

    if not publications:
        publications_list_view.controls.append(ft.Text("No hay datos de Reddit."))

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
                            title=ft.Text(f"u/{comment.author}", weight=ft.FontWeight.BOLD),
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
                        trailing=ft.Text(f"{comment_count}", color=Colors.ORANGE_ACCENT_700),
                        on_click=on_post_click,
                        data=post.id
                    ),
                    padding=10
                ),
                elevation=4,
            )
        )

    return ft.View(
        "/dashboard/reddit",
        [
            ft.AppBar(title=ft.Text("📊 Reddit"), bgcolor=Colors.ORANGE_ACCENT_700, actions=[ft.IconButton(Icons.ARROW_BACK, on_click=lambda _: page.go("/social_select"))]),
            ft.Row(
                [
                    ft.Column([ft.Text("Hilos"), ft.Divider(), publications_list_view], expand=3),
                    ft.VerticalDivider(width=1),
                    ft.Column([selected_post_title, ft.Divider(), comments_list_view], expand=2)
                ],
                expand=True
            )
        ],
        padding=0
    )