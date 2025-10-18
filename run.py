import os
import sys

# Добавляем текущую директорию в путь Python
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

try:
    from app import create_app
    app = create_app()
    print("✓ Successfully created Flask app")
    
except ImportError as e:
    print(f"✗ Import error: {e}")
    print("Trying to create simple app...")
    
    # Создаем простейшее приложение
    from flask import Flask
    app = Flask(__name__)
    
    @app.route('/')
    def hello():
        return "Flask is working! Basic setup is OK."

if __name__ == '__main__':
    print("Starting Flask application on http://localhost:5000")
    app.run(debug=True, host='0.0.0.0', port=5000)