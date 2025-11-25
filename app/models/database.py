# database.py
import psycopg2
from psycopg2 import sql
from psycopg2.extras import RealDictCursor
import logging
import os
from contextlib import contextmanager
from dotenv import load_dotenv

# Загрузка переменных окружения
load_dotenv('config.env')

# Настройка логирования
logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self, app=None):
        self.app = app
        self.db_config = self._load_config()
    
    def _load_config(self):
        """Загрузка конфигурации БД"""
        return {
            'host': os.getenv('DB_HOST', 'localhost'),
            'database': os.getenv('DB_NAME', 'postgres'),
            'user': os.getenv('DB_USER', 'postgres'),
            'password': os.getenv('DB_PASSWORD', ''),
            'port': os.getenv('DB_PORT', '5432')
        }
    
    def init_app(self, app):
        self.app = app
        self.db_config = self._load_config()
    
    def get_db_config(self):
        """Получение конфигурации БД"""
        try:
            from flask import current_app
            return {
                'host': current_app.config.get('DB_HOST') or os.getenv('DB_HOST', 'localhost'),
                'database': current_app.config.get('DB_NAME') or os.getenv('DB_NAME', 'postgres'),
                'user': current_app.config.get('DB_USER') or os.getenv('DB_USER', 'postgres'),
                'password': current_app.config.get('DB_PASSWORD') or os.getenv('DB_PASSWORD', ''),
                'port': current_app.config.get('DB_PORT') or os.getenv('DB_PORT', '5432')
            }
        except RuntimeError:
            return self.db_config
    
    @contextmanager
    def get_connection(self):
        """Контекстный менеджер для соединения с БД"""
        conn = None
        try:
            db_config = self.get_db_config()
            logger.info(f"Connecting to database: {db_config['host']}:{db_config['port']}")
            
            conn = psycopg2.connect(
                **db_config,
                connect_timeout=10
            )
            yield conn
        except psycopg2.OperationalError as e:
            logger.error(f"Database connection failed: {e}")
            raise Exception(f"Unable to connect to database: {e}")
        except psycopg2.Error as e:
            logger.error(f"Database error: {e}")
            raise
        finally:
            if conn:
                conn.close()
    
    @contextmanager
    def get_cursor(self, cursor_factory=None):
        """Контекстный менеджер для курсора"""
        with self.get_connection() as conn:
            cursor = conn.cursor(cursor_factory=cursor_factory or RealDictCursor)
            try:
                yield cursor
                conn.commit()
            except Exception as e:
                conn.rollback()
                logger.error(f"Database operation failed: {e}")
                raise
            finally:
                cursor.close()
    
    def execute_query(self, query, params=None, cursor_factory=None):
        """Выполнить запрос и вернуть результаты"""
        with self.get_cursor(cursor_factory) as cursor:
            cursor.execute(query, params or ())
            if cursor.description:  # Если есть результаты
                return cursor.fetchall()
            return None
    
    def execute_function(self, function_name, params=None):
        """Выполнить PostgreSQL функцию"""
        try:
            if params:
                placeholders = ', '.join(['%s'] * len(params))
                query = sql.SQL("SELECT * FROM {}({})").format(
                    sql.Identifier(function_name),
                    sql.SQL(placeholders)
                )
                return self.execute_query(query, params)
            else:
                query = sql.SQL("SELECT * FROM {}()").format(sql.Identifier(function_name))
                return self.execute_query(query)
        except Exception as e:
            logger.error(f"Error executing function {function_name}: {e}")
            raise

    def test_connection(self):
        """Тестирование подключения к БД"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT 1")
                    result = cursor.fetchone()
                    logger.info("Database connection test successful")
                    return True
        except Exception as e:
            logger.error(f"Database connection test failed: {e}")
            return False

# Создаем глобальный экземпляр для использования во всем приложении
db_manager = DatabaseManager()