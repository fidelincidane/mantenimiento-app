from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import Automatismo, Preventivo, Deficiencia, Foto, Recambio
from .models import Correctivo, DeficienciaCorrectivo, FotoCorrectivo, RecambioCorrectivo
import datetime


def login_view(request):
    # Crear superusuario si no existe
    from django.contrib.auth.models import User
    if not User.objects.filter(username='admin').exists():
        User.objects.create_superuser('admin', 'admin@test.com', 'admin123')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('automatismos')
        else:
            messages.error(request, 'Usuario o contraseña incorrectos')
    return render(request, 'preventivoapp/login.html')


def logout_view(request):
    logout(request)
    return redirect('login')


@login_required
def lista_automatismos(request):
    automatismos = Automatismo.objects.all().order_by('codigo')
    return render(request, 'preventivoapp/automatismos.html', {'automatismos': automatismos})


@login_required
def crear_automatismo(request):
    if request.method == 'POST':
        codigo = request.POST.get('codigo')
        if codigo:
            Automatismo.objects.create(codigo=codigo.upper())
            messages.success(request, f'Automatismo {codigo} creado')
            return redirect('automatismos')
    return redirect('automatismos')


# ========== PREVENTIVOS ==========

@login_required
def crear_preventivo(request):
    if request.method == 'POST':
        codigo_pds = request.POST.get('codigo')
        codigo_aut = request.POST.get('automatismo')
        
        automatismo, created = Automatismo.objects.get_or_create(
            codigo=codigo_aut.upper(),
            defaults={'codigo': codigo_aut.upper()}
        )
        if created:
            messages.success(request, f'Automatismo {automatismo.codigo} creado')
        
        preventivo = Preventivo.objects.create(
            codigo=codigo_pds.upper(),
            automatismo=automatismo,
            tecnico=request.user,
            estado='iniciado'
        )
        messages.success(request, f'Preventivo {codigo_pds} iniciado')
        return redirect('detalle_preventivo', id=preventivo.id)
    
    automatismo_id = request.GET.get('automatismo')
    automatismo_preseleccionado = None
    if automatismo_id:
        automatismo_preseleccionado = get_object_or_404(Automatismo, id=automatismo_id)
    
    automatismos = Automatismo.objects.all().order_by('codigo')
    return render(request, 'preventivoapp/crear_preventivo.html', {
        'automatismos': automatismos,
        'automatismo_preseleccionado': automatismo_preseleccionado
    })


@login_required
def detalle_preventivo(request, id):
    preventivo = get_object_or_404(Preventivo, id=id)
    
    if request.method == 'POST':
        observaciones = request.POST.get('observaciones')
        if observaciones is not None:
            preventivo.observaciones = observaciones
            preventivo.estado = 'en_progreso'
            preventivo.save()
            messages.success(request, 'Observaciones guardadas')
    
    return render(request, 'preventivoapp/detalle_preventivo.html', {'preventivo': preventivo})


@login_required
def finalizar_preventivo(request, id):
    preventivo = get_object_or_404(Preventivo, id=id)
    
    if preventivo.hora_inicio:
        ahora = timezone.now()
        inicio = timezone.make_aware(datetime.datetime.combine(preventivo.fecha_inicio, preventivo.hora_inicio))
        preventivo.tiempo = ahora - inicio
    
    preventivo.estado = 'finalizado'
    preventivo.fecha_fin = timezone.now()
    preventivo.save()
    messages.success(request, f'Preventivo {preventivo.codigo} finalizado')
    return redirect('detalle_preventivo', id=preventivo.id)


@login_required
def agregar_deficiencia(request, id):
    preventivo = get_object_or_404(Preventivo, id=id)
    
    if request.method == 'POST':
        descripcion = request.POST.get('descripcion')
        tipo = request.POST.get('tipo')
        severidad = request.POST.get('severidad')
        
        Deficiencia.objects.create(
            preventivo=preventivo,
            descripcion=descripcion,
            tipo=tipo,
            severidad=severidad
        )
        messages.success(request, 'Deficiencia registrada')
    
    return redirect('detalle_preventivo', id=id)


@login_required
def agregar_recambio(request, id):
    preventivo = get_object_or_404(Preventivo, id=id)
    
    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        cantidad = request.POST.get('cantidad')
        
        Recambio.objects.create(
            preventivo=preventivo,
            nombre=nombre,
            cantidad=cantidad
        )
        messages.success(request, 'Recambio registrado')
    
    return redirect('detalle_preventivo', id=id)


@login_required
def agregar_foto(request, id):
    preventivo = get_object_or_404(Preventivo, id=id)
    
    if request.method == 'POST':
        imagen = request.FILES.get('imagen')
        descripcion = request.POST.get('descripcion', '')
        
        if imagen:
            Foto.objects.create(
                preventivo=preventivo,
                imagen=imagen,
                descripcion=descripcion
            )
            messages.success(request, 'Foto añadida')
    
    return redirect('detalle_preventivo', id=id)


