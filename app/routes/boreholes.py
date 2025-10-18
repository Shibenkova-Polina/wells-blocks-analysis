# boreholes.py
from flask import Blueprint, render_template, jsonify, request
import logging
import os
from dotenv import load_dotenv
import psycopg2
from psycopg2 import sql
from psycopg2.extras import RealDictCursor

boreholes_bp = Blueprint('boreholes', __name__)

# Настройка логирования
logger = logging.getLogger(__name__)

# Загрузка переменных окружения
load_dotenv(dotenv_path='config.env')

def get_db_connection():
    """Функция подключения к БД как в app.py"""
    return psycopg2.connect(
        host=os.getenv('DB_HOST'),
        database=os.getenv('DB_NAME'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD'),
        port=os.getenv('DB_PORT', '5432')
    )

@boreholes_bp.route('/borehole/<block_id>/<borehole_name>')
def get_borehole_details_data(block_id, borehole_name):
    """Полная реализация страницы деталей скважины - как в app.py"""
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Получение данных об отклонениях расстояния
        dist_query = sql.SQL("""
            SELECT * FROM public.calc_distance_deviations({}) 
            WHERE borehole_name = {}
        """).format(sql.Placeholder(), sql.Placeholder())
        cursor.execute(dist_query, (block_id, borehole_name))
        dist_data = cursor.fetchone()

        # Получение данных об отклонениях глубины
        length_query = sql.SQL("""
            SELECT * FROM public.calc_length_deviations({}) 
            WHERE borehole_name = {}
        """).format(sql.Placeholder(), sql.Placeholder())
        cursor.execute(length_query, (block_id, borehole_name))
        length_data = cursor.fetchone()

        # Получение данных об отклонениях диаметра
        diameter_query = sql.SQL("""
            SELECT * FROM public.calc_diameter_deviations({}) 
            WHERE borehole_name = {}
        """).format(sql.Placeholder(), sql.Placeholder())
        cursor.execute(diameter_query, (block_id, borehole_name))
        diameter_data = cursor.fetchone()

        # Получение данных об отклонениях направления
        direction_query = sql.SQL("""
            SELECT * FROM public.calc_direction_deviations({}) 
            WHERE borehole_name = {}
        """).format(sql.Placeholder(), sql.Placeholder())
        cursor.execute(direction_query, (block_id, borehole_name))
        direction_data = cursor.fetchone()

        cursor.close()
        conn.close()

        # Форматирование данных скважины как в app.py
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

        logger.info(f"Borehole details successfully loaded: {borehole_name} in block {block_id}")

        return render_template('borehole.html',
                           block_id=block_id,
                           borehole=borehole_data)

    except Exception as e:
        logger.error(f"Error loading borehole details for {borehole_name} in block {block_id}: {str(e)}")
        if cursor:
            cursor.close()
        if conn:
            conn.close()
        return render_template('error.html', error_message=str(e)), 500

@boreholes_bp.route('/api/block/<block_id>/boreholes', methods=['GET'])
def get_boreholes_3D(block_id):
    """Получение данных о скважинах для 3D визуализации - как в app.py"""
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        cursor.execute(sql.SQL("""
            SELECT * FROM public."Boreholes3D" 
            WHERE "BlockID" = {}
        """).format(sql.Placeholder()), (block_id,))

        boreholes = cursor.fetchall()
        for hole in boreholes:
            for field in ['X', 'Y', 'Z', 'Length', 'Diameter', 'Angle', 'Azimuth']:
                if hole[field] is None:
                    hole[field] = 0.0
        
        cursor.close()
        conn.close()
        return jsonify(boreholes)
    
    except Exception as e:
        logger.error(f"Error loading 3D boreholes data for block {block_id}: {str(e)}")
        if cursor:
            cursor.close()
        if conn:
            conn.close()
        return jsonify({'error': str(e)}), 500

@boreholes_bp.route('/api/block/<block_id>/relief', methods=['GET'])
def get_relief_3D(block_id):
    """Получение данных о рельефе для 3D визуализации - как в app.py"""
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        cursor.execute(sql.SQL("""
            SELECT "ItemID", "TID", "Z_Level" FROM public."ReliefItems"
            WHERE "BlockID" = {}
        """).format(sql.Placeholder()), (block_id,))
        
        items = cursor.fetchall() 
        for item in items:
            cursor.execute(sql.SQL("""
                SELECT "X", "Y", "Z" FROM public."ReliefPoints" 
                WHERE "ReliefItemID" = {}
                ORDER BY "PointOrder"
            """).format(sql.Placeholder()), (item['ItemID'],))
            item['points'] = cursor.fetchall()
        
        cursor.close()
        conn.close()
        print('------------------------')
        print(items)
        return jsonify(items)
    
    except Exception as e:
        logger.error(f"Error loading relief data for block {block_id}: {str(e)}")
        if cursor:
            cursor.close()
        if conn:
            conn.close()
        return jsonify({'error': str(e)}), 500