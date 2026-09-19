FROM python:3.12 AS base
WORKDIR /app
RUN python -m pip install --upgrade pip
COPY requirements/requirements.txt . 
RUN pip install -r requirements.txt --no-cache-dir

FROM base AS development
COPY . .
CMD python manage.py makemigrations --no-input && python manage.py migrate && \ 
    python manage.py load_data && \
    python manage.py collectstatic --no-input && \
    python3 manage.py runserver 0.0.0.0:8000

FROM base AS production
COPY . .
RUN pip install gunicorn==25.3.0 --no-cache-dir
CMD gunicorn --bind 0.0.0.0:8000 core.wsgi