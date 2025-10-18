# analytics.py
from flask import Blueprint, jsonify, request
import logging
import os
from dotenv import load_dotenv
import psycopg2
from psycopg2 import sql
from decimal import Decimal

analytics_bp = Blueprint('analytics', __name__)

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

@analytics_bp.route('/api/blocks/progress')
def get_blocks_progress():
    """Прогресс по блокам - как в app.py"""
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT * FROM calculate_blocks_progress()")
        result = cur.fetchone()
        
        return jsonify({
            'total_blocks': result[0],
            'drilled_blocks': result[1],
            'percent_drilled': float(result[2]) if result[2] is not None else 0.0
        })
    except Exception as e:
        logger.error(f"Error in get_blocks_progress: {str(e)}")
        return jsonify({'error': str(e)}), 500
    finally:
        cur.close()
        conn.close()

@analytics_bp.route('/api/blocks/drilling_progress')
def get_drilling_progress():
    """Прогресс бурения по блокам - как в app.py"""
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            SELECT * FROM calculate_drilling_progress() 
            WHERE block_name IS NOT NULL AND total_holes_actual > 0
            ORDER BY percent_drilled_actual DESC
        """)
        columns = [desc[0] for desc in cur.description]
        results = []
        for row in cur.fetchall():
            row_dict = dict(zip(columns, row))
            # Преобразуем Decimal в float для JSON сериализации
            row_dict['percent_drilled_actual'] = float(row_dict['percent_drilled_actual']) if row_dict['percent_drilled_actual'] is not None else 0.0
            row_dict['percent_drilled_planned'] = float(row_dict['percent_drilled_planned']) if row_dict['percent_drilled_planned'] is not None else 0.0
            results.append(row_dict)
        
        return jsonify(results)
    except Exception as e:
        logger.error(f"Error in get_drilling_progress: {str(e)}")
        return jsonify({'error': str(e)}), 500
    finally:
        cur.close()
        conn.close()

@analytics_bp.route('/api/rigs/productivity')
def get_rig_productivity():
    """Производительность станков - как в app.py"""
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT * FROM calculate_rig_productivity_by_block()")
        columns = [desc[0] for desc in cur.description]
        results = []
        for row in cur.fetchall():
            row_dict = dict(zip(columns, row))
            # Преобразуем числовые значения
            for key in ['total_depth', 'drill_hours', 'performance_m_per_shift']:
                if row_dict[key] is not None:
                    row_dict[key] = float(row_dict[key])
            results.append(row_dict)
        
        return jsonify(results)
    except Exception as e:
        logger.error(f"Error in get_rig_productivity: {str(e)}")
        return jsonify({'error': str(e)}), 500
    finally:
        cur.close()
        conn.close()

@analytics_bp.route('/api/rigs/models')
def get_rig_models_productivity():
    """Производительность по моделям станков - как в app.py"""
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT * FROM calculate_rig_model_productivity()")
        columns = [desc[0] for desc in cur.description]
        results = []
        for row in cur.fetchall():
            results.append(dict(zip(columns, row)))
        
        return jsonify(results)
    except Exception as e:
        logger.error(f"Error in get_rig_models_productivity: {str(e)}")
        return jsonify({'error': str(e)}), 500
    finally:
        cur.close()
        conn.close()

@analytics_bp.route('/api/blocks/remaining_shifts')
def get_remaining_shifts():
    """Оставшиеся смены по блокам - как в app.py"""
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT * FROM calculate_remaining_shifts_by_block()")
        columns = [desc[0] for desc in cur.description]
        results = []
        for row in cur.fetchall():
            row_dict = dict(zip(columns, row))
            if row_dict['remaining_shifts'] is not None:
                row_dict['remaining_shifts'] = float(row_dict['remaining_shifts'])
            results.append(row_dict)
        
        return jsonify(results)
    except Exception as e:
        logger.error(f"Error in get_remaining_shifts: {str(e)}")
        return jsonify({'error': str(e)}), 500
    finally:
        cur.close()
        conn.close()

@analytics_bp.route('/api/blocks/efficiency')
def get_blocks_efficiency():
    """Эффективность бурения по блокам - как в app.py"""
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT * FROM calculate_drilling_efficiency_by_block()")
        columns = [desc[0] for desc in cur.description]
        results = []
        for row in cur.fetchall():
            row_dict = dict(zip(columns, row))
            if row_dict['efficiency_percent'] is not None:
                row_dict['efficiency_percent'] = float(row_dict['efficiency_percent'])
            results.append(row_dict)
        
        return jsonify(results)
    except Exception as e:
        logger.error(f"Error in get_blocks_efficiency: {str(e)}")
        return jsonify({'error': str(e)}), 500
    finally:
        cur.close()
        conn.close()

@analytics_bp.route('/api/block/search')
def search_block():
    """Поиск блока - как в app.py"""
    try:
        block_id = request.args.get('id')
        if not block_id:
            return jsonify({'error': 'Block ID is required'}), 400
        
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Получаем общую информацию о блоке
        cur.execute("""
            SELECT * FROM calculate_drilling_progress()
            WHERE block_id = %s
        """, (block_id,))
        block_info = cur.fetchone()
        logger.info(f"block_info: {block_info}")
        
        if not block_info:
            cur.close()
            conn.close()
            return jsonify({'error': 'Block not found'}), 404
        
        columns = [desc[0] for desc in cur.description]
        block_data = dict(zip(columns, block_info))
        logger.info(f"block_data: {block_data}")
        
        # Получаем информацию о станках на этом блоке
        cur.execute("""
            SELECT rs.block_id, rs.rig_id, COALESCE(dr.name, '-') AS rig_name, COALESCE(dr.model, '-') AS rig_model, rs.remaining_depth, rs.remaining_shifts, rp.total_depth, rp.shifts_count, rp.drill_hours, rp.performance_m_per_shift
            FROM calculate_remaining_shifts_by_block_rig() rs
            LEFT JOIN public."DrillingRigs" dr ON rs.rig_id = dr.id
            JOIN calculate_rig_productivity_by_block() rp ON rs.rig_id = rp.rig_id AND rs.block_id = rp.block_id
            WHERE rs.block_id = %s
            ORDER BY rp.block_id;
        """, (block_id,))
        columns = [desc[0] for desc in cur.description]
        rigs = []
        for row in cur.fetchall():
            rigs.append(dict(zip(columns, row)))
        logger.info(f"rig_productivity: {rigs}")
        
        # Получаем оставшиеся смены для блока
        cur.execute("""
            SELECT * FROM calculate_remaining_shifts_by_block()
            WHERE block_id = %s
        """, (block_id,))
        remaining_shifts = cur.fetchone()
        logger.info(f"remaining_shifts: {remaining_shifts}")
        
        # Получаем эффективность бурения для блока
        cur.execute("""
            SELECT block_id, efficiency_percent FROM calculate_drilling_efficiency_by_block()
            WHERE block_id = %s
        """, (block_id,))
        efficiency = cur.fetchone()
        logger.info(f"efficiency: {efficiency}")
        
        cur.close()
        conn.close()
        
        return jsonify({
            'block': block_data,
            'rigs': rigs,
            'remaining_shifts': remaining_shifts[1] if remaining_shifts else None,
            'efficiency': efficiency[1] if efficiency else None
        })
    except Exception as e:
        logger.error(f"Error in search_block: {str(e)}")
        return jsonify({'error': str(e)}), 500