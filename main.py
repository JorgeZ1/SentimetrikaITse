import flet as ft
import threading
from transformers import pipeline

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

# --- SCRAPERS (Importamos el de Reddit corregido y los otros con seguridad) ---
from Api.reddit_scraper_opt import run_reddit_scraper 

# Usamos try/except por si faltan archivos, para que no se rompa todo
try:
    from Api.facebook_scraper_opt import run_facebook_scrape_opt
except ImportError:
    run_facebook_scrape_opt = None
    print("⚠️ Aviso: No se encontró facebook_scraper_opt.py")

try:
    from Api.mastodon_scraper_opt import run_mastodon_scrape_opt
except ImportError:
    run_mastodon_scrape_opt = None
    print("⚠️ Aviso: No se encontró mastodon_scraper_opt.py")


# --- VARIABLES GLOBALES DE IA ---
translator_model = None
sentiment_model = None

def load_models():
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

def main(page: ft.Page):
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
    def run_all_scrapers(e):
        def _bg_task():
            def progress(msg):
                print(f"[System] {msg}")
            
            # Validar si la IA ya cargó
            if not translator_model or not sentiment_model:
                print("⚠️ Los modelos aún están cargando. Intenta en unos segundos...")
                # Opcional: return si quieres ser estricto
            
            print("🚀 --- INICIANDO ACTUALIZACIÓN MASIVA ---")

            # A. REDDIT (Usando el nuevo scraper con búsqueda)
            try:
                print("--- Ejecutando Reddit ---")
                run_reddit_scraper(
                    progress_callback=progress, 
                    search_query="Tecnología", # Tema por defecto para el botón global
                    translator=translator_model,
                    sentiment_analyzer=sentiment_model,
                    limit=5
                ) 
            except Exception as e:
                print(f"Error en Reddit: {e}")

            # B. FACEBOOK
            if run_facebook_scrape_opt:
                try:
                    print("--- Ejecutando Facebook ---")
                    run_facebook_scrape_opt(progress, translator_model, sentiment_model)
                except Exception as e:
                    print(f"Error en Facebook: {e}")

            # C. MASTODON
            if run_mastodon_scrape_opt:
                try:
                    print("--- Ejecutando Mastodon ---")
                    run_mastodon_scrape_opt(progress, translator_model, sentiment_model)
                except Exception as e:
                    print(f"Error en Mastodon: {e}")
            
            print("✨ Todo actualizado. Puedes recargar las vistas.")
            
        # Correr en hilo separado para no congelar la interfaz
        threading.Thread(target=_bg_task, daemon=True).start()

    # 4. COMPARTIR DATOS CON LAS VISTAS (page.data)
    # Esto es crucial: Aquí guardamos los modelos y la función para que Reddit/Facebook los usen
    page.data = {
        "run_all_scrapers_func": run_all_scrapers,
        "translator": None, 
        "sentiment": None
    }

    # --- SISTEMA DE NAVEGACIÓN ---
    def route_change(route):
        page.views.clear()
        
        # Actualizamos los modelos en page.data por si ya terminaron de cargar
        page.data["translator"] = translator_model
        page.data["sentiment"] = sentiment_model
        
        # Selector de Vistas
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
    def run_all_scrapers(e):
        def _bg_task():
            def progress(msg):
                print(f"[Scraper] {msg}")
            
            if not translator_model or not sentiment_model:
                print("⚠️ Espera a que los modelos carguen...")
                return

            # Ejecutar uno por uno
            run_reddit_scrape_opt(progress, translator_model, sentiment_model, "Python", 5, 5)
            run_facebook_scrape_opt(progress, translator_model, sentiment_model)
            run_mastodon_scrape_opt(progress, translator_model, sentiment_model)
            
            print("🎉 Todo actualizado. Recarga la vista.")
            
        threading.Thread(target=_bg_task, daemon=True).start()

    # Guardamos la función en page.data para que social_select.py pueda usarla
    page.data = {"run_all_scrapers_func": run_all_scrapers}

    page.on_route_change = route_change
    page.on_view_pop = view_pop
    
    # Iniciar en Login
    page.go("/login")

ft.app(target=main)