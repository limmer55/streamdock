from app import create_app, monitor_streams
import logging
import threading
import os
import shutil

# Logging-config
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)

logging.getLogger("urllib3.connectionpool").setLevel(logging.WARNING)
logging.getLogger('werkzeug').setLevel(logging.ERROR)

class SuppressHTTPErrorFilter(logging.Filter):
    def __init__(self, suppressed_errors):
        super().__init__()
        self.suppressed_errors = suppressed_errors

    def filter(self, record):
        # Suppress logs that contain the specified error codes
        return not any(error in record.getMessage() for error in self.suppressed_errors)

suppressed_errors = ["429 Client Error", "404 Client Error", "406 Client Error"]
http_error_filter = SuppressHTTPErrorFilter(suppressed_errors)

logging.getLogger().addFilter(http_error_filter)

app = create_app()

def clear_stream_cache():
    cache_dir = os.path.join(os.path.dirname(__file__), 'static', 'stream_cache')
    if os.path.exists(cache_dir):
        shutil.rmtree(cache_dir)
        os.makedirs(cache_dir)
        logging.info(f"Cache directory '{cache_dir}' has been cleared.")

def start_monitor_streams(app):
    with app.app_context():
        monitor_streams()

# stream monitoring thread
stream_monitor_thread = threading.Thread(target=start_monitor_streams, args=(app,), daemon=True)
stream_monitor_thread.start()

if __name__ == "__main__":
    clear_stream_cache()
    app.run(host="0.0.0.0", port=6050, debug=True, threaded=True)
