import facebook
import os
from dotenv import load_dotenv
from .database import SessionLocal, Publication, Comment
from typing import List, Dict, Any, Callable, Optional
from sqlalchemy.orm import Session
from .sentiment_utils import _mapear_sentimiento

load_dotenv()

class FacebookScraper:
    def __init__(self, progress_callback: Callable[[str], None]):
        self.progress_callback = progress_callback
        self.graph = self._initialize_graph_api()

    def _initialize_graph_api(self) -> Optional[facebook.GraphAPI]:
        PAGE_ACCESS_TOKEN: str = os.getenv("PAGE_ACCESS_TOKEN")
        PAGE_ID: str = os.getenv("PAGE_ID")

        if not PAGE_ACCESS_TOKEN or not PAGE_ID:
            self.progress_callback("❌ Error: Faltan credenciales (PAGE_ACCESS_TOKEN o PAGE_ID) en .env")
            return None

        self.progress_callback("Iniciando conexión con la API Graph de Facebook...")
        try:
            graph = facebook.GraphAPI(access_token=PAGE_ACCESS_TOKEN)
            page_info = graph.get_object(id=PAGE_ID, fields='name')
            self.progress_callback(f"✅ Conectado a página: {page_info.get('name', 'Desconocida')}")
            return graph
        except Exception as e:
            self.progress_callback(f"❌ Error de conexión: {e}")
            return None

    def _process_and_save_publications(self, session: Session, posts_data: List[Dict[str, Any]]) -> int:
        post_ids = [post['id'] for post in posts_data]
        existing_pubs_query = session.query(Publication.id).filter(Publication.id.in_(post_ids))
        existing_pub_ids = {pub_id[0] for pub_id in existing_pubs_query}

        new_pubs_to_add: List[Publication] = [
            Publication(
                id=post['id'],
                red_social="Facebook",
                title_original=post.get('message', 'Publicación multimedia/sin texto'),
                title_translated=post.get('message', 'Publicación multimedia/sin texto')
            )
            for post in posts_data if post['id'] not in existing_pub_ids
        ]

        if new_pubs_to_add:
            session.bulk_save_objects(new_pubs_to_add)
            self.progress_callback(f"  └ +{len(new_pubs_to_add)} publicaciones nuevas agregadas.")
            return len(new_pubs_to_add)
        return 0

    def _process_and_save_comments(self, session: Session, post_ids: List[str], translator: Optional[Callable], sentiment_analyzer: Optional[Callable]) -> int:
        all_comments_to_process: List[Dict[str, Any]] = []
        self.progress_callback("Descargando comentarios de todas las publicaciones...")
        for post_id in post_ids:
            comments_data = self.graph.get_connections(id=post_id, connection_name='comments', fields='id,message,from').get('data', [])
            for comment in comments_data:
                if comment.get('message'):
                    all_comments_to_process.append({
                        'publication_id': post_id,
                        'author': comment.get('from', {}).get('name', 'Anónimo'),
                        'text_original': comment['message']
                    })

        if not all_comments_to_process:
            self.progress_callback("No se encontraron comentarios para procesar.")
            return 0
            
        self.progress_callback("Verificando comentarios duplicados...")
        query = session.query(Comment.publication_id, Comment.author, Comment.text_original).filter(Comment.publication_id.in_(post_ids))
        existing_comment_tuples = {(p_id, author, text) for p_id, author, text in query}
        
        unique_comments: List[Dict[str, Any]] = [c for c in all_comments_to_process if (c['publication_id'], c['author'], c['text_original']) not in existing_comment_tuples]

        if not unique_comments:
            self.progress_callback("No hay comentarios nuevos para analizar.")
            return 0

        self.progress_callback(f"Procesando {len(unique_comments)} comentarios únicos...")
        
        texts_to_translate = [c['text_original'] for c in unique_comments]
        translated_texts: Dict[str, str] = {}
        if translator and texts_to_translate:
            try:
                results = translator(texts_to_translate, max_length=512, batch_size=16)
                for i, res in enumerate(results):
                    translated_texts[texts_to_translate[i]] = res['translation_text']
            except Exception as e:
                self.progress_callback(f"❌ Error traduciendo comentarios: {e}")

        texts_for_sentiment = [translated_texts.get(c['text_original'], c['text_original']) for c in unique_comments]
        sentiments: List[Dict[str, Any]] = []
        if sentiment_analyzer and texts_for_sentiment:
            try:
                sentiments = sentiment_analyzer(texts_for_sentiment, batch_size=16, truncation=True)
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
            
            new_comments_to_add.append(Comment(
                publication_id=comment_data['publication_id'],
                author=comment_data['author'],
                text_original=comment_data['text_original'],
                text_translated=text_translated,
                sentiment_label=sentiment_label,
                sentiment_score=sentiment_score
            ))

        if new_comments_to_add:
            session.bulk_save_objects(new_comments_to_add)
            self.progress_callback(f"  └ +{len(new_comments_to_add)} comentarios nuevos guardados.")
            return len(new_comments_to_add)
        return 0
    
    def scrape(self, translator: Optional[Callable], sentiment_analyzer: Optional[Callable]):
        if not self.graph:
            return

        PAGE_ID = os.getenv("PAGE_ID")
        session = SessionLocal()
        nuevas_publicaciones_totales = 0
        nuevos_comentarios_totales = 0

        try:
            self.progress_callback(f"Obteniendo feed de la página {PAGE_ID}...")
            posts_data = self.graph.get_connections(id=PAGE_ID, connection_name='feed', fields='id,message,created_time').get('data', [])
            
            if not posts_data:
                self.progress_callback("⚠️ No se encontraron publicaciones.")
                return

            post_ids = [post['id'] for post in posts_data]
            nuevas_publicaciones_totales = self._process_and_save_publications(session, posts_data)
            nuevos_comentarios_totales = self._process_and_save_comments(session, post_ids, translator, sentiment_analyzer)

            if nuevas_publicaciones_totales > 0 or nuevos_comentarios_totales > 0:
                self.progress_callback("Guardando todos los cambios en la base de datos...")
                session.commit()
            else:
                self.progress_callback("No se encontraron datos nuevos para guardar.")

        except Exception as e:
            session.rollback()
            self.progress_callback(f"❌ Error crítico en el proceso: {e}")
        finally:
            session.close()
            self.progress_callback(f"\n✅ Finalizado. Nuevas publicaciones: {nuevas_publicaciones_totales}, Total comentarios nuevos: {nuevos_comentarios_totales}")

def run_facebook_scrape_opt(
    progress_callback: Callable[[str], None], 
    translator: Optional[Callable], 
    sentiment_analyzer: Optional[Callable]
) -> None:
    """
    Versión PostgreSQL optimizada con procesamiento por lotes.
    """
    scraper = FacebookScraper(progress_callback)
    scraper.scrape(translator, sentiment_analyzer)