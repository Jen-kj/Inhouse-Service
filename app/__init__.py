
import os
from pathlib import Path

from flask import Flask
from .inhouse_service import bp as inhouse_bp
from .db import init_db


def _load_env_file(path: Path) -> None:
    if not path or not path.exists() or not path.is_file():
        return

    try:
        content = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        content = path.read_text(encoding="utf-8-sig")

    for raw_line in content.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip("'").strip('"')
        if key and key not in os.environ:
            os.environ[key] = value


def create_app():
    app = Flask(__name__)

    root = Path(__file__).resolve().parent.parent
    _load_env_file(root / "instance" / ".env")
    _load_env_file(root / "app" / "inhouse_service" / "instance" / ".env")
    _load_env_file(root / ".env")

    init_db()

    # ?쇱슦???깅줉
    app.register_blueprint(inhouse_bp)

    return app
