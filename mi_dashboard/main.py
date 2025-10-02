import flet as ft
from views import login, register, dashboard, comments

def main(page: ft.Page):
    page.title = "Sentimetrika"
    page.window_width = 1000
    page.window_height = 800
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.vertical_alignment = ft.MainAxisAlignment.CENTER

    def route_change(e):
        # NOTA: Ya no usamos page.views.clear() aquí
        
        # Lógica para la vista de comentarios
        if page.route.startswith("/comments/"):
            # 1. CORRECCIÓN: Quitamos int() para mantener el ID como string
            post_id = page.route.split("/")[-1]
            page.views.append(comments.create_comments_view(page, post_id))
        
        # Lógica para las vistas principales (estas SÍ limpian el historial)
        else:
            page.views.clear() # Limpiamos solo al ir a una vista principal
            if page.route == "/login":
                page.views.append(login.create_login_view(page))
            elif page.route == "/register":
                page.views.append(register.create_register_view(page))
            elif page.route == "/dashboard":
                page.views.append(dashboard.create_dashboard_view(page))

        page.update()

    def view_pop(e):
        page.views.pop()
        top_view = page.views[-1]
        page.go(top_view.route)

    page.on_route_change = route_change
    page.on_view_pop = view_pop

    page.go("/login")

ft.app(target=main, assets_dir="assets")