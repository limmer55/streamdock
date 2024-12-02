import os
from flask import current_app

def get_cache_dir():
    # Retrieve the cache directory path from the app configuration.
    # If not set, default to a 'cache' directory at the root of the project.
    return current_app.config.get('STREAM_CACHE_PATH', os.path.join(os.path.dirname(os.path.dirname(__file__)), 'cache'))
