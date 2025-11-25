# boreholes.py
from flask import Blueprint, render_template, jsonify
import logging
from dotenv import load_dotenv
from psycopg2 import sql
from psycopg2.extras import RealDictCursor

# Импортируем DatabaseManager
from app.models.database import db_manager

boreholes_bp = Blueprint('boreholes', __name__)

# Настройка логирования
logger = logging.getLogger(__name__)

# Загрузка переменных окружения
load_dotenv(dotenv_path='config.env')

@boreholes_bp.route('/borehole/<block_id>/<borehole_name>')
def get_borehole_details_data(block_id, borehole_name):
    """Полная реализация страницы деталей скважины"""
    try:
        # Используем DatabaseManager для выполнения запросов
        dist_result = db_manager.execute_query("""
            SELECT * FROM public.calc_distance_deviations(%s) 
            WHERE borehole_name = %s
        """, (block_id, borehole_name), cursor_factory=RealDictCursor)
        
        length_result = db_manager.execute_query("""
            SELECT * FROM public.calc_length_deviations(%s) 
            WHERE borehole_name = %s
        """, (block_id, borehole_name), cursor_factory=RealDictCursor)
        
        diameter_result = db_manager.execute_query("""
            SELECT * FROM public.calc_diameter_deviations(%s) 
            WHERE borehole_name = %s
        """, (block_id, borehole_name), cursor_factory=RealDictCursor)
        
        direction_result = db_manager.execute_query("""
            SELECT * FROM public.calc_direction_deviations(%s) 
            WHERE borehole_name = %s
        """, (block_id, borehole_name), cursor_factory=RealDictCursor)

        # Безопасное извлечение данных из результата запроса
        def safe_get(data_list, field_name, default=None):
            """Безопасно получает значение из списка данных по имени поля"""
            if data_list and len(data_list) > 0:
                value = data_list[0].get(field_name)
                return value if value is not None else default
            return default

        # Определяем структуру полей для каждой функции
        # На основе структуры возвращаемых данных из БД функций
        
        # Форматирование данных скважины с безопасным доступом
        borehole_data = {
            'name': borehole_name,
            'dist': {
                'planned': (safe_get(dist_result, 'planned_x', 0), safe_get(dist_result, 'planned_y', 0)),
                'actual': (safe_get(dist_result, 'actual_x', 0), safe_get(dist_result, 'actual_y', 0)),
                'deviation': safe_get(dist_result, 'deviation', 0)
            } if dist_result and len(dist_result) > 0 else None,
            'length': {
                'planned': float(safe_get(length_result, 'planned_length', 0)),
                'actual': float(safe_get(length_result, 'actual_length', 0)),
                'diff': float(safe_get(length_result, 'length_diff', 0)),
                'useful_planned': safe_get(length_result, 'useful_length_planned'),
                'useful_actual': safe_get(length_result, 'useful_length_actual'),
                'useful_diff': safe_get(length_result, 'useful_length_diff')
            } if length_result and len(length_result) > 0 else None,
            'diameter': {
                'planned': float(safe_get(diameter_result, 'planned_diameter', 0)),
                'actual': float(safe_get(diameter_result, 'actual_diameter', 0)),
                'diff': float(safe_get(diameter_result, 'diameter_diff', 0)),
                'overboring_planned': safe_get(diameter_result, 'overboring_planned'),
                'overboring_actual': safe_get(diameter_result, 'overboring_actual'),
                'overboring_diff': safe_get(diameter_result, 'overboring_diff')
            } if diameter_result and len(diameter_result) > 0 else None,
            'direction': {
                'angle_planned': safe_get(direction_result, 'planned_angle'),
                'angle_actual': safe_get(direction_result, 'actual_angle'),
                'angle_diff': safe_get(direction_result, 'angle_diff'),
                'azimuth_planned': safe_get(direction_result, 'planned_azimuth'),
                'azimuth_actual': safe_get(direction_result, 'actual_azimuth'),
                'azimuth_diff': safe_get(direction_result, 'azimuth_diff')
            } if direction_result and len(direction_result) > 0 else None
        }

        logger.info(f"Borehole details successfully loaded: {borehole_name} in block {block_id}")

        # Для отладки выведем структуру данных
        logger.info(f"Dist result keys: {list(dist_result[0].keys()) if dist_result and len(dist_result) > 0 else 'No data'}")
        logger.info(f"Length result keys: {list(length_result[0].keys()) if length_result and len(length_result) > 0 else 'No data'}")
        logger.info(f"Diameter result keys: {list(diameter_result[0].keys()) if diameter_result and len(diameter_result) > 0 else 'No data'}")
        logger.info(f"Direction result keys: {list(direction_result[0].keys()) if direction_result and len(direction_result) > 0 else 'No data'}")

        return render_template('borehole.html',
                           block_id=block_id,
                           borehole=borehole_data)

    except Exception as e:
        logger.error(f"Error loading borehole details for {borehole_name} in block {block_id}: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        
        # Возвращаем шаблон с сообщением об ошибке
        return render_template('borehole.html',
                           block_id=block_id,
                           borehole={'name': borehole_name},
                           error_message=f"Ошибка загрузки данных: {str(e)}")

@boreholes_bp.route('/api/block/<block_id>/boreholes', methods=['GET'])
def get_boreholes_3D(block_id):
    """Получение данных о скважинах для 3D визуализации"""
    try:
        result = db_manager.execute_query(
            sql.SQL("SELECT * FROM public.\"Boreholes3D\" WHERE \"BlockID\" = {}").format(sql.Placeholder()), 
            (block_id,),
            cursor_factory=RealDictCursor
        )
        
        if result:
            for hole in result:
                for field in ['X', 'Y', 'Z', 'Length', 'Diameter', 'Angle', 'Azimuth']:
                    if hole[field] is None:
                        hole[field] = 0.0
            
            return jsonify(result)
        return jsonify([])
    except Exception as e:
        logger.error(f"Error loading 3D boreholes data for block {block_id}: {str(e)}")
        return jsonify({'error': str(e)}), 500

@boreholes_bp.route('/api/block/<block_id>/relief', methods=['GET'])
def get_relief_3D(block_id):
    """Получение данных о рельефе для 3D визуализации"""
    try:
        items_result = db_manager.execute_query(
            sql.SQL("SELECT \"ItemID\", \"TID\", \"Z_Level\" FROM public.\"ReliefItems\" WHERE \"BlockID\" = {}").format(sql.Placeholder()),
            (block_id,),
            cursor_factory=RealDictCursor
        )
        
        if not items_result:
            return jsonify([])
        
        items = []
        for item in items_result:
            points_result = db_manager.execute_query(
                sql.SQL("SELECT \"X\", \"Y\", \"Z\" FROM public.\"ReliefPoints\" WHERE \"ReliefItemID\" = {} ORDER BY \"PointOrder\"").format(sql.Placeholder()),
                (item['ItemID'],),
                cursor_factory=RealDictCursor
            )
            item['points'] = points_result if points_result else []
            items.append(item)

        return jsonify(items)
    except Exception as e:
        logger.error(f"Error loading relief data for block {block_id}: {str(e)}")
        return jsonify({'error': str(e)}), 500