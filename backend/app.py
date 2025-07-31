# app.py (single entry point, no __init__.py needed)

from flask import Flask
from flask_cors import CORS
from config import Config
from routes.sync import sync_bp
from routes.export import export_bp
from routes.change_password import passwd_bp
from routes.info import info_bp

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    CORS(app)

    app.register_blueprint(sync_bp, url_prefix='/api')
    app.register_blueprint(export_bp, url_prefix='/api')
    app.register_blueprint(passwd_bp, url_prefix='/api')
    app.register_blueprint(info_bp, url_prefix='/api')

    @app.route("/")
    def home():
        return "<p>DVR Management API is running.</p>"

    return app

if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=5000)
