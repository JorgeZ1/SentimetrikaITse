import flet as ft
from flet import Colors, Icons
from Api.database import SessionLocal, Publication, Comment
from typing import List, Dict, Any

def get_reddit_data() -> (List[Publication], Dict[str, List[Comment]]):
    """Consulta PostgreSQL y estructura los datos para la vista"""
    session = SessionLocal()
    publications: List[Publication] = []
    comments_map: Dict[str, List[Comment]] = {} 
    
    try:
        # Filtramos por red social usando el ORM
        pubs_db = session.query(Publication).filter(Publication.red_social == 'Reddit').all()
        
        for p in pubs_db:
            publications.append(p)
            # Convertimos la relación de SQLAlchemy a una lista simple
            comments_map[p.id] = [c for c in p.comments]
            
    except Exception as e:
        print(f"Error leyendo DB: {e}")
    finally:
        session.close()
        
    return publications, comments_map

def get_sentiment_icon(sentiment: str) -> ft.Icon:
    if sentiment == 'positive':
        return ft.Icon(Icons.SENTIMENT_VERY_SATISFIED, color=Colors.GREEN_500)
    elif sentiment == 'negative':
        return ft.Icon(Icons.SENTIMENT_VERY_DISSATISFIED, color=Colors.RED_500)
    else: 
        return ft.Icon(Icons.SENTIMENT_NEUTRAL, color=Colors.GREY_500)

def create_dashboard_view(page: ft.Page) -> ft.View:
    
    # --- Controles UI ---
    publications_list_view = ft.ListView(expand=True, spacing=10, padding=20)
    comments_list_view = ft.ListView(expand=True, spacing=10, padding=10)
    
    selected_post_title = ft.Text(
        "Selecciona un Hilo para ver sus comentarios",
        style=ft.TextThemeStyle.TITLE_MEDIUM
    )

    # --- Carga de Datos ---
    publications, comments_map = get_reddit_data()

    if not publications:
        publications_list_view.controls.append(
            ft.Text("No se encontraron datos de Reddit en PostgreSQL.", style=ft.TextStyle(color=Colors.GREY_500))
        )

    # --- Eventos ---
    def on_post_click(e: ft.ControlEvent) -> None:
        post_id: str = e.control.data 
        
        selected_post: Publication = next((p for p in publications if p.id == post_id), None)
        if selected_post:
            # Accedemos con punto (.) porque ahora son objetos
            title_text: str = selected_post.title_translated or "Sin título"
            selected_post_title.value = f"Comentarios de: {title_text[:50]}..."
        
        comments_list_view.controls.clear()
        comments_for_post: List[Comment] = comments_map.get(post_id, [])
        
        if not comments_for_post:
            comments_list_view.controls.append(
                ft.ListTile(title=ft.Text("No se encontraron comentarios.", style=ft.TextStyle(color=Colors.GREY_500)))
            )
        else:
            for comment in comments_for_post:
                # Accedemos con punto (.)
                comments_list_view.controls.append(
                    ft.Card(
                        ft.ListTile(
                            leading=get_sentiment_icon(comment.sentiment_label),
                            title=ft.Text(f"u/{comment.author}", style=ft.TextStyle(weight=ft.FontWeight.BOLD)),
                            subtitle=ft.Text(comment.text_translated or "", style=ft.TextStyle(color=Colors.GREY_400))
                        ),
                        elevation=2
                    )
                )
        page.update()

    # --- Llenar Lista Publicaciones ---
    for post in publications:
        comment_count: int = len(comments_map.get(post.id, []))
        publications_list_view.controls.append(
            ft.Card(
                content=ft.Container(
                    ft.ListTile(
                        title=ft.Text(post.title_translated or "Sin texto", style=ft.TextStyle(weight=ft.FontWeight.BOLD)),
                        subtitle=ft.Text(post.title_original or "", style=ft.TextStyle(italic=True, color=Colors.GREY_500)),
                        trailing=ft.Text(f"{comment_count}", style=ft.TextStyle(color=Colors.ORANGE_ACCENT_700)),
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
            ft.AppBar(
                title=ft.Text("📊 Reddit", style=ft.TextStyle(color=Colors.WHITE)), 
                bgcolor=Colors.ORANGE_ACCENT_700, 
                actions=[
                    ft.IconButton(Icons.ARROW_BACK, on_click=lambda _: page.go("/social_select"))
                ]
            ),
            ft.Row(
                [
                    ft.Column(
                        [
                            ft.Text("Hilos", style=ft.TextThemeStyle.HEADLINE_SMALL),
                            ft.Divider(),
                            publications_list_view
                        ],
                        expand=3
                    ),
                    ft.VerticalDivider(width=1, color=Colors.GREY_300),
                    ft.Column(
                        [
                            selected_post_title,
                            ft.Divider(),
                            comments_list_view
                        ],
                        expand=2
                    )
                ],
                expand=True
            )
        ],
        padding=0
    )