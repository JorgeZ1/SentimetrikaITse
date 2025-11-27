import facebook
import os
from dotenv import load_dotenv
from .database import SessionLocal, Publication, Comment
from typing import List, Dict, Any, Callable, Optional
from sqlalchemy.orm import Session
from .sentiment_utils import _mapear_sentimiento

# Cargar .env al inicio por si acaso
load_dotenv()

class FacebookScraper:
    # 1. MODIFICADO: Aceptamos credenciales directas en el constructor
    def __init__(self, progress_callback: Callable[[str], None], page_id: str = None, token: str = None):
        self.progress_callback = progress_callback
        self.graph = None
        # Guardamos las credenciales manuales (vienen del dashboard)
        self.manual_page_id = page_id
        self.manual_token = token
        
        self.page_id = None 
        # No inicializamos aquí para hacerlo en scrape()

    def _initialize_graph_api(self) -> bool:
        """Inicializa la conexión usando credenciales manuales (prioridad) o de entorno"""
        
        # 1. Prioridad: Credenciales pasadas manualmente desde el Dashboard
        raw_token = self.manual_token
        raw_page_id = self.manual_page_id

        # 2. Respaldo: Si no se pasaron manuales, intentar leer .env
        if not raw_token or not raw_page_id:
            load_dotenv(override=True) # Forzar recarga de archivo
            raw_token = os.environ.get("PAGE_ACCESS_TOKEN") or os.getenv("PAGE_ACCESS_TOKEN")
            raw_page_id = os.environ.get("PAGE_ID") or os.getenv("PAGE_ID")

        if not raw_token or not raw_page_id:
            self.progress_callback("❌ Error: No hay credenciales disponibles (ni manuales ni en .env).")
            return False

        # 3. LIMPIEZA AGRESIVA (Sanitization)
        # Eliminamos espacios, saltos de línea y comillas que causan errores
        token = str(raw_token).strip().replace('"', '').replace("'", "")
        self.page_id = str(raw_page_id).strip().replace('"', '').replace("'", "")

        # Debug crítico para confirmar qué se está usando
        preview = token[:10] + "..." if len(token) > 10 else "N/A"
        self.progress_callback(f"⚙️ Conectando -> ID Objetivo: {self.page_id} | Token: {preview}")
        
        try:
            # 4. Conexión
            self.graph = facebook.GraphAPI(access_token=token, version="3.1")
            
            # Prueba de fuego: Consultar la propia página
            page_obj = self.graph.get_object(id=self.page_id, fields='name,id')
            self.progress_callback(f"✅ ¡CONEXIÓN EXITOSA! Página: {page_obj.get('name')} ({page_obj.get('id')})")
            return True
            
        except facebook.GraphAPIError as e:
            msg = str(e)
            if '190' in msg:
                self.progress_callback(f"❌ Error 190: El token es inválido o expiró para la página {self.page_id}.")
            elif '10' in msg:
                self.progress_callback(f"❌ Error 10: Permisos insuficientes. Verifica que el ID {self.page_id} sea correcto.")
            else:
                self.progress_callback(f"❌ Error API Graph: {msg}")
            return False
        except Exception as e:
            self.progress_callback(f"❌ Error general de conexión: {e}")
            return False

    def _process_and_save_publications(self, session: Session, posts_data: List[Dict[str, Any]]) -> int:
        if not posts_data: return 0
        
        post_ids = [post['id'] for post in posts_data]
        existing_pubs = {p[0] for p in session.query(Publication.id).filter(Publication.id.in_(post_ids)).all()}

        new_pubs = []
        for post in posts_data:
            if post['id'] not in existing_pubs:
                msg = post.get('message', '')
                new_pubs.append(Publication(
                    id=post['id'],
                    red_social="Facebook",
                    title_original=msg,
                    title_translated=msg
                ))

        if new_pubs:
            session.bulk_save_objects(new_pubs)
            self.progress_callback(f"  └ +{len(new_pubs)} pubs nuevas.")
            return len(new_pubs)
        return 0

    def _process_and_save_comments(self, session: Session, post_ids: List[str], translator, sentiment) -> int:
        if not post_ids: return 0
        
        self.progress_callback("Buscando comentarios nuevos...")
        all_comments = []
        
        for pid in post_ids:
            try:
                # filter='stream' trae todo (incluso ocultos)
                comments = self.graph.get_connections(id=pid, connection_name='comments', limit=50, filter='stream').get('data', [])
                for c in comments:
                    if 'message' in c:
                        all_comments.append({
                            'publication_id': pid,
                            'author': c.get('from', {}).get('name', 'Anónimo'),
                            'text': c['message']
                        })
            except:
                continue

        if not all_comments: return 0

        # Deduplicación simple
        existing_query = session.query(Comment.publication_id, Comment.text_original).filter(Comment.publication_id.in_(post_ids)).all()
        existing_set = {(pid, txt) for pid, txt in existing_query}
        
        unique_comments = [c for c in all_comments if (c['publication_id'], c['text']) not in existing_set]
        
        if not unique_comments: return 0
        
        self.progress_callback(f"Procesando {len(unique_comments)} comentarios...")
        
        texts = [c['text'] for c in unique_comments]
        translations = {}
        sentiments = []
        
        if translator:
            try:
                res = translator(texts, max_length=512, truncation=True, batch_size=8)
                translations = {t: r['translation_text'] for t, r in zip(texts, res)}
            except Exception as e:
                print(f"Warn Traducción: {e}")

        # Analizar sentimiento sobre TEXTO TRADUCIDO (español) para Facebook
        if sentiment:
            texts_for_sent = [translations.get(t, t) for t in texts]
            try:
                sentiments = sentiment(texts_for_sent, truncation=True, batch_size=8)
            except Exception as e:
                print(f"Warn Sentimiento: {e}")

        to_save = []
        for i, c in enumerate(unique_comments):
            orig = c['text']
            trans = translations.get(orig, orig)
            
            s_label = 'neutral'
            s_score = '0.0'
            if i < len(sentiments):
                s_label = _mapear_sentimiento(sentiments[i]['label'])
                s_score = str(round(sentiments[i]['score'], 4))
            
            to_save.append(Comment(
                publication_id=c['publication_id'],
                author=c['author'],
                text_original=orig,
                text_translated=trans,
                sentiment_label=s_label,
                sentiment_score=s_score
            ))
            
        if to_save:
            session.bulk_save_objects(to_save)
            return len(to_save)
        return 0

    def scrape(self, translator, sentiment):
        # PASO CRÍTICO: Iniciar con las credenciales (manuales o env)
        if not self._initialize_graph_api():
            return

        session = SessionLocal()
        try:
            self.progress_callback("Descargando feed...")
            # Usamos self.page_id validado
            posts = self.graph.get_connections(id=self.page_id, connection_name='feed', limit=20).get('data', [])
            
            if not posts:
                self.progress_callback("⚠️ Feed vacío o sin acceso.")
                return

            n_pubs = self._process_and_save_publications(session, posts)
            
            post_ids = [p['id'] for p in posts]
            n_comms = self._process_and_save_comments(session, post_ids, translator, sentiment)
            
            if n_pubs > 0 or n_comms > 0:
                session.commit()
                self.progress_callback("✅ Guardado en BD con éxito.")
            else:
                self.progress_callback("Todo al día.")
                
        except Exception as e:
            session.rollback()
            self.progress_callback(f"❌ Error Scraper: {e}")
        finally:
            session.close()

# 2. MODIFICADO: Aceptamos page_id y token como argumentos opcionales
def run_facebook_scrape_opt(
    progress_callback: Callable[[str], None], 
    translator: Optional[Callable], 
    sentiment_analyzer: Optional[Callable],
    page_id: str = None,  # Nuevo argumento
    token: str = None     # Nuevo argumento
) -> None:
    """
    Punto de entrada optimizado que permite inyección de credenciales.
    """
    # Pasamos los argumentos al constructor
    scraper = FacebookScraper(progress_callback, page_id=page_id, token=token)
    scraper.scrape(translator, sentiment_analyzer)