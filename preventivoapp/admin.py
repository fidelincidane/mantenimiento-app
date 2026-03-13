from django.contrib import admin
from .models import Automatismo, Preventivo, Deficiencia, Foto, Recambio
from .models import Correctivo, DeficienciaCorrectivo, FotoCorrectivo, RecambioCorrectivo


@admin.register(Automatismo)
class AutomatismoAdmin(admin.ModelAdmin):
    list_display = ('codigo',)
    search_fields = ('codigo',)


@admin.register(Preventivo)
class PreventivoAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'automatismo', 'tecnico', 'fecha_inicio', 'hora_inicio', 'estado')
    list_filter = ('estado', 'fecha_inicio', 'automatismo')
    search_fields = ('codigo', 'automatismo__codigo', 'tecnico__username')
    raw_id_fields = ('automatismo', 'tecnico')


@admin.register(Deficiencia)
class DeficienciaAdmin(admin.ModelAdmin):
    list_display = ('preventivo', 'tipo', 'severidad')
    list_filter = ('tipo', 'severidad')
    search_fields = ('descripcion',)


@admin.register(Foto)
class FotoAdmin(admin.ModelAdmin):
    list_display = ('preventivo', 'fecha', 'descripcion')
    raw_id_fields = ('preventivo',)


@admin.register(Recambio)
class RecambioAdmin(admin.ModelAdmin):
    list_display = ('preventivo', 'nombre', 'cantidad')
    search_fields = ('nombre',)


@admin.register(Correctivo)
class CorrectivoAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'automatismo', 'tecnico', 'fecha_inicio', 'hora_inicio', 'estado')
    list_filter = ('estado', 'fecha_inicio', 'automatismo')
    search_fields = ('codigo', 'automatismo__codigo', 'tecnico__username')
    raw_id_fields = ('automatismo', 'tecnico')


@admin.register(DeficienciaCorrectivo)
class DeficienciaCorrectivoAdmin(admin.ModelAdmin):
    list_display = ('correctivo', 'tipo', 'severidad')
    list_filter = ('tipo', 'severidad')
    search_fields = ('descripcion',)


@admin.register(FotoCorrectivo)
class FotoCorrectivoAdmin(admin.ModelAdmin):
    list_display = ('correctivo', 'fecha', 'descripcion')
    raw_id_fields = ('correctivo',)


@admin.register(RecambioCorrectivo)
class RecambioCorrectivoAdmin(admin.ModelAdmin):
    list_display = ('correctivo', 'nombre', 'cantidad')
    search_fields = ('nombre',)
