from fpdf import FPDF, XPos, YPos
from typing import List, Dict
from datetime import datetime
import os
from .database import Publication, Comment

class PDFReportGenerator(FPDF):
    def __init__(self):
        super().__init__()
        self.set_auto_page_break(auto=True, margin=15)
        
        # Use built-in Helvetica font - no external files needed
        # All text will be sanitized to remove problematic Unicode characters
        self.current_font_name = "Helvetica"
        self.set_font(self.current_font_name, size=12)

    def header(self):
        # Logo
        logo_path = os.path.join(os.path.dirname(__file__), "..", "frontend", "assets", "Sentimetrika.png")
        if os.path.exists(logo_path):
            self.image(logo_path, x=10, y=8, w=30)
        
        self.set_font(self.current_font_name, style='B', size=12)
        # Move to the right for the title, to avoid overlapping the logo
        self.set_x(45) 
        self.cell(0, 10, 'Sentimetrika - Reporte de Analisis', new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font(self.current_font_name, style='I', size=8)
        self.cell(0, 10, f'Pagina {self.page_no()}', new_x=XPos.RIGHT, new_y=YPos.TOP, align='C')

    def _sanitize_text(self, text: str) -> str:
        """Sanitize text to remove problematic Unicode characters"""
        if not text:
            return ""
        
        # Replace common problematic characters
        replacements = {
            ''': "'",  # Curly apostrophe
            ''': "'",
            '"': '"',  # Curly quotes
            '"': '"',
            '–': '-',  # En dash
            '—': '-',  # Em dash
            '…': '...',  # Ellipsis
            'á': 'a', 'é': 'e', 'í': 'i', 'ó': 'o', 'ú': 'u',  # Accented vowels
            'Á': 'A', 'É': 'E', 'Í': 'I', 'Ó': 'O', 'Ú': 'U',
            'ñ': 'n', 'Ñ': 'N',  # Spanish n with tilde
            'ü': 'u', 'Ü': 'U',  # U with diaeresis
        }
        for old, new in replacements.items():
            text = text.replace(old, new)
        
        # Remove any remaining non-ASCII characters
        text = text.encode('ascii', 'ignore').decode('ascii')
        return text

    def generate_single_publication_report(self, publication: Publication, comments: List[Comment]) -> str:
        self.add_page()
        self.set_font(self.current_font_name, style='B', size=16)
        self.cell(0, 10, f'Reporte de Publicacion: {publication.red_social}', new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='L')
        
        self.set_font(self.current_font_name, size=10)
        self.cell(0, 10, f'Fecha de generacion: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}', new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='L')
        self.ln(5)

        # --- Título de la Publicación ---
        self.set_font(self.current_font_name, style='B', size=12)
        title = getattr(publication, 'title_translated', None) or getattr(publication, 'title_original', None) or "Sin Titulo"
        title = self._sanitize_text(title)
        self.multi_cell(0, 8, f"Publicacion: {title}", border=0)
        self.ln(5)

        # --- Estadísticas de Sentimientos ---
        pos_count = sum(1 for c in comments if c.sentiment_label == 'positive')
        neg_count = sum(1 for c in comments if c.sentiment_label == 'negative')
        neu_count = sum(1 for c in comments if c.sentiment_label == 'neutral')
        total_comments = len(comments)

        self.set_font(self.current_font_name, style='B', size=14)
        self.cell(0, 10, 'Resumen de Sentimientos', new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='L')
        
        with self.table() as table:
            row = table.row()
            row.cell("Sentimiento")
            row.cell("Cantidad")
            row.cell("Porcentaje")
            
            row = table.row()
            row.cell("Positivos")
            row.cell(str(pos_count))
            row.cell(f"{(pos_count / total_comments * 100) if total_comments > 0 else 0:.2f}%")
            
            row = table.row()
            row.cell("Negativos")
            row.cell(str(neg_count))
            row.cell(f"{(neg_count / total_comments * 100) if total_comments > 0 else 0:.2f}%")

            row = table.row()
            row.cell("Neutrales")
            row.cell(str(neu_count))
            row.cell(f"{(neu_count / total_comments * 100) if total_comments > 0 else 0:.2f}%")

            row = table.row()
            row.cell("Total")
            row.cell(str(total_comments))
            row.cell("100%")

        self.ln(10)

        # --- Detalle de Comentarios ---
        self.set_font(self.current_font_name, style='B', size=14)
        self.cell(0, 10, 'Comentarios', new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='L')
        self.ln(5)

        if not comments:
            self.set_font(self.current_font_name, style='I', size=10)
            self.cell(0, 8, "  Sin comentarios.", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        else:
            self.set_font(self.current_font_name, size=9)
            with self.table(col_widths=(20, 15, 65)) as table:
                header = table.row()
                header.cell("Autor", align='C')
                header.cell("Sentimiento", align='C')
                header.cell("Comentario", align='C')
                
                for c in comments:
                    row = table.row()
                    author = self._sanitize_text(getattr(c, 'author', None) or "Anon")
                    text = self._sanitize_text(getattr(c, 'text_translated', None) or getattr(c, 'text_original', None) or "")
                    sentiment = getattr(c, 'sentiment_label', None) or "N/A"

                    row.cell(author)
                    row.cell(sentiment)
                    row.cell(text)
        
        # Guardar archivo con nombre descriptivo
        output_dir = "reports"
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        # Formato: Sentimetrika_[RedSocial]_Publicacion_[ID]_[Fecha].pdf
        social_network_name = publication.red_social.replace(' ', '_')
        pub_id = publication.id[:8] if hasattr(publication, 'id') else 'pub'
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{output_dir}/Sentimetrika_{social_network_name}_Publicacion_{pub_id}_{timestamp}.pdf"
        self.output(filename)
        return os.path.abspath(filename)

    def generate_report(self, social_network: str, publications: List[Publication], comments_map: Dict[str, List[Comment]]) -> str:
        self.add_page()
        self.set_font(self.current_font_name, style='B', size=16)
        self.cell(0, 10, f'Reporte de {social_network}', new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='L')
        
        self.set_font(self.current_font_name, size=10)
        self.cell(0, 10, f'Fecha de generacion: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}', new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='L')
        self.ln(5)

        # --- Estadísticas Generales ---
        total_pubs = len(publications)
        total_comments = sum(len(comments) for comments in comments_map.values())
        
        all_comments = [c for comments in comments_map.values() for c in comments]
        pos_count = sum(1 for c in all_comments if c.sentiment_label == 'positive')
        neg_count = sum(1 for c in all_comments if c.sentiment_label == 'negative')
        neu_count = sum(1 for c in all_comments if c.sentiment_label == 'neutral')

        self.set_font(self.current_font_name, style='B', size=14)
        self.cell(0, 10, 'Resumen Estadistico', new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='L')
        
        with self.table() as table:
            row = table.row()
            row.cell("Metrica")
            row.cell("Valor")
            
            row = table.row()
            row.cell("Total Publicaciones")
            row.cell(str(total_pubs))
            
            row = table.row()
            row.cell("Total Comentarios")
            row.cell(str(total_comments))
            
            row = table.row()
            row.cell("Positivos")
            row.cell(str(pos_count))
            
            row = table.row()
            row.cell("Negativos")
            row.cell(str(neg_count))
            
            row = table.row()
            row.cell("Neutrales")
            row.cell(str(neu_count))
            
        self.ln(10)

        # --- Detalle por Publicación ---
        self.set_font(self.current_font_name, style='B', size=14)
        self.cell(0, 10, 'Detalle de Publicaciones', new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='L')
        self.ln(5)

        for pub in publications:
            # Título de la publicación
            self.set_font(self.current_font_name, style='B', size=11)
            title = getattr(pub, 'title_translated', None) or getattr(pub, 'title_original', None) or "Sin Titulo"
            title = self._sanitize_text(title)
            
            self.multi_cell(0, 8, f"Post: {title}", border=0)
            self.ln(2)
            
            pub_comments = comments_map.get(pub.id, [])
            
            if not pub_comments:
                self.set_font(self.current_font_name, style='I', size=10)
                self.cell(0, 8, "  Sin comentarios.", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            else:
                self.set_font(self.current_font_name, size=9)
                # Tabla de comentarios
                # Definir anchos relativos: Autor (20%), Sentimiento (15%), Comentario (65%)
                with self.table(col_widths=(20, 15, 65)) as table:
                    header = table.row()
                    header.cell("Autor", align='C')
                    header.cell("Sentimiento", align='C')
                    header.cell("Comentario", align='C')
                    
                    for c in pub_comments:
                        row = table.row()
                        
                        # Limpieza básica de texto
                        author = self._sanitize_text(getattr(c, 'author', None) or "Anon")
                        text = self._sanitize_text(getattr(c, 'text_translated', None) or getattr(c, 'text_original', None) or "")
                        sentiment = getattr(c, 'sentiment_label', None) or "N/A"

                        row.cell(author)
                        row.cell(sentiment)
                        row.cell(text)
            
            self.ln(5)

        # Guardar archivo con nombre descriptivo
        output_dir = "reports"
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        # Formato: Sentimetrika_[RedSocial]_General_[Fecha].pdf
        social_network_name = social_network.replace(' ', '_')
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{output_dir}/Sentimetrika_{social_network_name}_General_{timestamp}.pdf"
        self.output(filename)
        return os.path.abspath(filename)
