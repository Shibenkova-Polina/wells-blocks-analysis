from flask import jsonify, request
import logging

class APIError(Exception):
    def __init__(self, message, status_code=500, payload=None):
        super().__init__()
        self.message = message
        self.status_code = status_code
        self.payload = payload
    
    def to_dict(self):
        rv = dict(self.payload or ())
        rv['message'] = self.message
        return rv

def setup_error_handlers(app):
    @app.errorhandler(APIError)
    def handle_api_error(error):
        response = jsonify(error.to_dict())
        response.status_code = error.status_code
        logging.error(f"API Error {error.status_code}: {error.message}")
        return response
    
    @app.errorhandler(404)
    def not_found_error(error):
        logging.warning(f"404 Not Found: {request.url}")
        return jsonify({'error': 'Resource not found'}), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        logging.error(f"500 Internal Server Error: {error}")
        return jsonify({'error': 'Internal server error'}), 500
    
    @app.errorhandler(Exception)
    def handle_unexpected_error(error):
        logging.error(f"Unexpected error: {error}")
        return jsonify({'error': 'An unexpected error occurred'}), 500