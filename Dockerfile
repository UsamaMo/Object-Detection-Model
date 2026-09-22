FROM python:3.13-slim
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PORT=8000
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app.py detector.py gunicorn.conf.py ./
COPY templates/ templates/
COPY static/ static/
COPY Objects/ Objects/
COPY Scenes/ Scenes/
RUN useradd --create-home appuser
USER appuser
EXPOSE 8000
CMD ["gunicorn", "--config", "gunicorn.conf.py", "app:app"]
