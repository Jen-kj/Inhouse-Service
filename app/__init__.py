
from flask import Flask
from .inhouse_service import bp as inhouse_bp
from .db import init_db

def create_app():
    app = Flask(__name__)

    init_db()

    # ?쇱슦???깅줉
    app.register_blueprint(inhouse_bp)

    return app
