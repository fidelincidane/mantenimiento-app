# Mantenimiento App - Django

Aplicación web para gestión de mantenimiento preventivo y correctivo de automatismos industriales.

## Stack Tecnológico
- **Backend**: Django 6.0
- **Base de datos**: PostgreSQL (en Render)
- **Almacenamiento de fotos**: Cloudinary
- **PDF**: Reportlab
- **Frontend**: HTML + Bootstrap 5 + Bootstrap Icons
- **Deploy**: Render (https://mantenimiento-fd3k.onrender.com)
- **Repositorio**: https://github.com/fidelincidane/mantenimiento-app

## Modelos Principales

### Automatismo
- `codigo`: CharField - Código del automatismo (ej: AUT001)

### Preventivo
- `codigo`: CharField - Código PDS (ej: PDS001)
- `automatismo`: ForeignKey a Automatismo
- `tecnico`: ForeignKey a User
- `estado`: choices=['iniciado', 'en_progreso', 'parado', 'finalizado']
- `tiempo`: DurationField (tiempo total)
- `fecha_inicio`: DateField
- `hora_inicio`: TimeField
- `fecha_fin`: DateTimeField
- `hora_parada`: DateTimeField
- `observaciones`: TextField

### Correctivo
- Igual que Preventivo + `descripcion` y `solucion`

### Deficiencia / DeficienciaCorrectivo
- `preventivo` / `correctivo`: ForeignKey
- `descripcion`: TextField
- `tipo`: choices=['electrica', 'mecanica', 'neumatica', 'hidraulica', 'software', 'otra']
- `severidad`: choices=['baja', 'media', 'alta', 'critica']
- **NO tiene campo `fecha`**

### Recambio / RecambioCorrectivo
- `preventivo` / `correctivo`: ForeignKey
- `nombre`: CharField
- `cantidad`: PositiveIntegerField
- **NO tiene campo `fecha`**

### Foto / FotoCorrectivo
- `preventivo` / `correctivo`: ForeignKey
- `imagen`: URLField (URL de Cloudinary)
- `descripcion`: CharField
- `fecha`: DateTimeField

## URLs Principales

| URL | Descripción |
|-----|-------------|
| `/` | Login |
| `/automatismos/` | Home - preventivos/correctivos activos |
| `/preventivo/nuevo/` | Crear preventivo |
| `/preventivo/<id>/` | Detalle preventivo |
| `/preventivo/<id>/pdf/` | Generar PDF preventivo |
| `/correctivo/nuevo/` | Crear correctivo |
| `/correctivo/<id>/` | Detalle correctivo |
| `/correctivo/<id>/pdf/` | Generar PDF correctivo |
| `/historial/` | Historial de finalizados |
| `/recambios/` | Buscador de recambios |

## Funcionalidades Implementadas

### Preventivos
- Crear, ver, finalizar preventivo
- Parar/reanudar (con control de tiempo)
- Agregar deficiencias, recambios, fotos
- Descargar PDF individual

### Correctivos
- Mismo flujo que preventivos

### Historial
- Lista de finalizados
- Multiselector para eliminar/descargar PDFs
- Ver detalle de preventivo/correctivo finalizado

### Recambios
- Buscador por nombre y automatismo
- Multiselector para eliminar varios
- Pestañas: preventivos / correctivos

### PDF
- Generado con Reportlab
- Incluye: info general, tiempo, deficiencias, recambios, enlaces a fotos
- Las fotos se muestran como ENLACES clicables (no imagen embebida)
- Multiselector para generar PDF de varios a la vez

## Bugs Corregidos (Importante)

1. **Error 500 en detalle_preventivo**: Template usaba `correcto.tiempo` en vez de `preventivo.tiempo`
2. **Auto-detección solo creaba 1 repuesto**: Tenía `break` que cortaba el bucle
3. **Colores de badges incorrectos**: Creado filtro `badge_color` en extras.py
4. **Error 500 en PDFs**: Modelo Deficiencia/Recambio NO tiene campo `fecha`, se quitó esa columna
5. **URL historial**: Cambiada de buscar por `codigo` a `id` para evitar errores
6. **Quitado campo observaciones**: Se eliminó de la vista detalle_preventivo

## Variables de Entorno Requeridas

```
CLOUDINARY_CLOUD_NAME=...
CLOUDINARY_API_KEY=...
CLOUDINARY_API_KEY_SECRET=...
```

## Comandos Útiles

```bash
# Migraciones
python manage.py makemigrations
python manage.py migrate

# Servidor local
python manage.py runserver

# Recoger archivos estáticos
python manage.py collectstatic

# Git
git add -A && git commit -m "mensaje" && git push origin main
```

## Estructura de Carpetas

```
mantenimiento/
├── manage.py
├── requirements.txt
├── Procfile
├── AGENTS.md
├── mantenimiento/
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
└── preventivoapp/
    ├── models.py
    ├── views.py
    ├── urls.py
    ├── admin.py
    ├── templates/preventivoapp/
    │   ├── base.html
    │   ├── login.html
    │   ├── automatismos.html
    │   ├── crear_preventivo.html
    │   ├── crear_correctivo.html
    │   ├── detalle_preventivo.html
    │   ├── detalle_correctivo.html
    │   ├── historial.html
    │   ├── detalle_historial_preventivo.html
    │   ├── detalle_historial_correctivo.html
    │   └── recambios.html
    └── templatetags/
        ├── __init__.py
        └── extras.py (filtros: duration, badge_color)
```

## Notas Importantes

- Las fotos se suben a Cloudinary usando el SDK
- El campo `imagen` es URLField (no ImageField)
- PDFs NO insertan fotos, solo muestran ENLACES clicables
- Modelo Deficiencia y Recambio NO tienen campo `fecha`
- Al hacer commit, usar `git pull origin main --rebase` si hay cambios remotos
