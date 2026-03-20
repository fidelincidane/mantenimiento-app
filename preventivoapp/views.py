from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from .models import Automatismo, Preventivo, Deficiencia, Foto, Recambio
from .models import Correctivo, DeficienciaCorrectivo, FotoCorrectivo, RecambioCorrectivo
import cloudinary
import cloudinary.uploader
import datetime


def get_cloudinary_config():
    cloudinary.config(
        cloud_name=settings.CLOUDINARY_STORAGE.get('CLOUD_NAME', ''),
        api_key=settings.CLOUDINARY_STORAGE.get('API_KEY', ''),
        api_secret=settings.CLOUDINARY_STORAGE.get('API_SECRET', '')
    )


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
    # Solo mostrar preventivo y correctivos en estado iniciado o parado
    preventivos_curso = Preventivo.objects.filter(estado__in=['iniciado', 'parado']).order_by('-fecha_inicio')
    correctivos_curso = Correctivo.objects.filter(estado__in=['iniciado', 'parado']).order_by('-fecha_inicio')
    
    return render(request, 'preventivoapp/automatismos.html', {
        'preventivos_curso': preventivos_curso,
        'correctivos_curso': correctivos_curso
    })


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
        # Calcular tiempo total
        inicio = timezone.make_aware(datetime.datetime.combine(preventivo.fecha_inicio, preventivo.hora_inicio))
        
        # Si estaba parado, calcular tiempo hasta la parada
        if preventivo.hora_parada:
            tiempo_hasta_parada = preventivo.hora_parada - inicio
            # Añadir tiempo anterior si existe
            if preventivo.tiempo:
                preventivo.tiempo = preventivo.tiempo + tiempo_hasta_parada
            else:
                preventivo.tiempo = tiempo_hasta_parada
        else:
            # No estaba parado, calcular normalmente
            tiempo_transcurrido = ahora - inicio
            if preventivo.tiempo:
                preventivo.tiempo = preventivo.tiempo + tiempo_transcurrido
            else:
                preventivo.tiempo = tiempo_transcurrido
    
    preventivo.estado = 'finalizado'
    preventivo.fecha_fin = timezone.now()
    preventivo.save()
    messages.success(request, f'Preventivo {preventivo.codigo} finalizado')
    return redirect('detalle_preventivo', id=preventivo.id)


@login_required
def parar_preventivo(request, id):
    preventivo = get_object_or_404(Preventivo, id=id)
    
    ahora = timezone.now()
    inicio = timezone.make_aware(datetime.datetime.combine(preventivo.fecha_inicio, preventivo.hora_inicio))
    
    if preventivo.hora_parada:
        # Ya estaba parado antes, calcular tiempo entre la última parada y ahora
        tiempo_desde_ultima_parada = ahora - preventivo.hora_parada
        if preventivo.tiempo:
            preventivo.tiempo = preventivo.tiempo + tiempo_desde_ultima_parada
        else:
            preventivo.tiempo = tiempo_desde_ultima_parada
    else:
        # Primera vez que para
        tiempo_transcurrido = ahora - inicio
        preventivo.tiempo = tiempo_transcurrido
    
    preventivo.hora_parada = ahora
    preventivo.estado = 'parado'
    preventivo.save()
    messages.success(request, 'Preventivo parado')
    return redirect('detalle_preventivo', id=preventivo.id)


@login_required
def reanudar_preventivo(request, id):
    preventivo = get_object_or_404(Preventivo, id=id)
    
    preventivo.hora_parada = None
    preventivo.estado = 'en_progreso'
    preventivo.save()
    messages.success(request, 'Preventivo reanudado')
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
            try:
                # Configurar Cloudinary
                get_cloudinary_config()
                
                # Subir a Cloudinary
                result = cloudinary.uploader.upload(
                    imagen,
                    folder='mantenimiento/fotos/'
                )
                
                # Guardar solo la URL en la base de datos
                foto = Foto.objects.create(
                    preventivo=preventivo,
                    imagen=result['secure_url'],
                    descripcion=descripcion
                )
                messages.success(request, 'Foto subida a Cloudinary')
            except Exception as e:
                messages.error(request, f'Error al subir foto: {str(e)}')
    
    return redirect('detalle_preventivo', id=id)


