# block_export.py
from flask import Blueprint, send_file, jsonify
import logging
import io
import csv
import json
from datetime import datetime
from decimal import Decimal
from psycopg2.extras import RealDictCursor

from app.routes.analytics import safe_float

logger = logging.getLogger(__name__)

block_export_bp = Blueprint('block_export', __name__)

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

@block_export_bp.route('/api/export/block/<block_id>/<data_type>/<format_type>')
def export_block_data(block_id, data_type, format_type):
    """Экспорт данных конкретного блока"""
    try:
        logger.info(f"Export request: block_id={block_id}, data_type={data_type}, format_type={format_type}")
        
        # Получаем данные в зависимости от типа
        data = get_block_report_data(block_id, data_type)
        
        logger.info(f"Retrieved data count: {len(data) if data else 0}")
        
        if not data:
            logger.warning(f"No data available for block {block_id}, type {data_type}")
            return jsonify({'error': 'No data available for export'}), 404
        
        # Преобразуем Decimal в float для JSON
        if format_type == 'json':
            data = convert_decimal_to_float(data)
        
        # Генерируем файл
        if format_type == 'csv':
            return export_csv(data, f"block_{block_id}_{data_type}")
        elif format_type == 'json':
            return export_json(data, f"block_{block_id}_{data_type}")
        elif format_type == 'txt':
            return export_txt(data, f"block_{block_id}_{data_type}")
        else:
            logger.error(f"Unsupported format: {format_type}")
            return jsonify({'error': 'Unsupported format'}), 400
            
    except Exception as e:
        logger.error(f"Block export error: {str(e)}", exc_info=True)
        return jsonify({'error': f'Export failed: {str(e)}'}), 500

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

def get_block_report_data(block_id, data_type):
    """Получение данных для отчетов по конкретному блоку - ИСПРАВЛЕННАЯ ВЕРСИЯ"""
    try:
        logger.info(f"Getting block report data: block_id={block_id}, data_type={data_type}")
        
        if data_type == 'deviations':
            data = get_block_deviations_data(block_id)
        elif data_type == 'boreholes':
            data = get_block_boreholes_data(block_id)
        elif data_type == 'critical':
            data = get_block_critical_deviations_data(block_id)
        else:
            logger.warning(f"Unknown data type: {data_type}")
            data = []
        
        logger.info(f"Retrieved {len(data)} records for {data_type}")
        return data
        
    except Exception as e:
        logger.error(f"Error getting block report data for {block_id}: {str(e)}", exc_info=True)
        return []

