# Librerías Utilizadas en SentimetrikaITse

## Resumen Ejecutivo

**Sentimetrika** es una aplicación de análisis de sentimientos multilingüe para redes sociales. Utiliza **14 librerías principales** organizadas en cuatro capas: **UI/Frontend**, **Procesamiento de IA/NLP**, **Scraping de Redes Sociales**, y **Persistencia de Datos**.

---

## 1. FRONTEND (Interfaz de Usuario)

### **flet** (v1.x)
- **Propósito:** Framework de UI para aplicaciones de escritorio/web en Python
- **Justificación:** 
  - Permite crear una interfaz Material Design moderna con mínimo código
  - Multiplataforma (Windows, macOS, Linux) desde un único código base
  - Componentes integrados (TextField, Button, Container, Navigation, etc.)
  - Soporte para threading sin bloquear UI
- **Uso en SentimetrikaITse:**
  - `main.py`: Inicializa la aplicación y gestiona rutas/vistas
  - `frontend/views/*.py`: Define dashboards para cada red social (Reddit, Facebook, Mastodon)
  - Componentes: AppBar, Drawer, ProgressBar, Cards, Dialogs, SnackBar, etc.

---

## 2. PROCESAMIENTO DE IA / NLP (Inteligencia Artificial)

### **transformers**
- **Propósito:** Biblioteca oficial de HuggingFace para modelos de IA preentrenados
- **Justificación:**
  - Acceso a modelos SOTA (State-of-the-Art) sin entrenarlos desde cero
  - Pipeline simplificado para tareas comunes (traducción, clasificación de texto)
  - Soporte para múltiples idiomas y modelos comunitarios
- **Modelos usados:**
  - **Helsinki-NLP/opus-mt-es-en:** Traducción español → inglés
  - **cardiffnlp/twitter-roberta-base-sentiment-latest:** Análisis de sentimientos (0/1/2 = neg/neu/pos)
- **Uso en SentimetrikaITse:**
  - `main.py`: Carga modelos en thread daemon al iniciar
  - `backend/reddit_scraper.py`: Traduce comentarios y analiza sentimiento
  - `backend/facebook_scraper.py`, `backend/mastodon_scraper.py`: Igual

### **torch** (PyTorch)
- **Propósito:** Backend computacional para modelos de deep learning
- **Justificación:**
  - Dependencia de `transformers` (requerida)
  - Optimización de inferencia en CPU/GPU
  - Operaciones tensor eficientes
- **Uso:** Subyacente en la ejecución de los modelos de transformers

### **sentencepiece**
- **Propósito:** Tokenizador de subpalabras (BPE/SentencePiece)
- **Justificación:**
  - Dependencia de modelos multilingües (Helsinki-NLP/opus-mt)
  - Convierte texto en tokens numéricos para modelos de IA
- **Uso:** Preprocesamiento de texto antes de pasarlo a transformers

### **sacremoses**
- **Propósito:** Herramientas de normalización de texto multilingüe
- **Justificación:**
  - Dependencia de algunos modelos de traducción
  - Normaliza puntuación, espacios y caracteres especiales
- **Uso:** Preprocesamiento de texto para traducción en múltiples idiomas

---

## 3. SCRAPING DE REDES SOCIALES

### **praw** (Python Reddit API Wrapper)
- **Propósito:** Cliente oficial para interactuar con la API de Reddit
- **Justificación:**
  - Abstrae la complejidad de OAuth2 y REST de Reddit
  - Métodos simples para obtener subreddits, posts, comentarios
  - Paginación automática y throttling respetando límites de Reddit
- **Uso en SentimetrikaITse:**
  - `backend/reddit_scraper.py`: 
    - Inicializa conexión con `REDDIT_CLIENT_ID` y `REDDIT_CLIENT_SECRET`
    - Obtiene posts de hot/new/top y sus comentarios
    - Deduplica y almacena en base de datos

### **Mastodon.py**
- **Propósito:** Cliente para redes federadas tipo Mastodon
- **Justificación:**
  - Acceso a API Mastodon.social y otras instancias
  - Abstracción de autenticación OAuth2
  - Manejo de posts, respuestas, búsquedas
- **Uso en SentimetrikaITse:**
  - `backend/mastodon_scraper.py`: Obtiene toots (posts) por ID y analiza sentimiento

### **facebook-sdk**
- **Propósito:** SDK oficial de Facebook para Graph API v3.x
- **Justificación:**
  - Acceso autenticado a páginas de Facebook y sus posts/comentarios
  - Manejo de permisos y tokens de acceso
- **Uso en SentimetrikaITse:**
  - `backend/facebook_scraper.py`: Obtiene posts de una página y sus comentarios

### **discord.py** (Mencionado pero sin uso actual)
- **Propósito:** Cliente para bots de Discord
- **Justificación:** Potencial expansión futura a análisis de Discord
- **Uso:** Actualmente instalado pero no integrado

---

## 4. PERSISTENCIA DE DATOS

### **sqlalchemy**
- **Propósito:** ORM (Object-Relational Mapping) agnóstico de base de datos
- **Justificación:**
  - Define modelos (Publication, Comment, User) sin escribir SQL crudo
  - Soporta SQLite (desarrollo) y PostgreSQL (producción)
  - Manejo de relaciones, cascadas y transacciones
