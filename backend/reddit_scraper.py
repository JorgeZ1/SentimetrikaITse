import praw
import os
from pathlib import Path 
from dotenv import load_dotenv
from .database import SessionLocal, Publication, Comment
from typing import List, Dict, Any, Callable, Optional
from sqlalchemy.orm import Session

load_dotenv()

# Configuración de API
CLIENT_ID: str = os.getenv("REDDIT_CLIENT_ID")
CLIENT_SECRET: str = os.getenv("REDDIT_CLIENT_SECRET")
USER_AGENT: str = "python:SentimentApp:v2.0 (by /u/SentimetrikaBot)"

from .sentiment_utils import _mapear_sentimiento

class RedditScraper:
    def __init__(self, progress_callback: Callable[[str], None]):
        self.progress_callback = progress_callback
        self.reddit = self._initialize_reddit()

    def _initialize_reddit(self) -> Optional[praw.Reddit]:
        if not CLIENT_ID or not CLIENT_SECRET:
            self.progress_callback("⚠️ ADVERTENCIA: Faltan credenciales de Reddit en el .env")
            return None
        
        self.progress_callback("Conectando a Reddit...")
        try:
            reddit = praw.Reddit(client_id=CLIENT_ID, client_secret=CLIENT_SECRET, user_agent=USER_AGENT)
            reddit.user.me()
            self.progress_callback("✅ Conexión exitosa a Reddit.")
            return reddit
        except Exception as e:
            self.progress_callback(f"ℹ️ No se pudo iniciar sesión con un usuario. Operando en modo de solo lectura. Error: {e}")
            return None

    def _process_and_save_publications(self, session: Session, posts: List[Any], translator: Optional[Callable]) -> int:
        post_ids = [post.id for post in posts]
        self.progress_callback("Verificando publicaciones existentes en la base de datos...")
        existing_pubs_query = session.query(Publication.id).filter(Publication.id.in_(post_ids))
        existing_pub_ids = {pub_id[0] for pub_id in existing_pubs_query}

        new_pubs_to_add: List[Publication] = []
        titles_to_translate = []
        pub_id_to_title = {}

        for post in posts:
            if post.id not in existing_pub_ids:
                titles_to_translate.append(post.title)
                pub_id_to_title[post.id] = post.title

        translated_titles: Dict[str, str] = {}
        if translator and titles_to_translate:
            self.progress_callback(f"Traduciendo {len(titles_to_translate)} títulos...")
            try:
                results = translator(titles_to_translate, max_length=512, batch_size=16)
                for i, res in enumerate(results):
                    original_title = titles_to_translate[i]
                    translated_titles[original_title] = res['translation_text']
            except Exception as e:
                self.progress_callback(f"❌ Error al traducir títulos en lote: {e}")

        for post_id, original_title in pub_id_to_title.items():
            translated = translated_titles.get(original_title, original_title)
            new_pub = Publication(
                id=str(post_id),
                red_social='Reddit',
                title_original=original_title,
                title_translated=translated
            )
            new_pubs_to_add.append(new_pub)

        if new_pubs_to_add:
            session.bulk_save_objects(new_pubs_to_add)
            self.progress_callback(f"  └ +{len(new_pubs_to_add)} publicaciones nuevas agregadas.")
            return len(new_pubs_to_add)
        return 0

    def _process_and_save_comments(self, session: Session, posts: List[Any], comment_limit: int, translator: Optional[Callable], sentiment_analyzer: Optional[Callable]) -> int:
        all_comments_to_process: List[Dict[str, Any]] = []
        
        self.progress_callback("Descargando comentarios...")
        for post in posts:
            post.comments.replace_more(limit=0)
            comments_batch = post.comments[:comment_limit]
            for comment in comments_batch:
                if hasattr(comment, 'body') and comment.body:
                    all_comments_to_process.append({
                        'publication_id': post.id,
                        'author': str(comment.author) if comment.author else "[deleted]",
                        'text_original': comment.body
                    })

        if not all_comments_to_process:
            self.progress_callback("No se encontraron comentarios para procesar.")
            return 0

        self.progress_callback("Verificando comentarios duplicados...")
        post_ids = [post.id for post in posts]
        existing_comment_tuples = set()
        if post_ids:
            query = session.query(Comment.publication_id, Comment.author, Comment.text_original).filter(Comment.publication_id.in_(post_ids))
            for p_id, author, text in query:
                existing_comment_tuples.add((p_id, author, text))

        unique_comments = [c for c in all_comments_to_process if (c['publication_id'], c['author'], c['text_original']) not in existing_comment_tuples]

        if not unique_comments:
            self.progress_callback("No hay comentarios nuevos para analizar.")
            return 0

        self.progress_callback(f"Procesando {len(unique_comments)} comentarios únicos...")

        texts_to_translate = [c['text_original'][:512] for c in unique_comments]
        translated_texts: Dict[str, str] = {}
        if translator and texts_to_translate:
            self.progress_callback(f"Traduciendo {len(texts_to_translate)} comentarios...")
            try:
                results = translator(texts_to_translate, max_length=512, batch_size=16, truncation=True)
                for i, res in enumerate(results):
                    translated_texts[texts_to_translate[i]] = res['translation_text']
            except Exception as e:
                self.progress_callback(f"❌ Error traduciendo comentarios: {e}")


        # Analizar sentimiento sobre el TEXTO ORIGINAL (inglés) para mejor precisión
        # Pero traducir para mostrar al usuario en español
        texts_for_sentiment = [c['text_original'][:512] for c in unique_comments]
        sentiments = []
        if sentiment_analyzer and texts_for_sentiment:
            self.progress_callback(f"Analizando sentimiento de {len(texts_for_sentiment)} comentarios (en inglés para mayor precisión)...")
            try:
                results = sentiment_analyzer(texts_for_sentiment, batch_size=16, truncation=True)
                sentiments = results
            except Exception as e:
                self.progress_callback(f"❌ Error analizando sentimientos: {e}")

        new_comments_to_add: List[Comment] = []
        for i, comment_data in enumerate(unique_comments):
            sentiment_label = 'neutral'
            sentiment_score = '0.0'
            
            if i < len(sentiments):
                s_res = sentiments[i]
                sentiment_label = _mapear_sentimiento(s_res['label'])
                sentiment_score = str(round(s_res.get('score', 0.0), 4))
            
            text_translated = translated_texts.get(comment_data['text_original'], comment_data['text_original'])
            
            new_comment = Comment(
                publication_id=comment_data['publication_id'],
                author=comment_data['author'],
                text_original=comment_data['text_original'],
                text_translated=text_translated,
                sentiment_label=sentiment_label,
                sentiment_score=sentiment_score
            )
            new_comments_to_add.append(new_comment)

        if new_comments_to_add:
            session.bulk_save_objects(new_comments_to_add)
            self.progress_callback(f"  └ +{len(new_comments_to_add)} comentarios nuevos guardados.")
            return len(new_comments_to_add)
        return 0

    def scrape(self, subreddit_name: str, post_limit: int, comment_limit: int, translator: Optional[Callable], sentiment_analyzer: Optional[Callable]):
        if not self.reddit:
            return

        session = SessionLocal()
        nuevas_publicaciones_totales = 0
        nuevos_comentarios_totales = 0

        try:
            self.progress_callback(f"Descargando {post_limit} publicaciones de r/{subreddit_name}...")
            subreddit = self.reddit.subreddit(subreddit_name)
            posts = list(subreddit.hot(limit=post_limit))
            
            if not posts:
                self.progress_callback("No se encontraron publicaciones.")
                return

            nuevas_publicaciones_totales = self._process_and_save_publications(session, posts, translator)
            nuevos_comentarios_totales = self._process_and_save_comments(session, posts, comment_limit, translator, sentiment_analyzer)

            if nuevas_publicaciones_totales > 0 or nuevos_comentarios_totales > 0:
                self.progress_callback("Guardando todos los cambios en la base de datos...")
                session.commit()
            else:
                self.progress_callback("No se encontraron datos nuevos para guardar.")

        except Exception as e:
            session.rollback()
            self.progress_callback(f"❌ Error durante el scraping: {e}")
        finally:
            session.close()
            self.progress_callback(f"\n--- ✅ Pipeline de Reddit finalizado. Nuevas publicaciones: {nuevas_publicaciones_totales}, Nuevos comentarios: {nuevos_comentarios_totales} ---")

def run_reddit_scrape_opt(
    progress_callback: Callable[[str], None], 
    translator: Optional[Callable], 
    sentiment_analyzer: Optional[Callable], 
    subreddit_name: str, 
    post_limit: int, 
    comment_limit: int
) -> None:
    """
    Versión PostgreSQL optimizada para Reddit con procesamiento por lotes.
    """
    scraper = RedditScraper(progress_callback)
    scraper.scrape(subreddit_name, post_limit, comment_limit, translator, sentiment_analyzer)