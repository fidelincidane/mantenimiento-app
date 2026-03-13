# Mantenimiento - App de Gestión de Mantenimiento

## Tecnologías
- **Backend**: Django 6 (Python)
- **Frontend**: HTML + Bootstrap 5
- **Base de datos**: SQLite (desarrollo) / PostgreSQL (producción)

## Requisitos
- Python 3.8+
- Django 6

## Instalación local

```bash
# 1. Instalar dependencias
pip install -r requirements.txt

# 2. Migrar base de datos
python manage.py migrate

# 3. Crear superusuario
python manage.py createsuperuser

# 4. Ejecutar servidor
python manage.py runserver
```

## Despliegue en Render

### Archivos necesarios ya incluidos:
- `requirements.txt` - dependencias
- `Procfile` - comando de inicio

### Pasos:
1. **Sube el proyecto a GitHub**
   - Crea un repositorio nuevo en GitHub
   - Sube la carpeta `mantenimiento/`

2. **Crear cuenta en Render**
   - Ve a render.com
   - Inicia sesión con GitHub

3. **Crear Base de Datos PostgreSQL**
   - New → PostgreSQL
   - Guarda la URL de conexión

4. **Crear Web Service**
   - New → Web Service
   - Conecta tu repositorio de GitHub
   - Configura:
     - **Build Command**: `pip install -r requirements.txt`
     - **Start Command**: `gunicorn mantenimiento.wsgi`
   - En **Environment Variables**:
     - `SECRET_KEY`: Genera una nueva (python -c "import secrets; print(secrets.token_urlsafe(50))")
     - `DEBUG`: `False`
     - `ALLOWED_HOSTS`: `tuapp.onrender.com`
     - `DATABASE_URL`: Pega la URL de PostgreSQL

5. **Migrar base de datos**
   - En Render, ve a **Shell** del web service
   - Ejecuta: `python manage.py migrate`
   - Crea superusuario: `python manage.py createsuperuser`

### Notas importantes:
- Las fotos se almacenan localmente. En producción usa **Cloudinary** o **AWS S3** para almacenamiento de archivos.
- El servicio gratuito de Render hiberna después de 15 min de inactividad.
