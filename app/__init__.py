# 설정 + 라우트 등록
from flask import Flask
from .inhouse_service import bp as inhouse_bp

def create_app():
    app = Flask(__name__)

    # 라우트 등록
    app.register_blueprint(inhouse_bp)

    return app