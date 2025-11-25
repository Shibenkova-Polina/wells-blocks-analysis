from flask import Blueprint, render_template, request, jsonify, redirect
import json
import logging
import os
from dotenv import load_dotenv
from psycopg2 import sql
from psycopg2.extras import RealDictCursor
from decimal import Decimal

# Импортируем DatabaseManager
from app.models.database import db_manager

# Настройка логирования
logger = logging.getLogger(__name__)

blocks_bp = Blueprint('blocks', __name__)

# Загрузка переменных окружения
load_dotenv(dotenv_path='config.env')

def get_db_connection():
    """Функция подключения к БД через DatabaseManager"""
    return db_manager.get_connection()

def safe_float(value, default=0.0):
    """Безопасное преобразование в float"""
    if value is None:
        return default
    try:
        return float(value)
    except (ValueError, TypeError):
        return default

def safe_int(value, default=0):
    """Безопасное преобразование в int"""
    if value is None:
        return default
    try:
        return int(value)
    except (ValueError, TypeError):
        return default

def safe_convert_value(value):
    """Безопасное преобразование значения в Python тип"""
    if value is None:
        return None
    
    # Обработка Decimal
    if isinstance(value, Decimal):
        return float(value)
    
    # Обработка других числовых типов
    try:
        return float(value)
    except (TypeError, ValueError):
        pass
    
    # Обработка строк и других типов
    return str(value) if value is not None else None

