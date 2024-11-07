FROM python:3.11-slim

WORKDIR /

RUN apt-get update && \
    apt-get install -y binutils libproj-dev gdal-bin vim python3 build-essential \
    libpq-dev libmemcached-dev libfreetype6-dev

COPY . .

RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8000

CMD ["sh", "-c", "python manage.py migrate && python manage.py runserver 0.0.0.0:8000"]
