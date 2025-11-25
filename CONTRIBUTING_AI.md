# Guía para Colaborar con IA

Este documento proporciona una guía para que otra IA pueda entender y modificar el proyecto Sentimetrika.

## Resumen del Proyecto

Sentimetrika es una aplicación de escritorio construida con Flet que permite analizar el sentimiento de publicaciones en redes sociales. La aplicación utiliza modelos de Hugging Face Transformers para el análisis de sentimientos y la traducción, y almacena los datos en una base de datos PostgreSQL.

## Estructura del Proyecto

El proyecto está organizado en las siguientes carpetas:

-   `backend/`: Contiene toda la lógica de negocio, incluyendo:
    -   `database.py`: Define el esquema de la base de datos y gestiona la conexión.
    -   `scrapers/`: Contiene los scrapers para cada red social (Reddit, Facebook, Mastodon).
    -   `report_generator.py`: Genera los informes en PDF.
    -   `sentiment_utils.py`: Funciones de utilidad para el análisis de sentimientos.
-   `frontend/`: Contiene toda la interfaz de usuario, construida con Flet.
    -   `views/`: Define las diferentes vistas (pantallas) de la aplicación.
    -   `assets/`: Contiene los recursos estáticos como imágenes y fuentes.
-   `tests/`: Contiene las pruebas unitarias y de integración.
-   `reports/`: Carpeta donde se guardan los informes generados.
-   `storage/`: Almacenamiento de datos temporales o persistentes.

## Cómo Añadir un Nuevo Scraper

Para añadir un scraper para una nueva red social, sigue estos pasos:

1.  **Crea un nuevo archivo de scraper** en la carpeta `backend/` (ej. `twitter_scraper.py`).
2.  **Crea una clase `TwitterScraper`** que siga la misma estructura que las clases existentes (`RedditScraper`, `FacebookScraper`, `MastodonScraper`).
3.  **Implementa el método `scrape`** en tu nueva clase. Este método debe:
    -   Conectarse a la API de la red social.
    -   Obtener las publicaciones y comentarios.
    -   Procesar los datos (traducción, análisis de sentimientos).
    -   Guardar los datos en la base de datos utilizando los modelos de `database.py`.
4.  **Crea una nueva función `run_twitter_scrape`** que instancie y llame a tu nueva clase `TwitterScraper`.
5.  **Añade una nueva vista de dashboard** en `frontend/views/` (ej. `dashboard_twitter.py`) para visualizar los datos del nuevo scraper.
6.  **Añade la nueva ruta** en la función `route_change` de `main.py`.

## Cómo Modificar la Interfaz de Usuario

La interfaz de usuario está construida con Flet. Para modificarla:

-   **Modifica las vistas existentes** en la carpeta `frontend/views/`. Cada archivo `.py` en esta carpeta corresponde a una pantalla de la aplicación.
-   **Utiliza los componentes de Flet** para construir la interfaz. Puedes encontrar la documentación de Flet en [https://flet.dev/docs/](https://flet.dev/docs/).
-   **Modifica el tema de la aplicación** en `frontend/theme.py`.

## Ejecutar la Aplicación

Para ejecutar la aplicación, sigue estos pasos:

1.  **Configura el entorno virtual:**
    ```bash
    python -m venv .venv
    source .venv/bin/activate  # En Windows: .venv\Scripts\activate
    ```
2.  **Instala las dependencias:**
    ```bash
    pip install -r requirements.txt
    ```
3.  **Configura las credenciales:**
    -   Crea un archivo `.env` en la raíz del proyecto.
    -   Añade las credenciales para las APIs de las redes sociales (Reddit, Facebook, Mastodon) y la base de datos PostgreSQL.
4.  **Ejecuta la aplicación:**
    ```bash
    python main.py
    ```
