from app import create_app
import logging

log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)
             
app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=6050)
