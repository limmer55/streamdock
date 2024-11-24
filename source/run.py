import os
from app import create_app
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',  # Log-Ausgabeformat
)
logging.getLogger("urllib3.connectionpool").setLevel(logging.WARNING)


log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)



class Suppress429Filter(logging.Filter):
    def filter(self, record):
        # Unterdrücke Logs, die "429" enthalten
        return "429 Client Error" not in record.getMessage()


os.makedirs('/tmp/transcoded_stream', exist_ok=True)
      
app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=6050)
