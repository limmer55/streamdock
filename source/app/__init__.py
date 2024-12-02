from flask import Flask, current_app
from .routes import main_bp, monitor_streams
import os
import logging
import json
import redis
import time

def create_app():
    # Initialize the Flask application with custom template and static folder paths
    app = Flask(
        __name__, 
        template_folder=os.path.join(os.path.dirname(__file__), '../templates'),
        static_folder=os.path.join(os.path.dirname(__file__), '../static')
    )

    # Load M3U URL from environment variable or config.json
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

    # Configure Redis connection
    app.config['REDIS_URL'] = 'redis://redis:6379/0'
    #app.config['REDIS_URL'] = 'redis://192.168.2.64:6379/0'
    app.redis = redis.StrictRedis.from_url(app.config['REDIS_URL'])

    # Check the connection to Redis, retrying every 5 seconds if it fails
    while True:
        try:
            app.redis.ping()
            logging.info("Connected to Redis server successfully.")
            break
        except redis.ConnectionError:
            logging.error("Failed to connect to Redis server. Retrying in 5 seconds...")
            time.sleep(5)

    # Register blueprints and reload configuration within the app context
    with app.app_context():
        app.register_blueprint(main_bp)
        reload_config()
        
    # Ensure the stream cache folder exists
    stream_cache_path = os.path.join(app.static_folder, 'stream_cache')
    if not os.path.exists(stream_cache_path):
        os.makedirs(stream_cache_path)
        logging.info(f"Created stream cache folder: {stream_cache_path}")

    app.config['STREAM_CACHE_PATH'] = stream_cache_path

    return app

def reload_config():
    """
    Reload the configuration from the config.json file.
    """
    config_path = os.path.join(os.path.dirname(__file__), '..', 'config.json')
    try:
        with open(config_path, 'r', encoding='utf-8') as config_file:
            config_data = json.load(config_file)
            current_app.config['M3U_URL'] = config_data.get('m3u_url', '')
            logging.info(f"M3U URL reloaded: {current_app.config['M3U_URL']}")
    except Exception as e:
        logging.error(f"Error reloading config.json: {e}")

