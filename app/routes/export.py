# export.py
from flask import Blueprint, send_file, jsonify, request
import logging
import io
import csv
import json
from datetime import datetime
from decimal import Decimal

logger = logging.getLogger(__name__)

export_bp = Blueprint('export', __name__)

class DecimalEncoder(json.JSONEncoder):
    """Кастомный энкодер для обработки Decimal объектов"""
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super(DecimalEncoder, self).default(obj)

def convert_decimal_to_float(data):
    """Рекурсивно преобразует Decimal в float в данных"""
    if isinstance(data, dict):
        return {key: convert_decimal_to_float(value) for key, value in data.items()}
    elif isinstance(data, list):
        return [convert_decimal_to_float(item) for item in data]
    elif isinstance(data, Decimal):
        return float(data)
    else:
        return data

@export_bp.route('/api/export/<report_type>/<format_type>')
def export_report(report_type, format_type):
    """Экспорт отчета в указанном формате"""
    try:
        # Получаем данные в зависимости от типа отчета
        data = get_report_data(report_type)
        
        if not data:
            return jsonify({'error': 'No data available for export'}), 404
        
        # Преобразуем Decimal в float для JSON
        if format_type == 'json':
            data = convert_decimal_to_float(data)
        
        # Генерируем файл
        if format_type == 'csv':
            return export_csv(data, report_type)
        elif format_type == 'json':
            return export_json(data, report_type)
        elif format_type == 'txt':
            return export_txt(data, report_type)
        else:
            return jsonify({'error': 'Unsupported format'}), 400
            
    except Exception as e:
        logger.error(f"Export error: {str(e)}")
        return jsonify({'error': str(e)}), 500

def export_csv(data, report_type):
    """Экспорт в CSV"""
    try:
        if not data:
            return jsonify({'error': 'No data to export'}), 404
            
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Заголовки
        if data and len(data) > 0:
            headers = list(data[0].keys())
            writer.writerow(headers)
            
            # Данные
            for row in data:
                # Преобразуем Decimal в строку для CSV
                row_data = []
                for header in headers:
                    value = row.get(header, '')
                    if isinstance(value, Decimal):
                        value = float(value)
                    row_data.append(str(value))
                writer.writerow(row_data)
        
        output.seek(0)
        filename = f"{report_type}_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        return send_file(
            io.BytesIO(output.getvalue().encode('utf-8')),
            mimetype='text/csv',
            as_attachment=True,
            download_name=filename
        )
    except Exception as e:
        logger.error(f"CSV export error: {str(e)}")
        return jsonify({'error': str(e)}), 500

def export_json(data, report_type):
    """Экспорт в JSON"""
    try:
        if not data:
            return jsonify({'error': 'No data to export'}), 404
            
        filename = f"{report_type}_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        return send_file(
            io.BytesIO(json.dumps(data, ensure_ascii=False, indent=2, cls=DecimalEncoder).encode('utf-8')),
            mimetype='application/json',
            as_attachment=True,
            download_name=filename
        )
    except Exception as e:
        logger.error(f"JSON export error: {str(e)}")
        return jsonify({'error': str(e)}), 500

def export_txt(data, report_type):
    """Экспорт в TXT"""
    try:
        if not data:
            return jsonify({'error': 'No data to export'}), 404
            
        output = io.StringIO()
        
        if data and len(data) > 0:
            headers = list(data[0].keys())
            output.write("\t".join(headers) + "\n")
            
            for row in data:
                row_data = []
                for header in headers:
                    value = row.get(header, '')
                    if isinstance(value, Decimal):
                        value = float(value)
                    row_data.append(str(value))
                output.write("\t".join(row_data) + "\n")
        
        output.seek(0)
        filename = f"{report_type}_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        
        return send_file(
            io.BytesIO(output.getvalue().encode('utf-8')),
            mimetype='text/plain',
            as_attachment=True,
            download_name=filename
        )
    except Exception as e:
        logger.error(f"TXT export error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@export_bp.route('/api/export/formats')
def get_export_formats():
    """Возвращает список поддерживаемых форматов"""
    return jsonify({
        'formats': ['csv', 'json', 'txt']
    })

def get_report_data(report_type):
    """Получение данных для отчетов"""
    try:
        from app.models.database import db_manager
        
        if report_type == 'blocks':
            return get_blocks_data()
        elif report_type == 'drilling_progress':
            return get_drilling_progress_data()
        elif report_type == 'rig_productivity':
            return get_rig_productivity_data()
        elif report_type == 'blocks_efficiency':
            return get_blocks_efficiency_data()
        else:
            return []
    except Exception as e:
        logger.error(f"Error getting report data for {report_type}: {str(e)}")
        return []

def get_blocks_data():
    """Получение данных по блокам"""
    try:
        from app.models.database import db_manager
        
        result = db_manager.execute_query("""
            SELECT 
                "BlockID" as block_id,
                "BlockName" as block_name,
                "CrushEnergy" as crush_energy,
                "HolesSpace" as holes_space,
                "RowsDistance" as rows_distance,
                "RockName" as rock_name,
                "RockRigity" as rock_rigidity,
                "RockDensity" as rock_density
            FROM public."BlockInfo"
        """)
        return [dict(row) for row in result] if result else []
    except Exception as e:
        logger.error(f"Error getting blocks data: {str(e)}")
        return []

def get_drilling_progress_data():
    """Получение данных о прогрессе бурения"""
    try:
        from app.models.database import db_manager
        
        result = db_manager.execute_function('calculate_drilling_progress')
        return [dict(row) for row in result] if result else []
    except Exception as e:
        logger.error(f"Error getting drilling progress data: {str(e)}")
        return []

def get_rig_productivity_data():
    """Получение данных о производительности станков"""
    try:
        from app.models.database import db_manager
        
        result = db_manager.execute_function('calculate_rig_productivity_by_block')
        return [dict(row) for row in result] if result else []
    except Exception as e:
        logger.error(f"Error getting rig productivity data: {str(e)}")
        return []

def get_blocks_efficiency_data():
    """Получение данных об эффективности блоков"""
    try:
        from app.models.database import db_manager
        
        result = db_manager.execute_function('calculate_drilling_efficiency_by_block')
        return [dict(row) for row in result] if result else []
    except Exception as e:
        logger.error(f"Error getting blocks efficiency data: {str(e)}")
        return []