# ========== CORRECTIVOS ==========

@login_required
def crear_correctivo(request):
    if request.method == 'POST':
        codigo_pds = request.POST.get('codigo')
        codigo_aut = request.POST.get('automatismo')
        descripcion = request.POST.get('descripcion')
        
        automatismo, created = Automatismo.objects.get_or_create(
            codigo=codigo_aut.upper(),
            defaults={'codigo': codigo_aut.upper()}
        )
        if created:
            messages.success(request, f'Automatismo {automatismo.codigo} creado')
        
        correctivo = Correctivo.objects.create(
            codigo=codigo_pds.upper(),
            automatismo=automatismo,
            descripcion=descripcion,
            tecnico=request.user,
            estado='iniciado'
        )
        messages.success(request, f'Correctivo {codigo_pds} iniciado')
        return redirect('detalle_correctivo', id=correctivo.id)
    
    automatismo_id = request.GET.get('automatismo')
    automatismo_preseleccionado = None
    if automatismo_id:
        automatismo_preseleccionado = get_object_or_404(Automatismo, id=automatismo_id)
    
    automatismos = Automatismo.objects.all().order_by('codigo')
    return render(request, 'preventivoapp/crear_correctivo.html', {
        'automatismos': automatismos,
        'automatismo_preseleccionado': automatismo_preseleccionado
    })


@login_required
def detalle_correctivo(request, id):
    correctivo = get_object_or_404(Correctivo, id=id)
    
    if request.method == 'POST':
        solucion = request.POST.get('solucion')
        if solucion is not None:
            correctivo.solucion = solucion
            correctivo.estado = 'en_reparacion'
            correctivo.save()
            messages.success(request, 'Solución guardada')
    
    return render(request, 'preventivoapp/detalle_correctivo.html', {'correctivo': correctivo})


@login_required
def finalizar_correctivo(request, id):
    correctivo = get_object_or_404(Correctivo, id=id)
    
    if correctivo.hora_inicio:
        ahora = timezone.now()
        inicio = timezone.make_aware(datetime.datetime.combine(correctivo.fecha_inicio, correctivo.hora_inicio))
        correctivo.tiempo = ahora - inicio
    
    correctivo.estado = 'finalizado'
    correctivo.fecha_fin = timezone.now()
    correctivo.save()
    messages.success(request, f'Correctivo {correctivo.codigo} finalizado')
    return redirect('detalle_correctivo', id=correctivo.id)


@login_required
def agregar_deficiencia_correctivo(request, id):
    correctivo = get_object_or_404(Correctivo, id=id)
    
    if request.method == 'POST':
        descripcion = request.POST.get('descripcion')
        tipo = request.POST.get('tipo')
        severidad = request.POST.get('severidad')
        
        DeficienciaCorrectivo.objects.create(
            correctivo=correctivo,
            descripcion=descripcion,
            tipo=tipo,
            severidad=severidad
        )
        messages.success(request, 'Deficiencia registrada')
    
    return redirect('detalle_correctivo', id=id)


@login_required
def agregar_recambio_correctivo(request, id):
    correctivo = get_object_or_404(Correctivo, id=id)
    
    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        cantidad = request.POST.get('cantidad')
        
        RecambioCorrectivo.objects.create(
            correctivo=correctivo,
            nombre=nombre,
            cantidad=cantidad
        )
        messages.success(request, 'Recambio registrado')
    
    return redirect('detalle_correctivo', id=id)


@login_required
def agregar_foto_correctivo(request, id):
    correctivo = get_object_or_404(Correctivo, id=id)
    
    if request.method == 'POST':
        imagen = request.FILES.get('imagen')
        descripcion = request.POST.get('descripcion', '')
        
        if imagen:
            FotoCorrectivo.objects.create(
                correctivo=correctivo,
                imagen=imagen,
                descripcion=descripcion
            )
            messages.success(request, 'Foto añadida')
    
    return redirect('detalle_correctivo', id=id)


# ========== HISTORIAL ==========

@login_required
def historial(request):
    preventivos = Preventivo.objects.filter(estado='finalizado').order_by('-fecha_inicio')
    correctivos = Correctivo.objects.filter(estado='finalizado').order_by('-fecha_inicio')
    return render(request, 'preventivoapp/historial.html', {
        'preventivos': preventivos,
        'correctivos': correctivos
    })


@login_required
def detalle_historial_preventivo(request, codigo_pds):
    preventivo = get_object_or_404(Preventivo, codigo=codigo_pds)
    return render(request, 'preventivoapp/detalle_historial_preventivo.html', {'preventivo': preventivo})


@login_required
def detalle_historial_correctivo(request, codigo_pds):
    correctivo = get_object_or_404(Correctivo, codigo=codigo_pds)
    return render(request, 'preventivoapp/detalle_historial_correctivo.html', {'correctivo': correctivo})