@login_required
def eliminar_preventivo(request, id):
    preventivo = get_object_or_404(Preventivo, id=id)
    preventivo.delete()
    messages.success(request, 'Preventivo eliminado')
    return redirect('historial')


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
        
        if correctivo.hora_parada:
            tiempo_hasta_parada = correctivo.hora_parada - inicio
            if correctivo.tiempo:
                correctivo.tiempo = correctivo.tiempo + tiempo_hasta_parada
            else:
                correctivo.tiempo = tiempo_hasta_parada
        else:
            tiempo_transcurrido = ahora - inicio
            if correctivo.tiempo:
                correctivo.tiempo = correctivo.tiempo + tiempo_transcurrido
            else:
                correctivo.tiempo = tiempo_transcurrido
    
    correctivo.estado = 'finalizado'
    correctivo.fecha_fin = timezone.now()
    correctivo.save()
    messages.success(request, f'Correctivo {correctivo.codigo} finalizado')
    return redirect('detalle_correctivo', id=correctivo.id)


@login_required
def parar_correctivo(request, id):
    correctivo = get_object_or_404(Correctivo, id=id)
    
    ahora = timezone.now()
    inicio = timezone.make_aware(datetime.datetime.combine(correctivo.fecha_inicio, correctivo.hora_inicio))
    
    if correctivo.hora_parada:
        tiempo_desde_ultima_parada = ahora - correctivo.hora_parada
        if correctivo.tiempo:
            correctivo.tiempo = correctivo.tiempo + tiempo_desde_ultima_parada
        else:
            correctivo.tiempo = tiempo_desde_ultima_parada
    else:
        tiempo_transcurrido = ahora - inicio
        correctivo.tiempo = tiempo_transcurrido
    
    correctivo.hora_parada = ahora
    correctivo.estado = 'parado'
    correctivo.save()
    messages.success(request, 'Correctivo parado')
    return redirect('detalle_correctivo', id=correctivo.id)


@login_required
def reanudar_correctivo(request, id):
    correctivo = get_object_or_404(Correctivo, id=id)
    
    correctivo.hora_parada = None
    correctivo.estado = 'en_reparacion'
    correctivo.save()
    messages.success(request, 'Correctivo reanudado')
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
            try:
                # Configurar Cloudinary
                get_cloudinary_config()
                
                # Subir a Cloudinary
                result = cloudinary.uploader.upload(
                    imagen,
                    folder='mantenimiento/correctivos/'
                )
                
                # Guardar solo la URL en la base de datos
                FotoCorrectivo.objects.create(
                    correctivo=correctivo,
                    imagen=result['secure_url'],
                    descripcion=descripcion
                )
                messages.success(request, 'Foto subida a Cloudinary')
            except Exception as e:
                messages.error(request, f'Error al subir foto: {str(e)}')
    
    return redirect('detalle_correctivo', id=id)


@login_required
def eliminar_correctivo(request, id):
    correctivo = get_object_or_404(Correctivo, id=id)
    correctivo.delete()
    messages.success(request, 'Correctivo eliminado')
    return redirect('historial')


# ========== HISTORIAL ==========

@login_required
def historial(request):
    busqueda_pds = request.GET.get('busqueda_pds', '')
    busqueda_aut = request.GET.get('busqueda_aut', '')
    
    preventivos = Preventivo.objects.filter(estado='finalizado').order_by('-fecha_inicio')
    correctivos = Correctivo.objects.filter(estado='finalizado').order_by('-fecha_inicio')
    
    if busqueda_pds:
        preventivos = preventivos.filter(codigo__icontains=busqueda_pds)
        correctivos = correctivos.filter(codigo__icontains=busqueda_pds)
    
    if busqueda_aut:
        preventivos = preventivos.filter(automatismo__codigo__icontains=busqueda_aut)
        correctivos = correctivos.filter(automatismo__codigo__icontains=busqueda_aut)
    
    return render(request, 'preventivoapp/historial.html', {
        'preventivos': preventivos,
        'correctivos': correctivos,
        'busqueda_pds': busqueda_pds,
        'busqueda_aut': busqueda_aut
    })


