from flask import jsonify
import decimal

def json_response(data, status_code=200):
    """Создание JSON ответа с поддержкой Decimal"""
    def decimal_default(obj):
        if isinstance(obj, decimal.Decimal):
            return float(obj)
        raise TypeError
    
    response = jsonify(data)
    response.status_code = status_code
    return response

def format_coordinates(x, y, z):
    """Форматирование координат"""
    return {
        'x': round(float(x or 0), 2),
        'y': round(float(y or 0), 2), 
        'z': round(float(z or 0), 2)
    }

def calculate_deviation(planned, actual):
    """Расчет отклонения"""
    if planned is None or actual is None:
        return None
    return abs(float(actual) - float(planned))