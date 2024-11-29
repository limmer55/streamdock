FROM python:3.11-slim


WORKDIR /app


COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt


COPY . .


ENV FLASK_APP run.py
ENV FLASK_ENV production
ENV PORT=6050


EXPOSE ${PORT}


CMD gunicorn --bind 0.0.0.0:${PORT} run:app