@login_required
def detalle_historial_preventivo(request, codigo_pds):
    preventivo = get_object_or_404(Preventivo, codigo=codigo_pds)
    return render(request, 'preventivoapp/detalle_historial_preventivo.html', {'preventivo': preventivo})


@login_required
def detalle_historial_correctivo(request, codigo_pds):
    correctivo = get_object_or_404(Correctivo, codigo=codigo_pds)
    return render(request, 'preventivoapp/detalle_historial_correctivo.html', {'correctivo': correctivo})


# ========== RECAMBIOS ==========

@login_required
def buscar_recambios(request):
    busqueda_nombre = request.GET.get('busqueda_nombre', '')
    busqueda_aut = request.GET.get('busqueda_aut', '')
    
    recambios_preventivos = Recambio.objects.all().select_related('preventivo', 'preventivo__automatismo')
    recambios_correctivos = RecambioCorrectivo.objects.all().select_related('correctivo', 'correctivo__automatismo')
    
    if busqueda_nombre:
        recambios_preventivos = recambios_preventivos.filter(nombre__icontains=busqueda_nombre)
        recambios_correctivos = recambios_correctivos.filter(nombre__icontains=busqueda_nombre)
    
    if busqueda_aut:
        recambios_preventivos = recambios_preventivos.filter(preventivo__automatismo__codigo__icontains=busqueda_aut)
        recambios_correctivos = recambios_correctivos.filter(correctivo__automatismo__codigo__icontains=busqueda_aut)
    
    return render(request, 'preventivoapp/recambios.html', {
        'recambios_preventivos': recambios_preventivos,
        'recambios_correctivos': recambios_correctivos,
        'busqueda_nombre': busqueda_nombre,
        'busqueda_aut': busqueda_aut
    })


# ========== PDF ==========

@login_required
def generar_pdf_preventivo(request, id):
    from django.http import HttpResponse
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
    from reportlab.lib.units import cm
    from reportlab.lib.enums import TA_CENTER, TA_LEFT
    from io import BytesIO
    import urllib.request
    
    preventivo = get_object_or_404(Preventivo, id=id)
    
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=2*cm, leftMargin=2*cm, topMargin=2*cm, bottomMargin=2*cm)
    
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name='TitleCenter', alignment=TA_CENTER, fontSize=18, spaceAfter=20))
    styles.add(ParagraphStyle(name='SubTitle', alignment=TA_CENTER, fontSize=12, textColor=colors.grey))
    styles.add(ParagraphStyle(name='Section', fontSize=14, textColor=colors.HexColor('#0d6efd'), spaceBefore=15, spaceAfter=10))
    
    story = []
    
    story.append(Paragraph(preventivo.codigo, styles['TitleCenter']))
    story.append(Paragraph(f"Automatismo: {preventivo.automatismo.codigo} | Técnico: {preventivo.tecnico.username}", styles['SubTitle']))
    story.append(Spacer(1, 20))
    
    story.append(Paragraph("Información General", styles['Section']))
    
    info_data = [
        ['Estado:', preventivo.get_estado_display()],
        ['Fecha Inicio:', preventivo.fecha_inicio.strftime('%d/%m/%Y %H:%M')],
    ]
    if preventivo.fecha_fin:
        info_data.append(['Fecha Fin:', preventivo.fecha_fin.strftime('%d/%m/%Y %H:%M')])
    if preventivo.tiempo:
        total_seconds = int(preventivo.tiempo.total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        info_data.append(['Tiempo Total:', f'{hours}h {minutes}m'])
    if preventivo.descripcion:
        info_data.append(['Descripción:', preventivo.descripcion])
    
    info_table = Table(info_data, colWidths=[5*cm, 12*cm])
    info_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]))
    story.append(info_table)
    story.append(Spacer(1, 15))
    
    if preventivo.deficiencias.all():
        story.append(Paragraph("Deficiencias", styles['Section']))
        defic_data = [['Descripción', 'Fecha']]
        for d in preventivo.deficiencias.all():
            defic_data.append([d.descripcion, d.fecha.strftime('%d/%m/%Y %H:%M')])
        defic_table = Table(defic_data, colWidths=[12*cm, 5*cm])
        defic_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0d6efd')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ]))
        story.append(defic_table)
        story.append(Spacer(1, 15))
    
    if preventivo.recambios.all():
        story.append(Paragraph("Recambios", styles['Section']))
        recam_data = [['Nombre', 'Cantidad', 'Fecha']]
        for r in preventivo.recambios.all():
            recam_data.append([r.nombre, str(r.cantidad), r.fecha.strftime('%d/%m/%Y %H:%M')])
        recam_table = Table(recam_data, colWidths=[8*cm, 3*cm, 6*cm])
        recam_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0d6efd')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ]))
        story.append(recam_table)
    
    doc.build(story)
    
    response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{preventivo.codigo}.pdf"'
    return response


