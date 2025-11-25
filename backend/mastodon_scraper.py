import os
import re
import pathlib
from mastodon import Mastodon
from dotenv import load_dotenv
from .database import SessionLocal, Publication, Comment
from typing import List, Dict, Any, Callable, Optional
from sqlalchemy.orm import Session
from .sentiment_utils import _mapear_sentimiento

load_dotenv()

class MastodonScraper:
    def __init__(self, progress_callback: Callable[[str], None]):
        self.progress_callback = progress_callback
        self.mastodon = self._conectar_api_mastodon()

    def _limpiar_html(self, html_content: str) -> str:
        """Elimina etiquetas HTML del contenido de un toot."""
        if not html_content:
            return ""
        cleanr = re.compile('<.*?>')
        cleantext = re.sub(cleanr, '', html_content)
        cleantext = cleantext.replace("</p>", " ").replace("<br>", " ")
        return " ".join(cleantext.split())

    def _conectar_api_mastodon(self) -> Optional[Mastodon]:
        """Conecta a la API de Mastodon."""
        # Intentar leer token de variable de entorno primero (más seguro)
        TOKEN = os.getenv("MASTODON_ACCESS_TOKEN")
        INSTANCE_URL = os.getenv("MASTODON_BASE_URL", "https://mastodon.social")

        # Fallback a archivo si no hay variable de entorno (para compatibilidad)
        if not TOKEN:
            TOKEN_FILE = pathlib.Path(__file__).parent / "user_token.secret"
            if os.path.exists(TOKEN_FILE):
                TOKEN = TOKEN_FILE.read_text().strip()

        if not TOKEN:
            self.progress_callback("⚠️ No se encontró token de Mastodon. Usando modo público (limitado).")
            try:
                return Mastodon(api_base_url=INSTANCE_URL)
            except:
                self.progress_callback("❌ Error crítico: No se pudo conectar ni en modo público.")
                return None

        try:
            mastodon = Mastodon(
                access_token=TOKEN,
                api_base_url=INSTANCE_URL
            )
            # Verificar credenciales si tenemos token
            try:
                mastodon.account_verify_credentials()
                self.progress_callback("✅ Conexión exitosa a Mastodon (Autenticado).")
            except:
                self.progress_callback("⚠️ Token inválido o expirado. Usando modo público.")
                mastodon = Mastodon(api_base_url=INSTANCE_URL)
            
            return mastodon
        except Exception as e:
            self.progress_callback(f"❌ Error al conectar a Mastodon: {e}")
            return None

    def _process_and_save_publications(self, session: Session, posts_data: List[Dict[str, Any]]) -> int:
        if not posts_data: return 0
        
        post_ids = [p['id'] for p in posts_data]
        existing_pubs = {p[0] for p in session.query(Publication.id).filter(Publication.id.in_(post_ids)).all()}
        
        new_pubs = []
        for post in posts_data:
            if post['id'] not in existing_pubs:
                new_pubs.append(Publication(
                    id=post['id'],
                    red_social="Mastodon",
                    title_original=post['text_original'],
                    title_translated=post['text_translated']
                ))
        
        if new_pubs:
            session.bulk_save_objects(new_pubs)
            self.progress_callback(f"  └ +{len(new_pubs)} toots nuevos.")
            return len(new_pubs)
        return 0

    def _process_and_save_comments(self, session: Session, all_comments: List[Dict[str, Any]], translator, sentiment) -> int:
        if not all_comments: return 0
        
        # Filtrar duplicados (simple)
        existing_tuples = set()
        post_ids = list({c['publication_id'] for c in all_comments})
        if post_ids:
            query = session.query(Comment.publication_id, Comment.text_original).filter(Comment.publication_id.in_(post_ids))
            existing_tuples = {(pid, txt) for pid, txt in query}

        unique = [c for c in all_comments if (c['publication_id'], c['text_original']) not in existing_tuples]
        
        if not unique: return 0
        
        self.progress_callback(f"Procesando {len(unique)} respuestas nuevas...")
        
        # IA en lote
        texts = [c['text_original'] for c in unique]
        translations = {}
        sentiments = []
        
        if translator:
            try:
                # Filtrar textos vacíos o muy cortos para no gastar IA
                to_translate = [t for t in texts if len(t) > 2]
                if to_translate:
                    res = translator(to_translate, max_length=512, truncation=True, batch_size=8)
                    translations = {t: r['translation_text'] for t, r in zip(to_translate, res)}
            except: pass
            
        if sentiment:
            texts_sent = [translations.get(t, t) for t in texts if len(t) > 2]
            if texts_sent:
                try:
                    sentiments = sentiment(texts_sent, truncation=True, batch_size=8)
                except: pass

        to_save = []
        sent_idx = 0
        for c in unique:
            txt = c['text_original']
            trans = translations.get(txt, txt)
            
            s_l, s_s = "neutral", "0.0"
            if len(txt) > 2 and sent_idx < len(sentiments):
                s_l = _mapear_sentimiento(sentiments[sent_idx]['label'])
                s_s = str(round(sentiments[sent_idx]['score'], 4))
                sent_idx += 1
                
            to_save.append(Comment(
                publication_id=c['publication_id'],
                author=c['author'],
                text_original=txt,
                text_translated=trans,
                sentiment_label=s_l,
                sentiment_score=s_s
            ))
            
        if to_save:
            session.bulk_save_objects(to_save)
            return len(to_save)
        return 0

    def scrape(self, target_ids: List[str], translator, sentiment_analyzer):
        """
        Ejecuta el scraping sobre una lista de IDs proporcionada en memoria.
        """
        if not self.mastodon:
            return

        if not target_ids:
            self.progress_callback("⚠️ No hay IDs para procesar.")
            return

        session = SessionLocal()
        nuevos_pubs = 0
        nuevos_comms = 0

        try:
            self.progress_callback(f"Analizando {len(target_ids)} IDs de Mastodon...")
            
            posts_data = []
            all_comments = []

            for post_id in target_ids:
                if not post_id.isdigit(): continue
                
                try:
                    # 1. Obtener Toot
                    status = self.mastodon.status(post_id)
                    text_clean = self._limpiar_html(status.content)
                    
                    # Traducción preliminar del post (para guardar en Publication)
                    trans_title = text_clean
                    if translator and text_clean:
                        try:
                            res = translator(text_clean[:512])
                            trans_title = res[0]['translation_text']
                        except: pass

                    posts_data.append({
                        'id': str(status.id),
                        'text_original': text_clean,
                        'text_translated': trans_title
                    })

                    # 2. Obtener Contexto (Comentarios)
                    context = self.mastodon.status_context(post_id)
                    descendants = context.get('descendants', [])
                    
                    for reply in descendants[:20]: # Límite por post
                        c_text = self._limpiar_html(reply.content)
                        if c_text:
                            author = reply.account.username or "unknown"
                            all_comments.append({
                                'publication_id': str(status.id),
                                'author': author,
                                'text_original': c_text
                            })
                            
                except Exception as e:
                    print(f"Error ID {post_id}: {e}")
                    continue

            # Guardar en lotes
            nuevos_pubs = self._process_and_save_publications(session, posts_data)
            nuevos_comms = self._process_and_save_comments(session, all_comments, translator, sentiment_analyzer)

            if nuevos_pubs > 0 or nuevos_comms > 0:
                session.commit()
                self.progress_callback("✅ Cambios guardados en BD.")
            else:
                self.progress_callback("Todo actualizado.")

        except Exception as e:
            session.rollback()
            self.progress_callback(f"❌ Error general: {e}")
        finally:
            session.close()
            self.progress_callback(f"Resumen: {nuevos_pubs} toots, {nuevos_comms} respuestas.")

def run_mastodon_scrape_opt(progress_callback, translator, sentiment, target_ids_list=None):
    """
    Punto de entrada. Recibe lista de IDs desde la UI.
    """
    scraper = MastodonScraper(progress_callback)
    
    # Si no vienen IDs de la UI, intentamos leer el archivo legacy por si acaso
    ids_to_use = target_ids_list
    if not ids_to_use:
        try:
            # Opcional: Mantener compatibilidad con archivo si se desea
            pass 
        except: 
            pass
            
    scraper.scrape(ids_to_use, translator, sentiment)