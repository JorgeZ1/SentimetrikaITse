import flet as ft
from views import login, register, dashboard, comments

def main(page: ft.Page):
    page.title = "Sentimetrika"
    page.window_width = 1000
    page.window_height = 800
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.vertical_alignment = ft.MainAxisAlignment.CENTER

    def route_change(e):
        page.views.clear()
        if page.route == "/login":
            page.views.append(login.create_login_view(page))
        elif page.route == "/register":
            page.views.append(register.create_register_view(page))
        elif page.route == "/dashboard":
            page.views.append(dashboard.create_dashboard_view(page))
        elif page.route.startswith("/comments/"):
            post_id = int(page.route.split("/")[-1])
            page.views.append(comments.create_comments_view(page, post_id))
        page.update()

    def view_pop(e):
        page.views.pop()
        page.go(page.views[-1].route)

    page.on_route_change = route_change
    page.on_view_pop = view_pop

    page.go("/login")

ft.app(target=main, assets_dir="assets")