@login_required
def generar_pdf_correctivo(request, id):
    from django.http import HttpResponse
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib.units import cm
    from reportlab.lib.enums import TA_CENTER
    from io import BytesIO
    
    correctivo = get_object_or_404(Correctivo, id=id)
    
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=2*cm, leftMargin=2*cm, topMargin=2*cm, bottomMargin=2*cm)
    
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name='TitleCenter', alignment=TA_CENTER, fontSize=18, spaceAfter=20))
    styles.add(ParagraphStyle(name='SubTitle', alignment=TA_CENTER, fontSize=12, textColor=colors.grey))
    styles.add(ParagraphStyle(name='Section', fontSize=14, textColor=colors.HexColor('#dc3545'), spaceBefore=15, spaceAfter=10))
    
    story = []
    
    story.append(Paragraph(correctivo.codigo, styles['TitleCenter']))
    story.append(Paragraph(f"Automatismo: {correctivo.automatismo.codigo} | Técnico: {correctivo.tecnico.username}", styles['SubTitle']))
    story.append(Spacer(1, 20))
    
    story.append(Paragraph("Información General", styles['Section']))
    
    info_data = [
        ['Estado:', correctivo.get_estado_display()],
        ['Fecha Inicio:', correctivo.fecha_inicio.strftime('%d/%m/%Y %H:%M')],
    ]
    if correctivo.fecha_fin:
        info_data.append(['Fecha Fin:', correctivo.fecha_fin.strftime('%d/%m/%Y %H:%M')])
    if correctivo.tiempo:
        total_seconds = int(correctivo.tiempo.total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        info_data.append(['Tiempo Total:', f'{hours}h {minutes}m'])
    if correctivo.descripcion:
        info_data.append(['Descripción:', correctivo.descripcion])
    
    info_table = Table(info_data, colWidths=[5*cm, 12*cm])
    info_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]))
    story.append(info_table)
    story.append(Spacer(1, 15))
    
    if correctivo.deficiencias.all():
        story.append(Paragraph("Deficiencias", styles['Section']))
        defic_data = [['Descripción', 'Fecha']]
        for d in correctivo.deficiencias.all():
            defic_data.append([d.descripcion, d.fecha.strftime('%d/%m/%Y %H:%M')])
        defic_table = Table(defic_data, colWidths=[12*cm, 5*cm])
        defic_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#dc3545')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ]))
        story.append(defic_table)
        story.append(Spacer(1, 15))
    
    if correctivo.recambios.all():
        story.append(Paragraph("Recambios", styles['Section']))
        recam_data = [['Nombre', 'Cantidad', 'Fecha']]
        for r in correctivo.recambios.all():
            recam_data.append([r.nombre, str(r.cantidad), r.fecha.strftime('%d/%m/%Y %H:%M')])
        recam_table = Table(recam_data, colWidths=[8*cm, 3*cm, 6*cm])
        recam_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#dc3545')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ]))
        story.append(recam_table)
    
    doc.build(story)
    
    response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{correctivo.codigo}.pdf"'
    return response
