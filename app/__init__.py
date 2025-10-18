from flask import Flask
from flask_caching import Cache
import logging
from logging.handlers import RotatingFileHandler
from .config import Config
from .utils.exceptions import setup_error_handlers

# Инициализация расширений
cache = Cache()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Инициализация расширений
    cache.init_app(app)
    
    # Регистрация обработчиков ошибок
    setup_error_handlers(app)
    
    # Регистрация blueprint'ов
    from app.routes.main import main_bp
    from app.routes.analytics import analytics_bp
    from app.routes.blocks import blocks_bp
    from app.routes.boreholes import boreholes_bp
    
    app.register_blueprint(main_bp)
    app.register_blueprint(analytics_bp, url_prefix='/analytics')
    app.register_blueprint(blocks_bp, url_prefix='/api')
    app.register_blueprint(boreholes_bp, url_prefix='/api')
    
    # Настройка логирования
    setup_logging(app)
    
    return app

def setup_logging(app):
    if not app.debug:
        # Очистка существующих обработчиков
        for handler in logging.root.handlers[:]:
            logging.root.removeHandler(handler)
        
        # Создание форматтера
        formatter = logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        )
        
        # Файловый обработчик
        file_handler = RotatingFileHandler(
            'app.log', maxBytes=10485760, backupCount=5
        )
        file_handler.setFormatter(formatter)
        file_handler.setLevel(logging.INFO)
        
        # Консольный обработчик
        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(formatter)
        stream_handler.setLevel(logging.INFO)
        
        # Настройка корневого логгера
        logging.root.setLevel(logging.INFO)
        logging.root.addHandler(file_handler)
        logging.root.addHandler(stream_handler)
        
        # Отключение логирования Werkzeug
        logging.getLogger('werkzeug').setLevel(logging.WARNING)