def get_block_deviations_data(block_id):
    """Получение данных об отклонениях по блоку - ИСПРАВЛЕННАЯ ВЕРСИЯ"""
    try:
        from app.models.database import db_manager
        
        # Получаем все отклонения (без cursor_factory)
        dist_result = db_manager.execute_function('calc_distance_deviations', (block_id,))
        length_result = db_manager.execute_function('calc_length_deviations', (block_id,))
        diameter_result = db_manager.execute_function('calc_diameter_deviations', (block_id,))
        direction_result = db_manager.execute_function('calc_direction_deviations', (block_id,))
        
        deviations = []
        
        # Обрабатываем отклонения расстояний
        for row in (dist_result or []):
            # Преобразуем в словарь, если это не словарь
            if not isinstance(row, dict):
                # Предполагаем порядок полей: borehole_name, planned_x, planned_y, actual_x, actual_y, deviation
                row_dict = {
                    'borehole_name': row[0] if len(row) > 0 else '',
                    'planned_x': row[1] if len(row) > 1 else None,
                    'planned_y': row[2] if len(row) > 2 else None,
                    'actual_x': row[3] if len(row) > 3 else None,
                    'actual_y': row[4] if len(row) > 4 else None,
                    'deviation': row[5] if len(row) > 5 else None
                }
            else:
                row_dict = row
                
            deviations.append({
                'borehole_name': str(row_dict.get('borehole_name', '')),
                'type': 'distance',
                'planned_x': safe_float(row_dict.get('planned_x')),
                'planned_y': safe_float(row_dict.get('planned_y')),
                'actual_x': safe_float(row_dict.get('actual_x')),
                'actual_y': safe_float(row_dict.get('actual_y')),
                'deviation': safe_float(row_dict.get('deviation'))
            })
        
        # Обрабатываем отклонения длины
        for row in (length_result or []):
            if not isinstance(row, dict):
                # Предполагаем порядок: borehole_name, planned_length, actual_length, length_diff
                row_dict = {
                    'borehole_name': row[0] if len(row) > 0 else '',
                    'planned_length': row[1] if len(row) > 1 else None,
                    'actual_length': row[2] if len(row) > 2 else None,
                    'length_diff': row[3] if len(row) > 3 else None
                }
            else:
                row_dict = row
                
            deviations.append({
                'borehole_name': str(row_dict.get('borehole_name', '')),
                'type': 'length',
                'planned': safe_float(row_dict.get('planned_length')),
                'actual': safe_float(row_dict.get('actual_length')),
                'deviation': safe_float(row_dict.get('length_diff'))
            })
        
        # Обрабатываем отклонения диаметра
        for row in (diameter_result or []):
            if not isinstance(row, dict):
                # Предполагаем порядок: borehole_name, planned_diameter, actual_diameter, diameter_diff
                row_dict = {
                    'borehole_name': row[0] if len(row) > 0 else '',
                    'planned_diameter': row[1] if len(row) > 1 else None,
                    'actual_diameter': row[2] if len(row) > 2 else None,
                    'diameter_diff': row[3] if len(row) > 3 else None
                }
            else:
                row_dict = row
                
            deviations.append({
                'borehole_name': str(row_dict.get('borehole_name', '')),
                'type': 'diameter',
                'planned': safe_float(row_dict.get('planned_diameter')),
                'actual': safe_float(row_dict.get('actual_diameter')),
                'deviation': safe_float(row_dict.get('diameter_diff'))
            })
        
        # Обрабатываем отклонения направления
        for row in (direction_result or []):
            if not isinstance(row, dict):
                # Предполагаем порядок: borehole_name, planned_angle, actual_angle, angle_diff, planned_azimuth, actual_azimuth, azimuth_diff
                row_dict = {
                    'borehole_name': row[0] if len(row) > 0 else '',
                    'planned_angle': row[1] if len(row) > 1 else None,
                    'actual_angle': row[2] if len(row) > 2 else None,
                    'angle_diff': row[3] if len(row) > 3 else None,
                    'planned_azimuth': row[4] if len(row) > 4 else None,
                    'actual_azimuth': row[5] if len(row) > 5 else None,
                    'azimuth_diff': row[6] if len(row) > 6 else None
                }
            else:
                row_dict = row
                
            deviations.append({
                'borehole_name': str(row_dict.get('borehole_name', '')),
                'type': 'direction',
                'angle_planned': safe_float(row_dict.get('planned_angle')),
                'angle_actual': safe_float(row_dict.get('actual_angle')),
                'angle_deviation': safe_float(row_dict.get('angle_diff')),
                'azimuth_planned': safe_float(row_dict.get('planned_azimuth')),
                'azimuth_actual': safe_float(row_dict.get('actual_azimuth')),
                'azimuth_deviation': safe_float(row_dict.get('azimuth_diff'))
            })
        
        logger.info(f"Retrieved {len(deviations)} deviations for block {block_id}")
        return deviations
        
    except Exception as e:
        logger.error(f"Error getting block deviations data: {str(e)}", exc_info=True)
        return []

    
def get_block_boreholes_data(block_id):
    """Получение данных о скважинах блока - ИСПРАВЛЕННАЯ ВЕРСИЯ"""
    try:
        from app.models.database import db_manager
        
        result = db_manager.execute_query("""
            SELECT 
                "Name" as borehole_name,
                "X" as x,
                "Y" as y,
                "Z" as z,
                "Length" as length,
                "Diameter" as diameter,
                "Angle" as angle,
                "Azimuth" as azimuth,
                "T" as type
            FROM public."Boreholes"
            WHERE "BlockID" = %s
            ORDER BY "Name"
        """, (block_id,), cursor_factory=RealDictCursor)
        
        boreholes = [dict(row) for row in result] if result else []
        logger.info(f"Retrieved {len(boreholes)} boreholes for block {block_id}")
        return boreholes
        
    except Exception as e:
        logger.error(f"Error getting block boreholes data: {str(e)}", exc_info=True)
        return []

