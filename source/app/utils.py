import os
import shutil
import logging
from flask import current_app

def clear_stream_cache():
    """
    Löscht alle Dateien und Ordner im stream_cache-Verzeichnis.
    """
    stream_cache_path = current_app.config.get('STREAM_CACHE_PATH')
    if not stream_cache_path:
        logging.error("STREAM_CACHE_PATH ist nicht in der App-Konfiguration gesetzt.")
        return

    if not os.path.exists(stream_cache_path):
        logging.warning(f"Stream-Cache-Pfad existiert nicht: {stream_cache_path}")
        return

    for filename in os.listdir(stream_cache_path):
        file_path = os.path.join(stream_cache_path, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
                logging.debug(f"Datei gelöscht: {file_path}")
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
                logging.debug(f"Verzeichnis gelöscht: {file_path}")
        except Exception as e:
            logging.error(f"Fehler beim Löschen von {file_path}: {e}")
