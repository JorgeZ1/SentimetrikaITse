import flet as ft
import threading
from transformers import pipeline
from typing import Optional, Callable

# --- VISTAS (Tus pantallas) ---
from mi_dashboard.views.login import create_login_view
from mi_dashboard.views.register import create_register_view
from mi_dashboard.views.social_select import create_social_select_view
from mi_dashboard.views.dashboard_facebook import create_dashboard_view as create_facebook_view
from mi_dashboard.views.dashboard_reddit import create_dashboard_view as create_reddit_view
from mi_dashboard.views.dashboard_mastodon import create_dashboard_view as create_mastodon_view
from mi_dashboard.theme import get_theme

# --- BASE DE DATOS ---
from Api.database import init_db

# --- SCRAPERS ---
from Api.reddit_scraper_opt import run_reddit_scrape_opt 
from Api.facebook_scraper_opt import run_facebook_scrape_opt
from Api.mastodon_scraper_opt import run_mastodon_scrape_opt

# --- VARIABLES GLOBALES DE IA ---
translator_model: Optional[Callable] = None
sentiment_model: Optional[Callable] = None

def load_models() -> None:
    """Carga los modelos pesados en segundo plano al iniciar"""
    global translator_model, sentiment_model
    print("⏳ Cargando modelos de IA (esto puede tardar un poco)...")
    try:
        # Modelo de traducción (Inglés a Español)
        translator_model = pipeline("translation", model="Helsinki-NLP/opus-mt-es-en")
        # Modelo de sentimientos (Twitter-Roberta)
        sentiment_model = pipeline("text-classification", model="cardiffnlp/twitter-roberta-base-sentiment-latest")
        print("✅ Modelos de IA cargados y listos.")
    except Exception as e:
        print(f"❌ Error cargando modelos: {e}")

def main(page: ft.Page) -> None:
    # 1. Inicializar Base de Datos
    print("🔌 Verificando conexión a base de datos...")
    init_db()
    
    # 2. Configuración de la Ventana
    page.title = "Sentimetrika - Dashboard"
    page.theme = get_theme()
    page.window_width = 1200
    page.window_height = 800
    
    # 3. Iniciar carga de IA en hilo separado (Daemon)
    threading.Thread(target=load_models, daemon=True).start()

    # --- FUNCIÓN GLOBAL DE ACTUALIZACIÓN (Para el botón del menú) ---
    def run_all_scrapers(e: ft.ControlEvent, translate: bool, page: ft.Page) -> None:
        def _bg_task() -> None:
            def progress(msg: str) -> None:
                print(f"[Scraper] {msg}")
            
            if not translator_model or not sentiment_model:
                print("⚠️ Espera a que los modelos carguen...")
                return

            translator_to_use: Optional[Callable] = translator_model if translate else None
            
            print("🚀 --- INICIANDO ACTUALIZACIÓN MASIVA ---")

            try:
                print("--- Ejecutando Reddit ---")
                run_reddit_scrape_opt(progress, translator_to_use, sentiment_model, "Python", 5, 5)
            except Exception as e:
                print(f"Error en Reddit: {e}")

            try:
                print("--- Ejecutando Facebook ---")
                run_facebook_scrape_opt(progress, translator_to_use, sentiment_model)
            except Exception as e:
                print(f"Error en Facebook: {e}")

            try:
                print("--- Ejecutando Mastodon ---")
                run_mastodon_scrape_opt(progress, translator_to_use, sentiment_model)
            except Exception as e:
                print(f"Error en Mastodon: {e}")
            
            page.snack_bar = ft.SnackBar(
                content=ft.Text("🎉 ¡Datos actualizados! Recarga el dashboard para ver los cambios."),
                open=True,
                bgcolor=ft.Colors.GREEN_700
            )
            page.update()
            
        threading.Thread(target=_bg_task, daemon=True).start()

    # 4. COMPARTIR DATOS CON LAS VISTAS (page.data)
    page.data = {"run_all_scrapers_func": lambda e, translate=True: run_all_scrapers(e, translate, page)}

    # --- SISTEMA DE NAVEGACIÓN ---
    def route_change(route: str) -> None:
        page.views.clear()
        
        page.data["translator"] = translator_model
        page.data["sentiment"] = sentiment_model
        
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

    def view_pop(view: ft.View) -> None:
        page.views.pop()
        top_view = page.views[-1]
        page.go(top_view.route)

    page.on_route_change = route_change
    page.on_view_pop = view_pop
    
    page.go("/login")

ft.app(target=main)