def get_block_critical_deviations_data(block_id):
    """Получение данных о критических отклонениях - ИСПРАВЛЕННАЯ ВЕРСИЯ"""
    try:
        from app.models.database import db_manager
        
        # Получаем все отклонения и фильтруем критические
        deviations = []
        
        # Критические отклонения расстояний (> 5м)
        dist_result = db_manager.execute_function('calc_distance_deviations', (block_id,))
        for row in (dist_result or []):
            if not isinstance(row, dict):
                deviation = safe_float(row[5] if len(row) > 5 else None)
            else:
                deviation = safe_float(row.get('deviation'))
                
            if deviation and abs(deviation) > 5:
                deviations.append({
                    'borehole_name': str(row[0] if not isinstance(row, dict) else row.get('borehole_name', '')),
                    'type': 'distance',
                    'deviation': deviation,
                    'threshold': 5,
                    'is_critical': True
                })
        
        # Критические отклонения длины (> 10%)
        length_result = db_manager.execute_function('calc_length_deviations', (block_id,))
        for row in (length_result or []):
            if not isinstance(row, dict):
                planned = safe_float(row[1] if len(row) > 1 else None)
                diff = safe_float(row[3] if len(row) > 3 else None)
            else:
                planned = safe_float(row.get('planned_length'))
                diff = safe_float(row.get('length_diff'))
                
            if planned and diff:
                percent_deviation = abs(diff / planned) * 100
                if percent_deviation > 10:
                    deviations.append({
                        'borehole_name': str(row[0] if not isinstance(row, dict) else row.get('borehole_name', '')),
                        'type': 'length',
                        'deviation': diff,
                        'planned': planned,
                        'percent_deviation': round(percent_deviation, 1),
                        'threshold': '10%',
                        'is_critical': True
                    })
        
        # Критические отклонения диаметра (> 10%)
        diameter_result = db_manager.execute_function('calc_diameter_deviations', (block_id,))
        for row in (diameter_result or []):
            if not isinstance(row, dict):
                planned = safe_float(row[1] if len(row) > 1 else None)
                diff = safe_float(row[3] if len(row) > 3 else None)
            else:
                planned = safe_float(row.get('planned_diameter'))
                diff = safe_float(row.get('diameter_diff'))
                
            if planned and diff:
                percent_deviation = abs(diff / planned) * 100
                if percent_deviation > 10:
                    deviations.append({
                        'borehole_name': str(row[0] if not isinstance(row, dict) else row.get('borehole_name', '')),
                        'type': 'diameter',
                        'deviation': diff,
                        'planned': planned,
                        'percent_deviation': round(percent_deviation, 1),
                        'threshold': '10%',
                        'is_critical': True
                    })
        
        # Критические отклонения направления
        direction_result = db_manager.execute_function('calc_direction_deviations', (block_id,))
        for row in (direction_result or []):
            if not isinstance(row, dict):
                angle_diff = safe_float(row[3] if len(row) > 3 else None)
                azimuth_diff = safe_float(row[6] if len(row) > 6 else None)
            else:
                angle_diff = safe_float(row.get('angle_diff'))
                azimuth_diff = safe_float(row.get('azimuth_diff'))
            
            # Угол наклона (> 5 градусов)
            if angle_diff and abs(angle_diff) > 5:
                deviations.append({
                    'borehole_name': str(row[0] if not isinstance(row, dict) else row.get('borehole_name', '')),
                    'type': 'angle',
                    'deviation': angle_diff,
                    'threshold': '5°',
                    'is_critical': True
                })
            
            # Азимут (> 10 градусов)
            if azimuth_diff and abs(azimuth_diff) > 10:
                deviations.append({
                    'borehole_name': str(row[0] if not isinstance(row, dict) else row.get('borehole_name', '')),
                    'type': 'azimuth',
                    'deviation': azimuth_diff,
                    'threshold': '10°',
                    'is_critical': True
                })
        
        logger.info(f"Found {len(deviations)} critical deviations for block {block_id}")
        return deviations
        
    except Exception as e:
        logger.error(f"Error getting block critical deviations data: {str(e)}", exc_info=True)
        return []