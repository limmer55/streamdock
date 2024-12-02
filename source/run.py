import os
from app import create_app
import logging

logging.basicConfig(
    level=logging.DEBUG,
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

app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=6050, debug=False)
