import flet as ft

def show_snackbar(page: ft.Page, message: str, is_error: bool = False):
    """
    Muestra un SnackBar. Si es un error, añade un botón para ver detalles si el mensaje es largo.
    """
    
    def show_details(e):
        dlg = ft.AlertDialog(
            title=ft.Text("Detalles del Error"),
            content=ft.Text(message, selectable=True),
            actions=[
                ft.TextButton("Cerrar", on_click=lambda _: close_dlg(dlg))
            ],
        )
        page.dialog = dlg
        dlg.open = True
        page.update()

    def close_dlg(dlg):
        dlg.open = False
        page.update()

    action = None
    if is_error and len(message) > 50:
        action = "Ver detalles"
        on_action = show_details
    else:
        on_action = None

    page.snack_bar = ft.SnackBar(
        content=ft.Text(message[:100] + "..." if len(message) > 100 and not action else message),
        bgcolor=ft.Colors.RED if is_error else ft.Colors.GREEN,
        action=action,
        on_action=on_action if action else None,
        duration=5000 if is_error else 3000
    )
    page.snack_bar.open = True
    page.update()