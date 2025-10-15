import flet as ft
from views import login, register, dashboard, comments, social_select # <--- Importación de la nueva vista

def main(page: ft.Page):
    page.title = "Sentimetrika"
    page.window_width = 1000
    page.window_height = 800
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.vertical_alignment = ft.MainAxisAlignment.CENTER

    def route_change(e):
        # Lógica para la vista de comentarios (rutas con parámetros)
        if page.route.startswith("/comments/"):
            post_id = page.route.split("/")[-1]
            # Asegúrate de no limpiar las vistas si estamos apilando una vista modal como 'comments'
            # y solo si la vista padre ya está en el stack. 
            # Aquí, lo mantendremos simple apilando la vista
            page.views.append(comments.create_comments_view(page, post_id))
        
        # Lógica para las vistas principales (rutas sin parámetros)
        else:
            page.views.clear()
            
            # 1. Login
            if page.route == "/login" or page.route == "/":
                page.views.append(login.create_login_view(page))
                
            # 2. Registro
            elif page.route == "/register":
                page.views.append(register.create_register_view(page))
                
            # 3. Vista de Selección de Redes Sociales <--- NUEVA RUTA
            elif page.route == "/social_select":
                page.views.append(social_select.create_social_select_view(page))
                
            # 4. Dashboard
            elif page.route == "/dashboard":
                page.views.append(dashboard.create_dashboard_view(page))

        page.update()

    # --- FUNCIÓN CORREGIDA ---
    def view_pop(e):
        # Comprobamos si hay más de una vista antes de hacer pop
        if len(page.views) > 1:
            page.views.pop()
            top_view = page.views[-1]
            page.go(top_view.route)

    page.on_route_change = route_change
    page.on_view_pop = view_pop

    # Inicia en la ruta /login
    page.go("/login")

ft.app(target=main, assets_dir="assets")
