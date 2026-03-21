# Mantenimiento - App de Gestion de Mantenimiento

Aplicacion web para la gestion de mantenimiento preventivo/correctivo, desarrollada con Django y desplegada en Render.

## Demo en vivo 🌍

👉 **App en Render:** _pendiente de añadir URL publica_

## Tecnologias 🛠️

- **Backend:** Django 6 (Python)
- **Frontend:** HTML + Bootstrap 5
- **Base de datos:** SQLite (desarrollo) / PostgreSQL (produccion)
- **Media storage:** Cloudinary
- **Servidor de produccion:** Gunicorn + Whitenoise

## Requisitos 📋

- Python 3.8+
- pip actualizado
- PostgreSQL (para produccion)

## Instalacion local 🚀

```bash
# 1) Crear entorno virtual (opcional pero recomendado)
python -m venv .venv

# 2) Activar entorno virtual (Windows)
.venv\Scripts\activate

# 3) Instalar dependencias
pip install -r requirements.txt

# 4) Migrar base de datos
python manage.py migrate

# 5) Crear superusuario
python manage.py createsuperuser

# 6) Ejecutar servidor
python manage.py runserver
```

## Variables de entorno 🔐

Configura estas variables para entorno de produccion:

- `SECRET_KEY`
- `DEBUG=False`
- `ALLOWED_HOSTS`
- `DATABASE_URL`
- `CLOUDINARY_CLOUD_NAME`
- `CLOUDINARY_API_KEY`
- `CLOUDINARY_API_KEY_SECRET`

## Despliegue en Render 🌐

### Archivos clave del proyecto 📁

- `requirements.txt` (dependencias de Python)
- `Procfile` (comando de inicio en Render)
- `mantenimiento/settings.py` (configuracion de entorno)

### Configuracion sugerida en Render ✅

- **Build Command:** `pip install -r requirements.txt`
- **Start Command:** `python manage.py migrate && python manage.py collectstatic --noinput && gunicorn mantenimiento.wsgi --log-file -`

### Pasos de despliegue

1. Conectar el repositorio en Render
2. Configurar variables de entorno
3. Desplegar el servicio
4. Verificar acceso y panel admin

## Almacenamiento de imagenes en Cloudinary ☁️

Las imagenes del sistema se almacenan en Cloudinary para evitar perdida de archivos en hosting gratuito y mejorar disponibilidad.

## Caracteristicas principales ✨

- Gestion de mantenimiento preventivo y correctivo
- Carga de imagenes de evidencias
- Panel administrativo Django
- Generacion de reportes en PDF
