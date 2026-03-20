# Mantenimiento App - Django

Aplicación web para gestión de mantenimiento preventivo y correctivo de automatismos industriales.

## Stack Tecnológico
- **Backend**: Django 6.0
- **Base de datos**: PostgreSQL (en Render)
- **Almacenamiento de fotos**: Cloudinary
- **PDF**: Reportlab
- **Frontend**: HTML + Bootstrap 5 + Bootstrap Icons
- **Deploy**: Render

## Modelos Principales

### Automatismo
- `codigo`: Código del automatismo (ej: AUT001)

### Preventivo
- `codigo`: PDS + número (ej: PDS001)
- `automatismo`: ForeignKey a Automatismo
- `estado`: iniciado, en_progreso, parado, finalizado
- `tecnico`: Usuario que creó el mantenimiento
- `tiempo`: Duración total (timedelta)
- `fecha_inicio`, `fecha_fin`

### Correctivo
- Similar a Preventivo pero para mantenimiento correctivo

### Modelos Relacionados
- `Deficiencia` / `DeficienciaCorrectivo`: Descripción de problemas
- `Recambio` / `RecambioCorrectivo`: Repuestos utilizados (nombre, cantidad)
- `Foto` / `FotoCorrectivo`: Fotos (URLField para Cloudinary)

## Variables de Entorno Requeridas

```
CLOUDINARY_CLOUD_NAME=...
CLOUDINARY_API_KEY=...
CLOUDINARY_API_KEY_SECRET=...
```

## URLs Principales

| URL | Descripción |
|-----|-------------|
| `/automatismos/` | Home - Lista de preventivos/correctivos activos |
| `/preventivo/nuevo/` | Crear preventivo |
| `/preventivo/<id>/` | Detalle preventivo |
| `/correctivo/nuevo/` | Crear correctivo |
| `/correctivo/<id>/` | Detalle correctivo |
| `/historial/` | Historial de finalizados |
| `/recambios/` | Buscador de recambios |

## Comandos Útiles

```bash
# Migraciones
python manage.py makemigrations
python manage.py migrate

# Servidor local
python manage.py runserver

# Recoger archivos estáticos
python manage.py collectstatic
```

## Estructura de Carpetas

```
mantenimiento/
├── manage.py
├── requirements.txt
├── Procfile
├── mantenimiento/
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
└── preventivoapp/
    ├── models.py
    ├── views.py
    ├── urls.py
    ├── templates/
    └── templatetags/
```

## Notas
- Las fotos se suben a Cloudinary usando el SDK de Cloudinary
- El campo `imagen` en Foto/FotoCorrectivo es URLField (no ImageField)
- Los PDFs se generan con reportlab
- El tiempo de mantenimiento se calcula correctamente cuando se pausa/reanuda
