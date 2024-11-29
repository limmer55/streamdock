from app import create_app
import logging
import os

log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)
             
app = create_app()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 6050))
    app.run(host="0.0.0.0", port=port)
