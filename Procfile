web: gunicorn schoolmanagement.wsgi:application --bind 0.0.0.0:$PORT
worker: celery -A schoolmanagement worker -l info
beat: celery -A schoolmanagement beat -l info
