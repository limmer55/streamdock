from app import create_app, monitor_streams
import logging
import threading

# Logging-Konfiguration
logging.basicConfig(
    level=logging.ERROR,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',  # Log-Ausgabeformat
)

logging.getLogger("urllib3.connectionpool").setLevel(logging.WARNING)
logging.getLogger('werkzeug').setLevel(logging.ERROR)

class SuppressHTTPErrorFilter(logging.Filter):
    def __init__(self, suppressed_errors):
        super().__init__()
        self.suppressed_errors = suppressed_errors

    def filter(self, record):
        # Unterdrücke Logs, die die angegebenen Fehlercodes enthalten
        return not any(error in record.getMessage() for error in self.suppressed_errors)

suppressed_errors = ["429 Client Error", "404 Client Error", "406 Client Error"]
http_error_filter = SuppressHTTPErrorFilter(suppressed_errors)

logging.getLogger().addFilter(http_error_filter)

# Flask-App erstellen
app = create_app()

def start_monitor_streams(app):
    with app.app_context():
        monitor_streams()

# Starte den Überwachungs-Thread
stream_monitor_thread = threading.Thread(target=start_monitor_streams, args=(app,), daemon=True)
stream_monitor_thread.start()

if __name__ == "__main__":
    # Flask-App starten
    app.run(host="0.0.0.0", port=6050, debug=False)
