release: python manage.py migrate && python manage.py create_default_admin
web: gunicorn mantenimiento.wsgi --log-file -
