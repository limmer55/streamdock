import os
from flask import current_app

def get_cache_dir():
    return current_app.config.get('STREAM_CACHE_PATH', os.path.join(os.path.dirname(os.path.dirname(__file__)), 'cache'))
