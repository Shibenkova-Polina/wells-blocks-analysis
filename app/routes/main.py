from flask import Blueprint, render_template, request, redirect
from app.utils.validators import validate_block_input

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    return render_template('main_index.html')

@main_bp.route('/analytics')
def analytics_dashboard():
    return render_template('analytics_index.html')

@main_bp.route('/borehole-analytics')
def borehole_analytics():
    return render_template('borehole_index.html')

@main_bp.route('/dashboard', methods=['GET', 'POST'])
def get_dashboard_data():
    from app.routes.blocks import get_dashboard_data
    return get_dashboard_data()

# API маршруты для аналитики
@main_bp.route('/api/blocks/progress')
def get_blocks_progress():
    from app.routes.analytics import get_blocks_progress
    return get_blocks_progress()

@main_bp.route('/api/blocks/drilling_progress')
def get_drilling_progress():
    from app.routes.analytics import get_drilling_progress
    return get_drilling_progress()

@main_bp.route('/api/rigs/productivity')
def get_rig_productivity():
    from app.routes.analytics import get_rig_productivity
    return get_rig_productivity()

@main_bp.route('/api/rigs/models')
def get_rig_models_productivity():
    from app.routes.analytics import get_rig_models_productivity
    return get_rig_models_productivity()

@main_bp.route('/api/blocks/remaining_shifts')
def get_remaining_shifts():
    from app.routes.analytics import get_remaining_shifts
    return get_remaining_shifts()

@main_bp.route('/api/blocks/efficiency')
def get_blocks_efficiency():
    from app.routes.analytics import get_blocks_efficiency
    return get_blocks_efficiency()

@main_bp.route('/api/block/search')
def search_block():
    from app.routes.analytics import search_block
    return search_block()

# API маршруты для 3D визуализации
@main_bp.route('/api/block/<block_id>/info', methods=['GET'])
def get_block_info_api(block_id):
    """Получение информации о блоке для 3D визуализации"""
    from app.routes.blocks import get_block_info_3d
    return get_block_info_3d(block_id)

@main_bp.route('/api/block/<block_id>/boreholes', methods=['GET'])
def get_block_boreholes(block_id):
    """Получение данных о скважинах для 3D визуализации"""
    from app.routes.boreholes import get_boreholes_3D
    return get_boreholes_3D(block_id)

@main_bp.route('/api/block/<block_id>/relief', methods=['GET'])
def get_block_relief(block_id):
    """Получение данных о рельефе для 3D визуализации"""
    from app.routes.boreholes import get_relief_3D
    return get_relief_3D(block_id)

# Маршрут для деталей скважины
@main_bp.route('/borehole/<block_id>/<borehole_name>')
def get_borehole_details(block_id, borehole_name):
    from app.routes.boreholes import get_borehole_details_data
    return get_borehole_details_data(block_id, borehole_name)