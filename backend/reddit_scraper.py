import praw
import os
from pathlib import Path 
from dotenv import load_dotenv
from .database import SessionLocal, Publication, Comment
from typing import List, Dict, Any, Callable, Optional
import threading
from sqlalchemy.orm import Session

load_dotenv()

# Configuración de API
CLIENT_ID: str = os.getenv("REDDIT_CLIENT_ID")
CLIENT_SECRET: str = os.getenv("REDDIT_CLIENT_SECRET")
USER_AGENT: str = "python:SentimentApp:v2.0 (by /u/SentimetrikaBot)"

from .sentiment_utils import _mapear_sentimiento, analizar_sentimiento_con_umbral

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

        # PASO 1: Preparar textos originales
        texts_original = [c['text_original'][:512] for c in unique_comments]
        translations_to_english: Dict[str, str] = {}

        # Si hay un traductor disponible, traducir a inglés ANTES del análisis
        if translator and texts_original:
            self.progress_callback(f"Traduciendo {len(texts_original)} comentarios a inglés para análisis...")
            try:
                # El traductor puede devolver una lista de dicts o directamente strings según implementación
                trans_results = translator(texts_original, max_length=512, batch_size=16)
                translated_texts = []
                for i, tres in enumerate(trans_results):
                    if isinstance(tres, dict) and 'translation_text' in tres:
                        translated_texts.append(tres['translation_text'])
                    elif isinstance(tres, str):
                        translated_texts.append(tres)
                    else:
                        # Fallback: mantener original si la respuesta no es reconocida
                        translated_texts.append(texts_original[i])

                for orig, tr in zip(texts_original, translated_texts):
                    translations_to_english[orig] = tr
            except Exception as e:
                self.progress_callback(f"❌ Error al traducir comentarios: {e}")
                translations_to_english = {t: t for t in texts_original}
        else:
            # No hay traductor: asumimos que el texto ya está en inglés
            translations_to_english = {t: t for t in texts_original}

        # PASO 2: Analizar sentimiento sobre el TEXTO EN INGLÉS (el modelo está entrenado en inglés)
        # Usar la traducción si existe
        texts_for_sentiment = [translations_to_english.get(t, t) for t in texts_original]
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
                raw_label = s_res['label']
                raw_score = s_res.get('score', 0.0)
                
                # Aplicar umbral de confianza para evitar exceso de 'neutral'
                # Umbral reducido para ser menos conservador en Reddit (texto en inglés)
                sentiment_label, used_score = analizar_sentimiento_con_umbral(raw_label, raw_score, umbral_confianza=0.35)
                sentiment_score = str(round(used_score, 4))
            
            # Obtener la traducción a inglés (para análisis)
            english_text = translations_to_english.get(comment_data['text_original'], comment_data['text_original'])
            
            # IMPORTANTE: Guardar siempre el texto original en text_original
            # y la versión en inglés (traducida o ya en inglés) en text_translated
            new_comment = Comment(
                publication_id=comment_data['publication_id'],
                author=comment_data['author'],
                text_original=comment_data['text_original'],  # Texto original (puede ser español/inglés)
                text_translated=english_text,  # Versión en inglés (para referencia)
                sentiment_label=sentiment_label,
                sentiment_score=sentiment_score
            )
            new_comments_to_add.append(new_comment)

        if new_comments_to_add:
            session.bulk_save_objects(new_comments_to_add)
            self.progress_callback(f"  └ +{len(new_comments_to_add)} comentarios nuevos guardados.")
            return len(new_comments_to_add)
        return 0

    def scrape(self, subreddit_name: str, post_limit: int, comment_limit: int, translator: Optional[Callable], sentiment_analyzer: Optional[Callable], stop_event: Optional[threading.Event] = None):
        if not self.reddit:
            return

        session = SessionLocal()
        nuevas_publicaciones_totales = 0
        nuevos_comentarios_totales = 0

        try:
            self.progress_callback(f"Descargando publicaciones de r/{subreddit_name}...")
            subreddit = self.reddit.subreddit(subreddit_name)

            # Buscar MÁS posts de los solicitados (2x) para tener variedad
            # y poder encontrar posts nuevos que no estén en la BD
            total_limit = max(1, int(post_limit))
            search_multiplier = 2
            search_limit = total_limit * search_multiplier
            
            # Distribuir entre 5 categorías para máxima cobertura
            hot_limit = max(1, int(search_limit * 0.3))
            new_limit = max(1, int(search_limit * 0.3))
            rising_limit = max(1, int(search_limit * 0.2))
            top_limit = max(1, int(search_limit * 0.1))
            controversial_limit = max(1, int(search_limit * 0.1))
            
            self.progress_callback(f"  └ Buscando en hot ({hot_limit})...")
            posts_hot = list(subreddit.hot(limit=hot_limit))

            if stop_event is not None and stop_event.is_set():
                self.progress_callback("⏹️ Detención solicitada.")
                session.close()
                return

            self.progress_callback(f"  └ Buscando en new ({new_limit})...")
            posts_new = list(subreddit.new(limit=new_limit))

            if stop_event is not None and stop_event.is_set():
                self.progress_callback("⏹️ Detención solicitada.")
                session.close()
                return

            self.progress_callback(f"  └ Buscando en rising ({rising_limit})...")
            posts_rising = list(subreddit.rising(limit=rising_limit))

            if stop_event is not None and stop_event.is_set():
                self.progress_callback("⏹️ Detención solicitada.")
                session.close()
                return

            self.progress_callback(f"  └ Buscando en top recientes ({top_limit})...")
            posts_top = list(subreddit.top(time_filter='week', limit=top_limit))

            if stop_event is not None and stop_event.is_set():
                self.progress_callback("⏹️ Detención solicitada.")
                session.close()
                return

            self.progress_callback(f"  └ Buscando en controversial ({controversial_limit})...")
            posts_controversial = list(subreddit.controversial(time_filter='week', limit=controversial_limit))

            # Deduplicar por ID
            posts_dict = {}
            for post in posts_hot + posts_new + posts_rising + posts_top + posts_controversial:
                posts_dict[post.id] = post
            
            all_posts = list(posts_dict.values())
            self.progress_callback(f"  └ Total encontrados antes de filtrar: {len(all_posts)}")
            
            # Priorizar posts que NO están en la BD
            existing_post_ids = set()
            if all_posts:
                post_ids_check = [p.id for p in all_posts]
                existing_query = session.query(Publication.id).filter(Publication.id.in_(post_ids_check))
                existing_post_ids = {pid[0] for pid in existing_query}
            
            # Separar posts nuevos y existentes
            new_posts = [p for p in all_posts if p.id not in existing_post_ids]
            existing_posts = [p for p in all_posts if p.id in existing_post_ids]
            
            # Priorizar nuevos, luego agregar existentes si hacen falta
            posts = (new_posts + existing_posts)[:total_limit]

            self.progress_callback(f"✅ Total de publicaciones únicas encontradas: {len(posts)}")

            if not posts:
                self.progress_callback("No se encontraron publicaciones.")
                return

            # Primero: Procesar y guardar todas las publicaciones nuevas
            added_pubs = self._process_and_save_publications(session, posts, translator)
            nuevas_publicaciones_totales += added_pubs
            if added_pubs > 0:
                session.commit()
                self.progress_callback(f"  └ {added_pubs} publicaciones nuevas guardadas.")
            
            # Segundo: Procesar comentarios de TODOS los posts (nuevos y existentes)
            # para permitir agregar comentarios nuevos a posts que ya existían
            if stop_event is not None and stop_event.is_set():
                self.progress_callback("⏹️ Detención solicitada.")
                session.close()
                return
            
            # Procesar comentarios por lotes para permitir commits parciales
            batch_size = max(1, min(10, len(posts)))
            for i in range(0, len(posts), batch_size):
                batch = posts[i:i+batch_size]
                if stop_event is not None and stop_event.is_set():
                    self.progress_callback("⏹️ Detención solicitada. Guardando progreso parcial...")
                    session.commit()
                    break

                added_comments = self._process_and_save_comments(session, batch, comment_limit, translator, sentiment_analyzer)
                nuevos_comentarios_totales += added_comments
                # Commit incremental
                if added_comments > 0:
                    session.commit()

            if nuevas_publicaciones_totales == 0 and nuevos_comentarios_totales == 0:
                self.progress_callback("ℹ️ No se encontraron datos nuevos (ya tienes estos posts/comentarios en la BD).")

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
    comment_limit: int,
    stop_event: Optional[threading.Event] = None
) -> None:
    """
    Versión PostgreSQL optimizada para Reddit con procesamiento por lotes.
    """
    scraper = RedditScraper(progress_callback)
    scraper.scrape(subreddit_name, post_limit, comment_limit, translator, sentiment_analyzer, stop_event=stop_event)