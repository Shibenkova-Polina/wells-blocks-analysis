from functools import wraps
from flask import request, abort
import re

def validate_block_id(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        block_id = kwargs.get('block_id')
        if block_id and not re.match(r'^\d+$', block_id):
            abort(400, description="Invalid block ID format")
        return f(*args, **kwargs)
    return decorated_function

def validate_block_input(block_input):
    """Валидация ввода блока"""
    if not block_input or len(block_input.strip()) == 0:
        return False, "Block input cannot be empty"
    
    if len(block_input) > 100:
        return False, "Block input too long"
    
    # Проверка на SQL-инъекции (базовая)
    if any(char in block_input for char in [';', "'", '"', '--', '/*']):
        return False, "Invalid characters in input"
    
    return True, ""

def sanitize_string(value):
    """Очистка строки от потенциально опасных символов"""
    if not value:
        return value
    return re.sub(r'[;\'"\\]', '', str(value))

def validate_borehole_name(borehole_name):
    """Валидация имени скважины"""
    if not borehole_name or not isinstance(borehole_name, str):
        return False, "Borehole name must be a non-empty string"
    
    if len(borehole_name.strip()) == 0:
        return False, "Borehole name cannot be empty or whitespace"
    
    if len(borehole_name) > 50:
        return False, "Borehole name too long"
    
    # Проверка на допустимые символы
    if not re.match(r'^[a-zA-Z0-9_\-\. ]+$', borehole_name):
        return False, "Borehole name contains invalid characters"
    
    return True, ""

def safe_float_conversion(value, default=0.0):
    """Безопасное преобразование в float"""
    if value is None:
        return default
    try:
        return float(value)
    except (ValueError, TypeError):
        return default