- **Uso en SentimetrikaITse:**
  - `backend/database.py`:
    - Modelo `Publication`: id, red_social, title_original, title_translated
    - Modelo `Comment`: publication_id, author, text_original, text_translated, sentiment_label, sentiment_score
    - Modelo `User`: email, hashed_password (para autenticación futura)
  - Cascadas: Al eliminar una publicación, se borran todos sus comentarios automáticamente

### **psycopg2-binary**
- **Propósito:** Adaptador PostgreSQL nativo para Python
- **Justificación:**
  - Soporte para PostgreSQL en producción (BD más robusta que SQLite)
  - Conexiones pooled y manejo eficiente de transacciones
- **Uso en SentimetrikaITse:**
  - `.env`: `DB_TYPE=postgresql` activa esta conexión
  - En desarrollo se usa SQLite (más ligero), en producción PostgreSQL (más escalable)

---

## 5. CONFIGURACIÓN Y UTILIDADES

### **python-dotenv**
- **Propósito:** Carga variables de entorno desde archivo `.env`
- **Justificación:**
  - Mantiene credenciales (API keys, DB passwords) fuera del código fuente
  - Diferencia entre desarrollo/producción sin cambiar código
- **Uso en SentimetrikaITse:**
  - `.env`: Almacena `REDDIT_CLIENT_ID`, `REDDIT_CLIENT_SECRET`, `POSTGRES_*`, etc.
  - `backend/database.py`: Lee `DB_TYPE` para elegir SQLite o PostgreSQL
  - `backend/reddit_scraper.py`: Lee credenciales de Reddit

### **tqdm**
- **Propósito:** Barras de progreso elegantes en terminal
- **Justificación:**
  - Mejora UX mostrando porcentaje/ETA en operaciones largas (traducción en batch, scraping)
- **Uso en SentimetrikaITse:**
  - Posible uso en `backend/model_profiler.py` (profiling de performance)
  - Logs visuales de progreso en scraping

---

## 6. GENERACIÓN DE REPORTES

### **fpdf2**
- **Propósito:** Generador de PDF desde Python
- **Justificación:**
  - Crea reportes PDF exportables con datos de publicaciones/comentarios
  - Tablas, estilos y múltiples páginas
  - API simplificada vs. reportlab
- **Uso en SentimetrikaITse:**
  - `backend/report_generator.py`: 
    - Genera PDF con título, tabla de estadísticas, y listado de publicaciones+sentimiento
    - Usado en dashboards (botón "Generar PDF")

---

## Diagrama de Capas

```
┌─────────────────────────────────────────────────────┐
│             FRONTEND (Flet)                          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐ │
│  │ Dashboard   │  │ Comments    │  │ Social      │ │
│  │ Reddit      │  │ View        │  │ Select      │ │
│  │ Facebook    │  │             │  │ Login       │ │
│  │ Mastodon    │  │             │  │ Register    │ │
│  └─────────────┘  └─────────────┘  └─────────────┘ │
└─────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────┐
│              SCRAPERS & IA                           │
│  ┌───────────────┐  ┌────────────────────────────┐ │
│  │ Reddit        │  │ NLP Pipeline:              │ │
│  │ (praw)        │  │ ├─ Traducción (transformers)  │
│  │ Facebook      │  │ └─ Sentimiento (transformers) │
│  │ (facebook-sdk)│  │                            │ │
│  │ Mastodon      │  └────────────────────────────┘ │
│  │ (Mastodon.py) │                                 │
│  └───────────────┘                                 │
└─────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────┐
│            PERSISTENCE (SQLAlchemy)                 │
│  ┌───────────────────────────────────────────────┐ │
│  │  SQLite (dev) / PostgreSQL (prod)             │ │
│  │  ├─ publications                              │ │
│  │  ├─ comments                                  │ │
│  │  └─ users                                     │ │
│  └───────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────┘
```

---

## Requisitos y Versiones

Ver `requirements.txt` para versiones exactas. Instalación:

```bash
pip install -r requirements.txt
```

---

## Justificación Arquitectónica

**¿Por qué esta combinación de librerías?**

1. **Flet (Frontend):** Desarrollo rápido de UI multiplataforma sin JavaScript/HTML
2. **Transformers (IA):** Modelos comunitarios de alta calidad sin entrenar manualmente
3. **PRAW/Mastodon.py/facebook-sdk:** Acceso nativo a APIs de redes sociales (sin web scraping frágil)
4. **SQLAlchemy (BD):** Flexibilidad para cambiar de SQLite (dev) a PostgreSQL (prod)
5. **python-dotenv (Config):** Seguridad de credenciales y facilidad de deployment

**Alternativas consideradas (y por qué no):**
- **Selenium/Playwright** vs. **PRAW/Mastodon.py:** APIs oficiales son más estables y rápidas
- **FastAPI** vs. **Flet:** GUI de escritorio es más accesible para usuarios no-técnicos
- **Django ORM** vs. **SQLAlchemy:** SQLAlchemy es más ligero y flexible
- **spaCy** vs. **Transformers:** transformers tiene modelos multilingües preentrenados

---

## Performance Consideraciones

- **Modelos grandes:** Traducción + Sentimiento = ~2GB VRAM. Se cargan una sola vez en startup
- **Batch processing:** Traducción/análisis en lotes (batch_size=16) para aprovechar GPU/CPU
- **Scraping:** Deduplicación en BD para evitar duplicados; commits parciales en lotes
- **Threading:** Carga de modelos en daemon thread para no bloquear UI

---

**Última actualización:** 11 de Diciembre, 2025
