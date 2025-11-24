import flet as ft
from mi_dashboard.views.login import create_login_view
from mi_dashboard.views.register import create_register_view
from mi_dashboard.views.social_select import create_social_select_view
from mi_dashboard.views.dashboard_facebook import create_dashboard_view as create_facebook_view
from mi_dashboard.views.dashboard_reddit import create_dashboard_view as create_reddit_view
from mi_dashboard.views.dashboard_mastodon import create_dashboard_view as create_mastodon_view
from mi_dashboard.theme import get_theme

# --- IMPORTANTE: Importar la inicialización de la DB ---
from Api.database import init_db

# --- Imports para correr scrapers en hilo (igual que antes) ---
import threading
# Importar los scrapers optimizados (ahora usan Postgres)
from Api.reddit_scraper_opt import run_reddit_scrape_opt
from Api.facebook_scraper_opt import run_facebook_scrape_opt
from Api.mastodon_scraper_opt import run_mastodon_scrape_opt
from transformers import pipeline

# Variables globales para modelos (cargan una vez)
translator_model = None
sentiment_model = None

def load_models():
    global translator_model, sentiment_model
    print("Cargando modelos de IA (esto puede tardar un poco)...")
    try:
        translator_model = pipeline("translation", model="Helsinki-NLP/opus-mt-es-en")
        sentiment_model = pipeline("text-classification", model="cardiffnlp/twitter-roberta-base-sentiment-latest")
        print("✅ Modelos cargados.")
    except Exception as e:
        print(f"❌ Error cargando modelos: {e}")

def main(page: ft.Page):
    # --- 1. Inicializar DB al arrancar ---
    print("Verificando conexión a base de datos...")
    init_db()
    
    # Configuración inicial de la ventana
    page.title = "Sentimetrika - Dashboard"
    page.theme = get_theme()
    page.window_width = 1200
    page.window_height = 800
    
    # Cargar modelos en segundo plano para no congelar la UI de inicio
    threading.Thread(target=load_models, daemon=True).start()

    def route_change(route):
        page.views.clear()
        
        # Rutas
        if page.route == "/login":
            page.views.append(create_login_view(page))
        elif page.route == "/register":
            page.views.append(create_register_view(page))
        elif page.route == "/social_select":
            page.views.append(create_social_select_view(page))
        elif page.route == "/dashboard/facebook":
            page.views.append(create_facebook_view(page))
        elif page.route == "/dashboard/reddit":
            page.views.append(create_reddit_view(page))
        elif page.route == "/dashboard/mastodon":
            page.views.append(create_mastodon_view(page))
        else:
            page.views.append(create_login_view(page))
            
        page.update()

    def view_pop(view):
        page.views.pop()
        top_view = page.views[-1]
        page.go(top_view.route)

    # --- Lógica de Scraper Global (Conectada al botón de actualizar) ---
    def run_all_scrapers(e, translate: bool, page: ft.Page):
        def _bg_task():
            def progress(msg):
                print(f"[Scraper] {msg}")
            
            if not translator_model or not sentiment_model:
                print("⚠️ Espera a que los modelos carguen...")
                return

            # Usar el traductor solo si está habilitado
            translator_to_use = translator_model if translate else None

            # Ejecutar uno por uno
            run_reddit_scrape_opt(progress, translator_to_use, sentiment_model, "Python", 5, 5)
            # TODO: A futuro, pasar el translator_to_use a los otros scrapers
            run_facebook_scrape_opt(progress, translator_to_use, sentiment_model)
            run_mastodon_scrape_opt(progress, translator_to_use, sentiment_model)
            
            page.snack_bar = ft.SnackBar(
                content=ft.Text("🎉 ¡Datos actualizados! Recarga el dashboard para ver los cambios."),
                open=True,
                bgcolor=ft.colors.GREEN_700
            )
            page.update()
            
        threading.Thread(target=_bg_task, daemon=True).start()

    # Guardamos la función en page.data para que social_select.py pueda usarla
    page.data = {"run_all_scrapers_func": lambda e, translate: run_all_scrapers(e, translate, page)}

    page.on_route_change = route_change
    page.on_view_pop = view_pop
    page.go("/login")

ft.app(target=main)