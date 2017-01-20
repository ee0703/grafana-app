#! /bin/sh

cd /app/agent
nginx
python manage.py makemigrations api && python manage.py migrate && uwsgi --ini uwsgi.ini
# == only for debug ==
# python manage.py makemigrations api && python manage.py migrate && python manage.py runserver
