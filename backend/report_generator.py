from fpdf import FPDF
from typing import List, Dict
from datetime import datetime
import os
from .database import Publication, Comment

class PDFReportGenerator(FPDF):
    def __init__(self):
        super().__init__()
        self.set_auto_page_break(auto=True, margin=15)

    def header(self):
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, 'Sentimetrika - Reporte de Análisis', 0, 1, 'C')
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Página {self.page_no()}', 0, 0, 'C')

    def generate_single_publication_report(self, publication: Publication, comments: List[Comment]) -> str:
        self.add_page()
        self.set_font('Arial', 'B', 16)
        self.cell(0, 10, f'Reporte de Publicación: {publication.red_social}', 0, 1, 'L')
        
        self.set_font('Arial', '', 10)
        self.cell(0, 10, f'Fecha de generación: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}', 0, 1, 'L')
        self.ln(5)

        # --- Título de la Publicación ---
        self.set_font('Arial', 'B', 12)
        title = publication.title_translated or publication.title_original or "Sin Título"
        try:
            title_safe = title.encode('latin-1', 'replace').decode('latin-1')
        except:
            title_safe = title
        self.multi_cell(0, 8, f"Publicación: {title_safe}", border=0)
        self.ln(5)

        # --- Estadísticas de Sentimientos ---
        pos_count = sum(1 for c in comments if c.sentiment_label == 'positive')
        neg_count = sum(1 for c in comments if c.sentiment_label == 'negative')
        neu_count = sum(1 for c in comments if c.sentiment_label == 'neutral')
        total_comments = len(comments)

        self.set_font('Arial', 'B', 14)
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
        self.set_font('Arial', 'B', 14)
        self.cell(0, 10, 'Comentarios', 0, 1, 'L')
        self.ln(5)

        if not comments:
            self.set_font('Arial', 'I', 10)
            self.cell(0, 8, "  Sin comentarios.", 0, 1)
        else:
            self.set_font('Arial', '', 9)
            with self.table(col_widths=(20, 15, 65)) as table:
                header = table.row()
                header.cell("Autor", align='C')
                header.cell("Sentimiento", align='C')
                header.cell("Comentario", align='C')
                
                for c in comments:
                    row = table.row()
                    author = c.author or "Anon"
                    text = c.text_translated or c.text_original or ""
                    sentiment = c.sentiment_label or "N/A"
                    
                    try:
                        author_safe = author.encode('latin-1', 'replace').decode('latin-1')
                        text_safe = text.encode('latin-1', 'replace').decode('latin-1')
                    except:
                        author_safe = author
                        text_safe = text

                    row.cell(author_safe)
                    row.cell(sentiment)
                    row.cell(text_safe)
        
        # Guardar archivo
        output_dir = "reports"
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            
        filename = f"{output_dir}/reporte_publicacion_{publication.id[:8]}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        self.output(filename)
        return os.path.abspath(filename)

    def generate_report(self, social_network: str, publications: List[Publication], comments_map: Dict[str, List[Comment]]) -> str:
        self.add_page()
        self.set_font('Arial', 'B', 16)
        self.cell(0, 10, f'Reporte de {social_network}', 0, 1, 'L')
        
        self.set_font('Arial', '', 10)
        self.cell(0, 10, f'Fecha de generación: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}', 0, 1, 'L')
        self.ln(5)

        # --- Estadísticas Generales ---
        total_pubs = len(publications)
        total_comments = sum(len(comments) for comments in comments_map.values())
        
        all_comments = [c for comments in comments_map.values() for c in comments]
        pos_count = sum(1 for c in all_comments if c.sentiment_label == 'positive')
        neg_count = sum(1 for c in all_comments if c.sentiment_label == 'negative')
        neu_count = sum(1 for c in all_comments if c.sentiment_label == 'neutral')

        self.set_font('Arial', 'B', 14)
        self.cell(0, 10, 'Resumen Estadístico', 0, 1, 'L')
        
        # Tabla de resumen
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
        self.set_font('Arial', 'B', 14)
        self.cell(0, 10, 'Detalle de Publicaciones', 0, 1, 'L')
        self.ln(5)

        for pub in publications:
            # Título de la publicación
            self.set_font('Arial', 'B', 11)
            title = pub.title_translated or pub.title_original or "Sin Título"
            # Encode/decode para evitar errores de caracteres en fpdf standard (si no se usa unicode font)
            # fpdf2 soporta unicode mejor si se carga una fuente, pero por defecto usa latin-1
            # Intentaremos limpiar un poco
            try:
                title_safe = title.encode('latin-1', 'replace').decode('latin-1')
            except:
                title_safe = title
            
            self.multi_cell(0, 8, f"Post: {title_safe}", border=0)
            self.ln(2)
            
            pub_comments = comments_map.get(pub.id, [])
            
            if not pub_comments:
                self.set_font('Arial', 'I', 10)
                self.cell(0, 8, "  Sin comentarios.", 0, 1)
            else:
                self.set_font('Arial', '', 9)
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
                        author = c.author or "Anon"
                        text = c.text_translated or c.text_original or ""
                        sentiment = c.sentiment_label or "N/A"
                        
                        try:
                            author_safe = author.encode('latin-1', 'replace').decode('latin-1')
                            text_safe = text.encode('latin-1', 'replace').decode('latin-1')
                        except:
                            author_safe = author
                            text_safe = text

                        row.cell(author_safe)
                        row.cell(sentiment)
                        row.cell(text_safe)
            
            self.ln(5)

        # Guardar archivo
        output_dir = "reports"
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            
        filename = f"{output_dir}/reporte_{social_network.lower()}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        self.output(filename)
        return os.path.abspath(filename)