@blocks_bp.route('/dashboard', methods=['GET', 'POST'])
def get_dashboard_data():
    """Полная реализация дашборда блока"""
    try:
        # Получение входных данных
        if request.method == 'POST':
            block_input = request.form.get('block_input', '').strip()
        else:
            block_input = request.args.get('block_input', '').strip()
        
        if not block_input:
            logger.warning("Empty block input received")
            return redirect('/borehole-analytics')
        
        # Используем DatabaseManager для получения соединения
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()

            # Определение block_id и block_name
            block_id, block_name = None, None
            
            if not '_' in block_input:
                # Поиск по ID блока
                block_id = block_input
                cursor.execute(sql.SQL("""
                        SELECT "BlockName" FROM public."BlockInfo"
                        WHERE "BlockID" = {}
                    """).format(sql.Placeholder()), (block_id,))
                result = cursor.fetchone()

                if not result:
                    logger.warning(f"Block not found by ID: {block_input}")
                    return redirect('/borehole-analytics')
                
                block_name = result[0]
            else:
                # Поиск по названию блока
                cursor.execute(sql.SQL("""
                        SELECT "BlockID", "BlockName" FROM public."BlockInfo"
                        WHERE "BlockName" = {}
                    """).format(sql.Placeholder()), (block_input,))
                result = cursor.fetchone()

                if not result:
                    logger.warning(f"Block not found by name: {block_input}")
                    return redirect('/borehole-analytics')
                
                block_id = result[0]
                block_name = result[1]

            logger.info(f"Loading dashboard data for block {block_id} ({block_name})")
            
            # Общий отчет по блоку
            cursor.execute(sql.SQL("SELECT * FROM public.generate_report({})").format(
                sql.Placeholder()
            ), (block_id,))
            report_data = cursor.fetchall()

            # Список скважин блока
            query = sql.SQL("""
                SELECT 
                    b."Name" as name,
                    EXISTS (
                        SELECT 1 
                        FROM public."Boreholes" a 
                        WHERE a."BlockID" = b."BlockID"
                        AND a."Name" = b."Name" 
                        AND a."T" = 3
                    ) as active
                FROM public."Boreholes" b
                WHERE b."BlockID" = {}
                GROUP BY b."Name", b."BlockID"
                ORDER BY b."Name"
            """).format(sql.Placeholder())
            cursor.execute(query, (block_id,))
            boreholes_result = cursor.fetchall()
            boreholes = [{'name': row[0], 'active': row[1]} for row in boreholes_result]

            logger.info(f"Found {len(boreholes)} boreholes for block {block_id}")
            
            # Данные для графиков отклонений
            cursor.execute(sql.SQL("SELECT * FROM public.calc_distance_deviations({})").format(
                sql.Placeholder()
            ), (block_id,))
            dist_deviations = cursor.fetchall()

            cursor.execute(sql.SQL("SELECT * FROM public.calc_length_deviations({})").format(
                sql.Placeholder()
            ), (block_id,))
            length_deviations = cursor.fetchall()

            cursor.execute(sql.SQL("SELECT * FROM public.calc_diameter_deviations({})").format(
                sql.Placeholder()
            ), (block_id,))
            diameter_deviations = cursor.fetchall()

            cursor.execute(sql.SQL("SELECT * FROM public.calc_direction_deviations({})").format(
                sql.Placeholder()
            ), (block_id,))
            direction_deviations = cursor.fetchall()

            # Данные для буровой сетки
            cursor.execute(sql.SQL("""
                SELECT 
                    CASE WHEN "T" = 2 THEN "X" ELSE NULL END as planned_x,
                    CASE WHEN "T" = 2 THEN "Y" ELSE NULL END as planned_y,
                    CASE WHEN "T" = 3 THEN "X" ELSE NULL END as actual_x,
                    CASE WHEN "T" = 3 THEN "Y" ELSE NULL END as actual_y,
                    "Name" as borehole_name
                FROM public."Boreholes"
                WHERE "BlockID" = {}
            """).format(sql.Placeholder()), (block_id,))
            grid_data = cursor.fetchall()

        # Обработка данных для графиков - исправленная версия
        charts_data = {
            'dist_deviations': [],
            'length_deviations': [],
            'diameter_deviations': [],
            'angle_deviations': [],
            'azimuth_deviations': []
        }

        # Обработка отклонений расстояний
        for row in dist_deviations:
            if len(row) > 5 and row[0] and row[5] is not None:
                charts_data['dist_deviations'].append({
                    'name': str(row[0]),
                    'deviation': safe_float(row[5])
                })

        # Обработка отклонений длины
        for row in length_deviations:
            if len(row) > 3 and row[0] and row[3] is not None:
                charts_data['length_deviations'].append({
                    'name': str(row[0]),
                    'diff': safe_float(row[3])
                })

        # Обработка отклонений диаметра
        for row in diameter_deviations:
            if len(row) > 3 and row[0] and row[3] is not None:
                charts_data['diameter_deviations'].append({
                    'name': str(row[0]),
                    'diff': safe_float(row[3])
                })

        # Обработка отклонений направления
        for row in direction_deviations:
            if len(row) > 3 and row[0]:
                if row[3] is not None:  # angle_diff
                    charts_data['angle_deviations'].append({
                        'name': str(row[0]),
                        'diff': safe_float(row[3])
                    })
                if len(row) > 6 and row[6] is not None:  # azimuth_diff
                    charts_data['azimuth_deviations'].append({
                        'name': str(row[0]),
                        'diff': safe_float(row[6])
                    })

        # Выявление критических отклонений
        critical_deviations = {
            'dist': [],
            'length': [],
            'diameter': [],
            'angle': [],
            'azimuth': []
        }

        # отклонение > 5м
        for row in dist_deviations:
            if len(row) > 5 and row[5] and float(row[5]) > 5:
                critical_deviations['dist'].append({
                    'name': row[0],
                    'deviation': float(row[5])
                })

        # разница > 10%
        for row in length_deviations:
            if len(row) > 3 and row[1] and row[2] and row[3] and abs(float(row[3])) > float(row[1]) * 0.1:
                critical_deviations['length'].append({
                    'name': row[0],
                    'diff': float(row[3]),
                    'percent': round(abs(float(row[3])) / float(row[1]) * 100, 1)
                })

        for row in diameter_deviations:
            if len(row) > 3 and row[1] and row[2] and row[3] and abs(float(row[3])) > float(row[1]) * 0.1:
                critical_deviations['diameter'].append({
                    'name': row[0],
                    'diff': float(row[3]),
                    'percent': round(abs(float(row[3])) / float(row[1]) * 100, 1)
                })

        for row in direction_deviations:
            if len(row) > 3 and row[1] and row[2] and row[3] and abs(float(row[3])) > float(row[1]) * 0.1:
                critical_deviations['angle'].append({
                    'name': row[0],
                    'diff': float(row[3]),
                    'percent': round(abs(float(row[3])) / float(row[1]) * 100, 1)
                })

        for row in direction_deviations:
            if len(row) > 6 and row[4] and row[5] and row[6] is not None:
                azimuth_diff = float(row[6])
                planned_azimuth = float(row[4])
                if azimuth_diff > planned_azimuth * 0.1 or azimuth_diff > (360 - planned_azimuth) * 0.1:
                    critical_deviations['azimuth'].append({
                        'name': row[0],
                        'diff': azimuth_diff,
                        'percent': round(azimuth_diff / planned_azimuth * 100, 1) if planned_azimuth != 0 else 0
                    })

        logger.info(f"critical_deviations: {critical_deviations}")

        # Получение информации о блоке
        block_info = get_block_info(block_id)

        # Подготовка данных сетки
        planned_grid = [{'x': row[0], 'y': row[1], 'name': row[4]} for row in grid_data if row[0] is not None]
        actual_grid = [{'x': row[2], 'y': row[3], 'name': row[4]} for row in grid_data if row[2] is not None]

        # Логирование успешной загрузки
        logger.info(f"Dashboard data successfully loaded for block {block_id}")

        # Рендеринг шаблона
        return render_template('dashboard.html',
                            block_id=block_id,
                            block_name=block_name,
                            report_data=report_data,
                            boreholes=boreholes,
                            charts_data=json.dumps(charts_data, default=str),
                            critical_deviations=json.dumps(critical_deviations, default=str),
                            block_info=block_info,
                            planned_grid_data=json.dumps(planned_grid, default=str),
                            actual_grid_data=json.dumps(actual_grid, default=str))
    
    except Exception as e:
        logger.error(f"Error loading dashboard data: {str(e)}")
        return redirect('/borehole-analytics')

