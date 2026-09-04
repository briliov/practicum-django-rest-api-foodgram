FROM python:3.12

WORKDIR /app

RUN python -m pip install --upgrade pip

COPY requirements/requirements.txt .

RUN pip install -r requirements.txt --no-cache-dir && pip install gunicorn==25.3.0

COPY . .

CMD python manage.py makemigrations && python manage.py migrate && python manage.py collectstatic --no-input && gunicorn --bind 0.0.0.0:8000 core.wsgi --reload
