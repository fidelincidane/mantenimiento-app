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

# Crear superusuario automáticamente si no existe
def create_default_user():
    from django.contrib.auth.models import User
    if not User.objects.filter(username='admin').exists():
        User.objects.create_superuser('admin', 'admin@test.com', 'admin123')
        print('>>> Superusuario creado: admin / admin123')

create_default_user()