def get_block_info(block_id):
    """Получение информации о блоке"""
    try:
        logger.info(f"Getting block info for block_id: {block_id}")
        
        result = db_manager.execute_query(
            sql.SQL("""
                SELECT 
                    "CrushEnergy", "HolesSpace", "RowsDistance", 
                    "RockName", "RockRigity", "RockDensity"
                FROM public."BlockInfo"
                WHERE "BlockID" = {}
            """).format(sql.Placeholder()), 
            (block_id,),
            cursor_factory=RealDictCursor  # Убедитесь, что используем RealDictCursor
        )
        
        logger.info(f"Query result: {result}")
        
        if result and len(result) > 0:
            row = result[0]
            logger.info(f"Raw row data: {row}")
            logger.info(f"Row keys: {list(row.keys())}")
            
            # Обращаемся к полям по имени, а не по индексу
            crush_energy = safe_float(row.get('CrushEnergy'))
            holes_space = safe_float(row.get('HolesSpace'))
            rows_distance = safe_float(row.get('RowsDistance'))
            rock_name = row.get('RockName', "Не указано")
            rock_rigidity = row.get('RockRigity', "Не указано")
            rock_density = safe_float(row.get('RockDensity'))
            
            logger.info(f"Processed data - crush_energy: {crush_energy}, holes_space: {holes_space}, rows_distance: {rows_distance}, rock_density: {rock_density}")
            
            return {
                'crush_energy': crush_energy,
                'default_hole_space': holes_space,
                'default_row_distance': rows_distance,
                'rock_name': rock_name,
                'rock_rigidity': rock_rigidity,
                'rock_density': rock_density
            }
        else:
            logger.warning(f"No block info found for block_id: {block_id}")
            return {}
            
    except Exception as e:
        logger.error(f"Error getting block info for {block_id}: {str(e)}")
        logger.error(f"Error type: {type(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return {}

# Дополнительные маршруты для 3D визуализации
@blocks_bp.route('/api/block/<block_id>/info', methods=['GET'])
def get_block_info_3d(block_id):
    try:
        result = db_manager.execute_query(
            sql.SQL("SELECT * FROM public.\"BlockInfo\" WHERE \"BlockID\" = {}").format(sql.Placeholder()), 
            (block_id,),
            cursor_factory=RealDictCursor
        )
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error getting block info 3D: {e}")
        return jsonify({'error': str(e)}), 500

@blocks_bp.route('/borehole/<block_id>/<borehole_name>')
def get_borehole_details_data(block_id, borehole_name):
    try:
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()

            dist_query = sql.SQL("""
                SELECT * FROM public.calc_distance_deviations({}) 
                WHERE borehole_name = {}
            """).format(sql.Placeholder(), sql.Placeholder())
            cursor.execute(dist_query, (block_id, borehole_name))
            dist_data = cursor.fetchone()

            length_query = sql.SQL("""
                SELECT * FROM public.calc_length_deviations({}) 
                WHERE borehole_name = {}
            """).format(sql.Placeholder(), sql.Placeholder())
            cursor.execute(length_query, (block_id, borehole_name))
            length_data = cursor.fetchone()

            diameter_query = sql.SQL("""
                SELECT * FROM public.calc_diameter_deviations({}) 
                WHERE borehole_name = {}
            """).format(sql.Placeholder(), sql.Placeholder())
            cursor.execute(diameter_query, (block_id, borehole_name))
            diameter_data = cursor.fetchone()

            direction_query = sql.SQL("""
                SELECT * FROM public.calc_direction_deviations({}) 
                WHERE borehole_name = {}
            """).format(sql.Placeholder(), sql.Placeholder())
            cursor.execute(direction_query, (block_id, borehole_name))
            direction_data = cursor.fetchone()

        borehole_data = {
            'name': borehole_name,
            'dist': {
                'planned': (dist_data[1], dist_data[2]),
                'actual': (dist_data[3], dist_data[4]),
                'deviation': dist_data[5]
            } if dist_data else None,
            'length': {
                'planned':  float(length_data[1]),
                'actual':  float(length_data[2]),
                'diff':  float(length_data[3]),
                'useful_planned': length_data[4],
                'useful_actual': length_data[5],
                'useful_diff': length_data[6]
            } if length_data else None,
            'diameter': {
                'planned':  float(diameter_data[1]),
                'actual':  float(diameter_data[2]),
                'diff':  float(diameter_data[3]),
                'overboring_planned': diameter_data[4],
                'overboring_actual': diameter_data[5],
                'overboring_diff': diameter_data[6]
            } if diameter_data else None,
            'direction': {
                'angle_planned': direction_data[1],
                'angle_actual': direction_data[2],
                'angle_diff': direction_data[3],
                'azimuth_planned': direction_data[4],
                'azimuth_actual': direction_data[5],
                'azimuth_diff': direction_data[6]
            } if direction_data else None
        }

        return render_template('borehole.html',
                           block_id=block_id,
                           borehole=borehole_data)
    except Exception as e:
        logger.error(f"Error getting borehole details: {e}")
        return jsonify({'error': str(e)}), 500