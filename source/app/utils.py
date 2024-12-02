# utils.py
import logging
import os
import shutil

from .helpers import get_cache_dir

def clear_stream_cache(exclude_hashes=None):
    """
    Clears the stream cache directories, excluding any hashes provided.

    :param exclude_hashes: A set of stream hashes to exclude from deletion.
    """
    cache_dir = get_cache_dir()
    for entry in os.scandir(cache_dir):
        if entry.is_dir():
            if exclude_hashes and entry.name in exclude_hashes:
                logging.debug(f"Excluding cache directory: {entry.path}")
                continue
            try:
                shutil.rmtree(entry.path)
                logging.info(f"Deleted cache directory: {entry.path}")
            except Exception as e:
                logging.error(f"Failed to delete cache directory {entry.path}: {e}")
