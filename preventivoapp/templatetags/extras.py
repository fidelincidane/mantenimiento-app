from django import template

register = template.Library()

@register.filter
def duration(td):
    # Convierte timedelta a formato legible (1d 2h 30m)
    if not td:
        return "-"
    total_seconds = int(td.total_seconds())
    days = total_seconds // 86400
    hours = (total_seconds % 86400) // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60
    
    parts = []
    if days > 0:
        parts.append(f"{days}d")
    if hours > 0:
        parts.append(f"{hours}h")
    if minutes > 0:
        parts.append(f"{minutes}m")
    if seconds > 0 or not parts:
        parts.append(f"{seconds}s")
    
    return " ".join(parts)

@register.filter
def badge_color(estado):
    """Mapea estado a color de badge Bootstrap"""
    colores = {
        'iniciado': 'primary',
        'en_progreso': 'info',
        'parado': 'warning',
        'finalizado': 'success',
    }
    return colores.get(estado, 'secondary')
