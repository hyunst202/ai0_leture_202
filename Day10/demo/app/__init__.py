import sqlite3

from flask import Flask, jsonify
from flask_wtf.csrf import CSRFError, CSRFProtect
from werkzeug.exceptions import HTTPException

from .config import configuration
from .validation import ApiError


def create_app(test_config=None):
    app = Flask(__name__)
    app.config.update(configuration(test_config))
    app.json.ensure_ascii = False
    CSRFProtect(app)

    from . import auth, board, cli, db, masking
    app.before_request(auth.load_user)
    app.teardown_appcontext(db.close_db)
    app.register_blueprint(auth.bp)
    app.register_blueprint(board.bp)
    app.register_blueprint(masking.bp)
    cli.register(app)

    @app.get("/")
    def index():
        return app.send_static_file("index.html")

    @app.errorhandler(ApiError)
    def api_error(error):
        return jsonify(error=error.message), error.status

    @app.errorhandler(CSRFError)
    def csrf_error(error):
        return jsonify(error="요청 확인 토큰이 없거나 만료되었습니다. 새로고침 후 다시 시도해주세요."), 400

    @app.errorhandler(sqlite3.OperationalError)
    def database_error(error):
        app.logger.error("Database operation unavailable (%s)", type(error).__name__)
        return jsonify(error="데이터베이스를 사용할 수 없습니다. 잠시 후 다시 시도해주세요."), 503

    @app.errorhandler(HTTPException)
    def http_error(error):
        messages = {404: "요청한 항목을 찾을 수 없습니다.", 405: "허용하지 않는 요청입니다.", 413: "입력 용량이 너무 큽니다."}
        return jsonify(error=messages.get(error.code, "요청 형식을 확인해주세요.")), error.code

    @app.after_request
    def response_headers(response):
        from flask import request
        if request.path.startswith("/api/") or request.path == "/":
            response.headers["Cache-Control"] = "no-store"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "same-origin"
        response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self'; style-src 'self'; object-src 'none'; base-uri 'self'; frame-ancestors 'none'; form-action 'self'"
        return response

    return app

