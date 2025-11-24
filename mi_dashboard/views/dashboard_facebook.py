import flet as ft
from flet import Colors, Icons
# Importamos la conexión y modelos
from Api.database import SessionLocal, Publication 

def get_facebook_data():
    """Consulta PostgreSQL y estructura los datos para la vista"""
    session = SessionLocal()
    publications = []
    comments_map = {} 
    
    try:
        # Filtramos por red social usando el ORM
        pubs_db = session.query(Publication).filter(Publication.red_social == 'Facebook').all()
        
        for p in pubs_db:
            publications.append(p)
            # Convertimos la relación de SQLAlchemy a una lista simple
            # p.comments funciona "mágicamente" gracias a la relationship en el modelo
            comments_map[p.id] = [c for c in p.comments]
            
    except Exception as e:
        print(f"Error leyendo DB: {e}")
    finally:
        session.close()
        
    return publications, comments_map

def get_sentiment_icon(sentiment):
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
    
    selected_post_title = ft.Text("Haz clic en una publicación para ver sus comentarios",
                                  style=ft.TextThemeStyle.TITLE_MEDIUM,
                                  weight=ft.FontWeight.BOLD)

    # --- Carga de Datos ---
    publications, comments_map = get_facebook_data()

    if not publications:
        publications_list_view.controls.append(
            ft.Text("No se encontraron datos de Facebook en PostgreSQL.", style=ft.TextStyle(color=Colors.GREY_500))
        )

    # --- Eventos ---
    def on_post_click(e):
        post_id = e.control.data 
        
        selected_post = next((p for p in publications if p.id == post_id), None)
        if selected_post:
            # Accedemos con punto (.) porque ahora son objetos
            title_text = selected_post.title_translated or "Sin título"
            selected_post_title.value = f"Comentarios de: {title_text[:50]}..."
        
        comments_list_view.controls.clear()
        comments_for_post = comments_map.get(post_id, [])
        
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
                            title=ft.Text(f"@{comment.author}", style=ft.TextStyle(weight=ft.FontWeight.BOLD)),
                            subtitle=ft.Text(comment.text_translated or "", style=ft.TextStyle(color=Colors.GREY_400))
                        ),
                        elevation=2
                    )
                )
        page.update()

    # --- Llenar Lista Publicaciones ---
    for post in publications:
        comment_count = len(comments_map.get(post.id, []))
        publications_list_view.controls.append(
            ft.Card(
                content=ft.Container(
                    ft.ListTile(
                        title=ft.Text(post.title_translated or "Sin texto", style=ft.TextStyle(weight=ft.FontWeight.BOLD)),
                        subtitle=ft.Text(post.title_original or "", style=ft.TextStyle(italic=True, color=Colors.GREY_500)),
                        trailing=ft.Text(f"{comment_count} Comentarios", style=ft.TextStyle(color=Colors.BLUE_800)),
                        on_click=on_post_click,
                        data=post.id
                    ),
                    padding=10
                ),
                elevation=4,
            )
        )

    return ft.View(
        "/dashboard/facebook",
        [
            ft.AppBar(
                title=ft.Text("📘 Dashboard de Facebook", style=ft.TextStyle(color=Colors.WHITE)),
                bgcolor=Colors.BLUE_800,
                actions=[
                    ft.IconButton(Icons.ARROW_BACK, on_click=lambda _: page.go("/social_select"))
                ]
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