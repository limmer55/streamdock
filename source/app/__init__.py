from flask import Flask
from .routes import main_bp
import os
import logging
import json

def create_app():
    app = Flask(
        __name__, 
        template_folder=os.path.join(os.path.dirname(__file__), '../templates'),
        static_folder=os.path.join(os.path.dirname(__file__), '../static')
    )

    logging.basicConfig(level=logging.DEBUG)  # Setze auf DEBUG für detaillierte Logs

    # Priorität: Umgebungsvariable > config.json
    m3u_url_env = os.environ.get('M3U_URL')
    if m3u_url_env:
        app.config['M3U_URL'] = m3u_url_env
        logging.info(f"M3U URL loaded from environment: {app.config['M3U_URL']}")
    else:
        config_path = os.path.join(os.path.dirname(__file__), '..', 'config.json')
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as config_file:
                try:
                    config_data = json.load(config_file)
                    app.config['M3U_URL'] = config_data.get('m3u_url', '')
                    logging.info(f"M3U URL loaded from config.json: {app.config['M3U_URL']}")
                except json.JSONDecodeError:
                    app.config['M3U_URL'] = ''
                    logging.error("Error parsing config.json. 'M3U_URL' set to empty.")
        else:
            app.config['M3U_URL'] = ''
            logging.warning("config.json not found. 'M3U_URL' set to empty.")

    with app.app_context():
        app.register_blueprint(main_bp)

    # Definiere das Stream-Cache-Verzeichnis innerhalb des statischen Verzeichnisses
    stream_cache_path = os.path.join(app.static_folder, 'stream_cache')
    if not os.path.exists(stream_cache_path):
        os.makedirs(stream_cache_path)
        logging.info(f"Created stream cache folder: {stream_cache_path}")

    # Speichern Sie den Cache-Pfad in der App-Konfiguration für den Zugriff in anderen Modulen
    app.config['STREAM_CACHE_PATH'] = stream_cache_path

    return app
