import logging
import os
import shutil

from .helpers import get_cache_dir

def clear_stream_cache():
    cache_dir = get_cache_dir()
    if os.path.exists(cache_dir):
        shutil.rmtree(cache_dir)
        os.makedirs(cache_dir, exist_ok=True)
        logging.info("Cache-Verzeichnis wurde geleert.")
    else:
        logging.warning("Cache-Verzeichnis existiert nicht.")
