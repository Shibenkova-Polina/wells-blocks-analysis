import csv
import json
import xml.etree.ElementTree as ET
from io import StringIO, BytesIO
from datetime import datetime
import base64

class ExportHandler:
    def __init__(self):
        self.supported_formats = ['csv', 'json', 'xml', 'txt', 'pdf', 'excel', 'docx']
    
    def export_data(self, data, format_type, filename=None):
        """Основной метод для экспорта данных"""
        if format_type == 'csv':
            return self._to_csv(data, filename)
        elif format_type == 'json':
            return self._to_json(data, filename)
        elif format_type == 'xml':
            return self._to_xml(data, filename)
        elif format_type == 'txt':
            return self._to_txt(data, filename)
        elif format_type == 'pdf':
            return self._to_pdf(data, filename)
        elif format_type == 'excel':
            return self._to_excel(data, filename)
        elif format_type == 'docx':
            return self._to_docx(data, filename)
        else:
            raise ValueError(f"Unsupported format: {format_type}")
    
    def _to_csv(self, data, filename):
        """Экспорт в CSV"""
        if not data:
            return self._empty_response('csv')
        
        output = StringIO()
        writer = csv.writer(output)
        
        # Заголовки
        if isinstance(data, list) and len(data) > 0:
            headers = list(data[0].keys())
            writer.writerow(headers)
            
            # Данные
            for row in data:
                writer.writerow([str(row.get(header, '')) for header in headers])
        
        csv_content = output.getvalue()
        output.close()
        
        if not filename:
            filename = f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        return BytesIO(csv_content.encode('utf-8')), 'text/csv', filename
    
    def _to_json(self, data, filename):
        """Экспорт в JSON"""
        if not filename:
            filename = f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        json_content = json.dumps(data, ensure_ascii=False, indent=2)
        return BytesIO(json_content.encode('utf-8')), 'application/json', filename
    
    def _to_xml(self, data, filename):
        """Экспорт в XML"""
        root = ET.Element('report')
        root.set('generated', datetime.now().isoformat())
        
        if isinstance(data, list):
            for i, item in enumerate(data):
                record = ET.SubElement(root, 'record')
                record.set('id', str(i))
                for key, value in item.items():
                    field = ET.SubElement(record, key)
                    field.text = str(value)
        
        xml_str = ET.tostring(root, encoding='utf-8', method='xml')
        
        if not filename:
            filename = f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xml"
        
        return BytesIO(xml_str), 'application/xml', filename
    
    def _to_txt(self, data, filename):
        """Экспорт в текстовый формат"""
        if not filename:
            filename = f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        
        lines = []
        if isinstance(data, list) and len(data) > 0:
            # Заголовки
            headers = list(data[0].keys())
            lines.append(" | ".join(headers))
            lines.append("-" * len(" | ".join(headers)))
            
            # Данные
            for row in data:
                line = " | ".join([str(row.get(header, '')) for header in headers])
                lines.append(line)
        
        txt_content = "\n".join(lines)
        return BytesIO(txt_content.encode('utf-8')), 'text/plain', filename
    
    def _to_pdf(self, data, filename):
        """Экспорт в PDF (упрощенная версия)"""
        if not filename:
            filename = f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        
        # Создаем простой PDF с использованием базового HTML
        pdf_content = self._generate_pdf_content(data)
        return BytesIO(pdf_content.encode('utf-8')), 'application/pdf', filename
    
    def _to_excel(self, data, filename):
        """Экспорт в Excel (CSV с другим расширением)"""
        if not filename:
            filename = f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        
        # Используем CSV как временное решение для Excel
        csv_buffer, _, _ = self._to_csv(data, filename.replace('.xlsx', '.csv'))
        return csv_buffer, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', filename
    
    def _to_docx(self, data, filename):
        """Экспорт в Word (упрощенная версия)"""
        if not filename:
            filename = f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.docx"
        
        # Создаем простой документ
        doc_content = self._generate_docx_content(data)
        return BytesIO(doc_content.encode('utf-8')), 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', filename
    
    def _generate_pdf_content(self, data):
        """Генерация содержимого для PDF"""
        html_content = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; }
                table { width: 100%; border-collapse: collapse; margin: 20px 0; }
                th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
                th { background-color: #f2f2f2; }
                h1 { color: #333; }
            </style>
        </head>
        <body>
            <h1>Отчет</h1>
            <p>Сгенерировано: """ + datetime.now().strftime('%Y-%m-%d %H:%M:%S') + """</p>
        """
        
        if isinstance(data, list) and len(data) > 0:
            html_content += "<table><tr>"
            # Заголовки
            headers = list(data[0].keys())
            for header in headers:
                html_content += f"<th>{header}</th>"
            html_content += "</tr>"
            
            # Данные
            for row in data:
                html_content += "<tr>"
                for header in headers:
                    html_content += f"<td>{str(row.get(header, ''))}</td>"
                html_content += "</tr>"
            html_content += "</table>"
        
        html_content += "</body></html>"
        return html_content
    
    def _generate_docx_content(self, data):
        """Генерация содержимого для Word"""
        doc_content = "Отчет\n"
        doc_content += "Сгенерировано: " + datetime.now().strftime('%Y-%m-%d %H:%M:%S') + "\n\n"
        
        if isinstance(data, list) and len(data) > 0:
            # Заголовки
            headers = list(data[0].keys())
            doc_content += "\t".join(headers) + "\n"
            doc_content += "-" * (len("\t".join(headers))) + "\n"
            
            # Данные
            for row in data:
                doc_content += "\t".join([str(row.get(header, '')) for header in headers]) + "\n"
        
        return doc_content
    
    def _empty_response(self, format_type):
        """Возвращает пустой файл указанного формата"""
        filename = f"empty_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{format_type}"
        empty_content = "No data available"
        return BytesIO(empty_content.encode('utf-8')), f'text/{format_type}', filename