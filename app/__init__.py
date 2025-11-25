# app/__init__.py
from flask import Flask
import os

def create_app():
    app = Flask(__name__, 
                template_folder='templates',
                static_folder='static')
    
    # Конфигурация
    app.config.update(
        SECRET_KEY=os.getenv('SECRET_KEY', 'dev-secret-key'),
        DB_HOST=os.getenv('DB_HOST'),
        DB_NAME=os.getenv('DB_NAME'), 
        DB_USER=os.getenv('DB_USER'),
        DB_PASSWORD=os.getenv('DB_PASSWORD'),
        DB_PORT=os.getenv('DB_PORT', '5432')
    )
    
    # Импорт и регистрация blueprint
    from app.routes.main import main_bp
    from app.routes.analytics import analytics_bp
    from app.routes.blocks import blocks_bp
    from app.routes.boreholes import boreholes_bp
    from app.routes.export import export_bp
    
    app.register_blueprint(main_bp)
    app.register_blueprint(analytics_bp)
    app.register_blueprint(blocks_bp)
    app.register_blueprint(boreholes_bp)
    app.register_blueprint(export_bp)
    
    return app