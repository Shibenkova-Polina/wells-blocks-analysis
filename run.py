# run.py
import os
import sys

# Добавляем текущую директорию в путь Python
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

try:
    from app import create_app
    app = create_app()
    print("✓ Successfully created Flask app with all blueprints")
    
    # Проверка зарегистрированных маршрутов
    print("Registered routes:")
    for rule in app.url_map.iter_rules():
        print(f"  {rule}")
        
except Exception as e:
    print(f"✗ Error creating app: {e}")
    import traceback
    traceback.print_exc()
    
    # Создаем простое приложение для отладки
    from flask import Flask
    app = Flask(__name__)
    
    @app.route('/')
    def hello():
        return "Flask is working! But there was an error with the main app setup."

if __name__ == '__main__':
    print("Starting Flask application on http://localhost:5000")
    print("Available pages:")
    print("  - http://localhost:5000/ (главная страница)")
    print("  - http://localhost:5000/analytics (аналитика)")
    print("  - http://localhost:5000/borehole-analytics (аналитика скважин)")
    app.run(debug=True, host='0.0.0.0', port=5000)