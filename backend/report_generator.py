from fpdf import FPDF
from typing import List, Dict
from datetime import datetime
import os
from .database import Publication, Comment

class PDFReportGenerator(FPDF):
    def __init__(self):
        super().__init__()
        self.set_auto_page_break(auto=True, margin=15)
        
        # For full Unicode support (including emojis and extended Latin characters),
        # a .ttf font file must be provided. DejaVuSans is a good option.
        # Ensure 'DejaVuSans.ttf', 'DejaVuSans-Bold.ttf', etc., are accessible to the application.
        # You might need to place them in the same directory as this script or specify a full path.
        try:
            self.add_font("DejaVuSans", "", "DejaVuSans.ttf", uni=True)
            self.add_font("DejaVuSans", "B", "DejaVuSans-Bold.ttf", uni=True) # Assuming a bold variant exists
            self.add_font("DejaVuSans", "I", "DejaVuSans-Oblique.ttf", uni=True) # Assuming an italic variant exists
            self.add_font("DejaVuSans", "BI", "DejaVuSans-BoldOblique.ttf", uni=True) # Assuming bold-italic variant exists
            self.current_font_name = "DejaVuSans"
        except (RuntimeError, FileNotFoundError): # FileNotFoundError or other font loading issues
            print("Warning: DejaVuSans.ttf (or its variants) not found or could not be loaded. Falling back to Arial. "
                  "Unicode characters (like emojis or special accented letters) may not render correctly. "
                  "Please ensure DejaVuSans.ttf and its variants are available.")
            self.current_font_name = "Arial" # Fallback, but with limited Unicode
        
        self.set_font(self.current_font_name, '', 12) # Set default font

    def header(self):
        # Logo
        logo_path = os.path.join(os.path.dirname(__file__), "..", "frontend", "assets", "Sentimetrika.png")
        if os.path.exists(logo_path):
            self.image(logo_path, x=10, y=8, w=30)
        
        self.set_font(self.current_font_name, 'B', 12)
        # Move to the right for the title, to avoid overlapping the logo
        self.set_x(45) 
        self.cell(0, 10, 'Sentimetrika - Reporte de Análisis', 0, 1, 'C')
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font(self.current_font_name, 'I', 8)
        self.cell(0, 10, f'Página {self.page_no()}', 0, 0, 'C')

    def generate_single_publication_report(self, publication: Publication, comments: List[Comment]) -> str:
        self.add_page()
        self.set_font(self.current_font_name, 'B', 16)
        self.cell(0, 10, f'Reporte de Publicación: {publication.red_social}', 0, 1, 'L')
        
        self.set_font(self.current_font_name, '', 10)
        self.cell(0, 10, f'Fecha de generación: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}', 0, 1, 'L')
        self.ln(5)

        # --- Título de la Publicación ---
        self.set_font(self.current_font_name, 'B', 12)
        title = getattr(publication, 'title_translated', None) or getattr(publication, 'title_original', None) or "Sin Título"
        self.multi_cell(0, 8, f"Publicación: {title}", border=0)
        self.ln(5)

        # --- Estadísticas de Sentimientos ---
        pos_count = sum(1 for c in comments if c.sentiment_label == 'positive')
        neg_count = sum(1 for c in comments if c.sentiment_label == 'negative')
        neu_count = sum(1 for c in comments if c.sentiment_label == 'neutral')
        total_comments = len(comments)

        self.set_font(self.current_font_name, 'B', 14)
        self.cell(0, 10, 'Resumen de Sentimientos', 0, 1, 'L')
        
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
        self.set_font(self.current_font_name, 'B', 14)
        self.cell(0, 10, 'Comentarios', 0, 1, 'L')
        self.ln(5)

        if not comments:
            self.set_font(self.current_font_name, 'I', 10)
            self.cell(0, 8, "  Sin comentarios.", 0, 1)
        else:
            self.set_font(self.current_font_name, '', 9)
            with self.table(col_widths=(20, 15, 65)) as table:
                header = table.row()
                header.cell("Autor", align='C')
                header.cell("Sentimiento", align='C')
                header.cell("Comentario", align='C')
                
                for c in comments:
                    row = table.row()
                    author = getattr(c, 'author', None) or "Anon"
                    text = getattr(c, 'text_translated', None) or getattr(c, 'text_original', None) or ""
                    sentiment = getattr(c, 'sentiment_label', None) or "N/A"

                    row.cell(author)
                    row.cell(sentiment)
                    row.cell(text)
        
        # Guardar archivo
        output_dir = "reports"
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            
        filename = f"{output_dir}/reporte_publicacion_{publication.id[:8]}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        self.output(filename)
        return os.path.abspath(filename)

    def generate_report(self, social_network: str, publications: List[Publication], comments_map: Dict[str, List[Comment]]) -> str:
        self.add_page()
        self.set_font(self.current_font_name, 'B', 16)
        self.cell(0, 10, f'Reporte de {social_network}', 0, 1, 'L')
        
        self.set_font(self.current_font_name, '', 10)
        self.cell(0, 10, f'Fecha de generación: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}', 0, 1, 'L')
        self.ln(5)

        # --- Estadísticas Generales ---
        total_pubs = len(publications)
        total_comments = sum(len(comments) for comments in comments_map.values())
        
        all_comments = [c for comments in comments_map.values() for c in comments]
        pos_count = sum(1 for c in all_comments if c.sentiment_label == 'positive')
        neg_count = sum(1 for c in all_comments if c.sentiment_label == 'negative')
        neu_count = sum(1 for c in all_comments if c.sentiment_label == 'neutral')

        self.set_font(self.current_font_name, 'B', 14)
        self.cell(0, 10, 'Resumen Estadístico', 0, 1, 'L')
        
        with self.table() as table:
            row = table.row()
            row.cell("Métrica")
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
        self.set_font(self.current_font_name, 'B', 14)
        self.cell(0, 10, 'Detalle de Publicaciones', 0, 1, 'L')
        self.ln(5)

        for pub in publications:
            # Título de la publicación
            self.set_font(self.current_font_name, 'B', 11)
            title = getattr(pub, 'title_translated', None) or getattr(pub, 'title_original', None) or "Sin Título"
            
            self.multi_cell(0, 8, f"Post: {title}", border=0)
            self.ln(2)
            
            pub_comments = comments_map.get(pub.id, [])
            
            if not pub_comments:
                self.set_font(self.current_font_name, 'I', 10)
                self.cell(0, 8, "  Sin comentarios.", 0, 1)
            else:
                self.set_font(self.current_font_name, '', 9)
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
                        author = getattr(c, 'author', None) or "Anon"
                        text = getattr(c, 'text_translated', None) or getattr(c, 'text_original', None) or ""
                        sentiment = getattr(c, 'sentiment_label', None) or "N/A"

                        row.cell(author)
                        row.cell(sentiment)
                        row.cell(text)
            
            self.ln(5)

        # Guardar archivo
        output_dir = "reports"
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            
        filename = f"{output_dir}/reporte_{social_network.lower()}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        self.output(filename)
        return os.path.abspath(filename)
