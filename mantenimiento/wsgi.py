"""
WSGI config for mantenimiento project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/6.0/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mantenimiento.settings')

application = get_wsgi_application()

# Ejecutar migrate al inicio
from django.core.management import execute_from_command_line
execute_from_command_line(['manage.py', 'migrate', '--noinput'])
