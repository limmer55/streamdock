FROM python:3.11-slim


WORKDIR /app


COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt


COPY . .


ENV FLASK_APP run.py
ENV FLASK_ENV production


EXPOSE 6050


CMD ["gunicorn", "--bind", "0.0.0.0:6050", "run:app"]
