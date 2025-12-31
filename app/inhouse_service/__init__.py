# bp 만들고 routes를 불러와서 라우트를 bp에 채우는 파일

from flask import Blueprint

bp = Blueprint("inhouse_service", __name__)

from . import routes  # noqa