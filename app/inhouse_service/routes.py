# URL(라우트) 정의

from flask import render_template
from . import bp

@bp.get("/")
def home():
    return render_template("empty_page.html", active="empty")