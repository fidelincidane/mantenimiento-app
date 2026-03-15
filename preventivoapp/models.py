from django.db import models
from django.contrib.auth.models import User


class Automatismo(models.Model):
    codigo = models.CharField(max_length=50, unique=True, verbose_name='Código')

    class Meta:
        verbose_name = 'Automatismo'
        verbose_name_plural = 'Automatismos'

    def __str__(self):
        return self.codigo


class Preventivo(models.Model):
    codigo = models.CharField(max_length=50, unique=True, verbose_name='Código PDS')
    automatismo = models.ForeignKey(Automatismo, on_delete=models.CASCADE, related_name='preventivos')
    tecnico = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='preventivos')
    fecha_inicio = models.DateField(auto_now_add=True, verbose_name='Fecha inicio')
    hora_inicio = models.TimeField(auto_now_add=True, verbose_name='Hora inicio')
    tiempo = models.DurationField(null=True, blank=True, verbose_name='Tiempo transcurrido')
    observaciones = models.TextField(blank=True, verbose_name='Observaciones / Anomalías')
    fecha_fin = models.DateTimeField(null=True, blank=True, verbose_name='Fecha fin')
    hora_parada = models.DateTimeField(null=True, blank=True, verbose_name='Hora de última parada')
    estado = models.CharField(max_length=20, choices=[
        ('iniciado', 'Iniciado'),
        ('en_progreso', 'En curso'),
        ('parado', 'Parado'),
        ('finalizado', 'Finalizado')
    ], default='iniciado', verbose_name='Estado')

    class Meta:
        verbose_name = 'Preventivo'
        verbose_name_plural = 'Preventivos'
        ordering = ['-fecha_inicio', '-hora_inicio']

    def __str__(self):
        return f"{self.codigo} - {self.automatismo}"


class Deficiencia(models.Model):
    TIPO_CHOICES = [
        ('electrica', 'Eléctrica'),
        ('mecanica', 'Mecánica'),
        ('neumatica', 'Neumática'),
        ('hidraulica', 'Hidráulica'),
        ('software', 'Software'),
        ('otra', 'Otra'),
    ]
    
    SEVERIDAD_CHOICES = [
        ('baja', 'Baja'),
        ('media', 'Media'),
        ('alta', 'Alta'),
        ('critica', 'Crítica'),
    ]

    preventivo = models.ForeignKey(Preventivo, on_delete=models.CASCADE, related_name='deficiencias')
    descripcion = models.TextField(verbose_name='Descripción')
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, verbose_name='Tipo')
    severidad = models.CharField(max_length=20, choices=SEVERIDAD_CHOICES, verbose_name='Severidad')

    class Meta:
        verbose_name = 'Deficiencia'
        verbose_name_plural = 'Deficiencias'

    def __str__(self):
        return f"{self.tipo} - {self.severidad}"


class Foto(models.Model):
    preventivo = models.ForeignKey(Preventivo, on_delete=models.CASCADE, related_name='fotos')
    imagen = models.ImageField(upload_to='fotos/', verbose_name='Imagen')
    descripcion = models.CharField(max_length=200, blank=True, verbose_name='Descripción')
    fecha = models.DateTimeField(auto_now_add=True, verbose_name='Fecha')

    class Meta:
        verbose_name = 'Foto'
        verbose_name_plural = 'Fotos'

    def __str__(self):
        return f"Foto {self.id} - {self.preventivo}"


class Recambio(models.Model):
    preventivo = models.ForeignKey(Preventivo, on_delete=models.CASCADE, related_name='recambios')
    nombre = models.CharField(max_length=200, verbose_name='Nombre del recambio')
    cantidad = models.PositiveIntegerField(default=1, verbose_name='Cantidad')

    class Meta:
        verbose_name = 'Recambio'
        verbose_name_plural = 'Recambios'

    def __str__(self):
        return f"{self.nombre} x{self.cantidad}"


class Correctivo(models.Model):
    codigo = models.CharField(max_length=50, unique=True, verbose_name='Código PDS')
    automatismo = models.ForeignKey(Automatismo, on_delete=models.CASCADE, related_name='correctivos')
    tecnico = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='correctivos')
    descripcion = models.TextField(verbose_name='Descripción de la avería')
    solucion = models.TextField(blank=True, verbose_name='Solución aplicada')
    fecha_inicio = models.DateField(auto_now_add=True, verbose_name='Fecha inicio')
    hora_inicio = models.TimeField(auto_now_add=True, verbose_name='Hora inicio')
    tiempo = models.DurationField(null=True, blank=True, verbose_name='Tiempo transcurrido')
    fecha_fin = models.DateTimeField(null=True, blank=True, verbose_name='Fecha fin')
    hora_parada = models.DateTimeField(null=True, blank=True, verbose_name='Hora de última parada')
    estado = models.CharField(max_length=20, choices=[
        ('iniciado', 'Iniciado'),
        ('en_reparacion', 'En reparación'),
        ('parado', 'Parado'),
        ('finalizado', 'Finalizado')
    ], default='iniciado', verbose_name='Estado')

    class Meta:
        verbose_name = 'Correctivo'
        verbose_name_plural = 'Correctivos'
        ordering = ['-fecha_inicio', '-hora_inicio']

    def __str__(self):
        return f"{self.codigo} - {self.automatismo}"


class DeficienciaCorrectivo(models.Model):
    TIPO_CHOICES = [
        ('electrica', 'Eléctrica'),
        ('mecanica', 'Mecánica'),
        ('neumatica', 'Neumática'),
        ('hidraulica', 'Hidráulica'),
        ('software', 'Software'),
        ('otra', 'Otra'),
    ]
    
    SEVERIDAD_CHOICES = [
        ('baja', 'Baja'),
        ('media', 'Media'),
        ('alta', 'Alta'),
        ('critica', 'Crítica'),
    ]

    correctivo = models.ForeignKey(Correctivo, on_delete=models.CASCADE, related_name='deficiencias')
    descripcion = models.TextField(verbose_name='Descripción')
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, verbose_name='Tipo')
    severidad = models.CharField(max_length=20, choices=SEVERIDAD_CHOICES, verbose_name='Severidad')

    class Meta:
        verbose_name = 'Deficiencia'
        verbose_name_plural = 'Deficiencias'

    def __str__(self):
        return f"{self.tipo} - {self.severidad}"


class FotoCorrectivo(models.Model):
    correctivo = models.ForeignKey(Correctivo, on_delete=models.CASCADE, related_name='fotos')
    imagen = models.ImageField(upload_to='fotos_correctivo/', verbose_name='Imagen')
    descripcion = models.CharField(max_length=200, blank=True, verbose_name='Descripción')
    fecha = models.DateTimeField(auto_now_add=True, verbose_name='Fecha')

    class Meta:
        verbose_name = 'Foto'
        verbose_name_plural = 'Fotos'

    def __str__(self):
        return f"Foto {self.id} - {self.correctivo}"


class RecambioCorrectivo(models.Model):
    correctivo = models.ForeignKey(Correctivo, on_delete=models.CASCADE, related_name='recambios')
    nombre = models.CharField(max_length=200, verbose_name='Nombre del recambio')
    cantidad = models.PositiveIntegerField(default=1, verbose_name='Cantidad')

    class Meta:
        verbose_name = 'Recambio'
        verbose_name_plural = 'Recambios'

    def __str__(self):
        return f"{self.nombre} x{self.cantidad}"
