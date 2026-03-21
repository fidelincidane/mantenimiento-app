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
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib.units import cm
    from reportlab.lib.enums import TA_CENTER, TA_LEFT
    from io import BytesIO
    
    preventivo = get_object_or_404(Preventivo, id=id)
    
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=1.5*cm, leftMargin=1.5*cm, topMargin=1.5*cm, bottomMargin=1.5*cm)
    
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name='TitleMain', alignment=TA_CENTER, fontSize=20, textColor=colors.white, spaceAfter=0, backColor=colors.HexColor('#0d6efd')))
    styles.add(ParagraphStyle(name='TitleCode', alignment=TA_CENTER, fontSize=24, spaceAfter=20, textColor=colors.HexColor('#0d6efd')))
    styles.add(ParagraphStyle(name='Section', fontSize=12, textColor=colors.HexColor('#0d6efd'), spaceBefore=10, spaceAfter=5, fontName='Helvetica-Bold'))
    
    story = []
    
    # Titulo principal
    title_table = Table([['HOJA DE PREVENTIVO']], colWidths=[17*cm])
    title_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#0d6efd')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 16),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
    ]))
    story.append(title_table)
    story.append(Spacer(1, 10))
    
    # Codigo PDS
    story.append(Paragraph(f"PDS {preventivo.codigo}", styles['TitleCode']))
    story.append(Spacer(1, 10))
    
    # Informacion general - siempre mostrar todos los campos
    story.append(Paragraph("INFORMACIÓN GENERAL", styles['Section']))
    
    # Crear tabla con todos los datos
    info_data = [
        ['Automatismo:', preventivo.automatismo.codigo if preventivo.automatismo else '-'],
        ['Técnico:', preventivo.tecnico.username if preventivo.tecnico else '-'],
        ['Fecha Inicio:', preventivo.fecha_inicio.strftime('%d/%m/%Y') if preventivo.fecha_inicio else '-'],
        ['Hora Inicio:', preventivo.hora_inicio.strftime('%H:%M') if preventivo.hora_inicio else '-'],
        ['Fecha Fin:', preventivo.fecha_fin.strftime('%d/%m/%Y %H:%M') if preventivo.fecha_fin else '-'],
        ['Estado:', preventivo.get_estado_display() if preventivo.estado else '-'],
    ]
    
    info_table = Table(info_data, colWidths=[5*cm, 12*cm])
    info_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#e9ecef')),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#dee2e6')),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(info_table)
    story.append(Spacer(1, 10))
    
    # Tiempo Total
    story.append(Paragraph("TIEMPO TOTAL", styles['Section']))
    tiempo_text = '-'
    if preventivo.tiempo:
        total_seconds = int(preventivo.tiempo.total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        tiempo_text = f'{hours}h {minutes}m {seconds}s'
    
    tiempo_table = Table([[tiempo_text]], colWidths=[17*cm])
    tiempo_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f8f9fa')),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#dee2e6')),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 14),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
    ]))
    story.append(tiempo_table)
    story.append(Spacer(1, 10))
    
    # Observaciones
    story.append(Paragraph("OBSERVACIONES / ANOMALÍAS", styles['Section']))
    obs_text = preventivo.observaciones if preventivo.observaciones else 'Sin observaciones'
    obs_table = Table([[obs_text]], colWidths=[17*cm], rowHeights=[60])
    obs_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.white),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#dee2e6')),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(obs_table)
    story.append(Spacer(1, 10))
    
    # Deficiencias
    story.append(Paragraph("DEFICIENCIAS", styles['Section']))
    defic_data = [['Tipo', 'Severidad', 'Descripción', 'Fecha']]
    for d in preventivo.deficiencias.all():
        defic_data.append([
            d.get_tipo_display() if d.tipo else '-',
            d.get_severidad_display() if d.severidad else '-',
            d.descripcion if d.descripcion else '-',
            d.fecha.strftime('%d/%m/%Y %H:%M') if d.fecha else '-'
        ])
    if len(defic_data) == 1:
        defic_data.append(['-', '-', 'Sin deficiencias registradas', '-'])
    
    defic_table = Table(defic_data, colWidths=[3*cm, 3*cm, 8*cm, 3*cm])
    defic_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0d6efd')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#dee2e6')),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5),
    ]))
    story.append(defic_table)
    story.append(Spacer(1, 10))
    
    # Recambios
    story.append(Paragraph("REPUESTOS UTILIZADOS", styles['Section']))
    recam_data = [['Nombre', 'Cantidad', 'Fecha']]
    for r in preventivo.recambios.all():
        recam_data.append([
            r.nombre if r.nombre else '-',
            str(r.cantidad) if r.cantidad else '-',
            r.fecha.strftime('%d/%m/%Y %H:%M') if r.fecha else '-'
        ])
    if len(recam_data) == 1:
        recam_data.append(['-', '-', '-'])
    
    recam_table = Table(recam_data, colWidths=[10*cm, 3*cm, 4*cm])
    recam_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0d6efd')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#dee2e6')),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5),
    ]))
    story.append(recam_table)
    story.append(Spacer(1, 10))
    
    # Fotos
    if preventivo.fotos.all():
        story.append(Paragraph("FOTOGRAFÍAS", styles['Section']))
        story.append(Paragraph(f"{preventivo.fotos.count()} foto(s) adjunta(s) - Ver en la aplicación", styles.get('Normal')))
    
    doc.build(story)
    
    response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="preventivo_{preventivo.codigo}.pdf"'
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
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=1.5*cm, leftMargin=1.5*cm, topMargin=1.5*cm, bottomMargin=1.5*cm)
    
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name='TitleCode', alignment=TA_CENTER, fontSize=24, spaceAfter=20, textColor=colors.HexColor('#dc3545')))
    styles.add(ParagraphStyle(name='Section', fontSize=12, textColor=colors.HexColor('#dc3545'), spaceBefore=10, spaceAfter=5, fontName='Helvetica-Bold'))
    
    story = []
    
    # Titulo principal
    title_table = Table([['HOJA DE CORRECTIVO']], colWidths=[17*cm])
    title_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#dc3545')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 16),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
    ]))
    story.append(title_table)
    story.append(Spacer(1, 10))
    
    # Codigo PDS
    story.append(Paragraph(f"PDS {correctivo.codigo}", styles['TitleCode']))
    story.append(Spacer(1, 10))
    
    # Informacion general
    story.append(Paragraph("INFORMACIÓN GENERAL", styles['Section']))
    
    info_data = [
        ['Automatismo:', correctivo.automatismo.codigo if correctivo.automatismo else '-'],
        ['Técnico:', correctivo.tecnico.username if correctivo.tecnico else '-'],
        ['Fecha Inicio:', correctivo.fecha_inicio.strftime('%d/%m/%Y') if correctivo.fecha_inicio else '-'],
        ['Hora Inicio:', correctivo.hora_inicio.strftime('%H:%M') if correctivo.hora_inicio else '-'],
        ['Fecha Fin:', correctivo.fecha_fin.strftime('%d/%m/%Y %H:%M') if correctivo.fecha_fin else '-'],
        ['Estado:', correctivo.get_estado_display() if correctivo.estado else '-'],
    ]
    
    info_table = Table(info_data, colWidths=[5*cm, 12*cm])
    info_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#e9ecef')),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#dee2e6')),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(info_table)
    story.append(Spacer(1, 10))
    
    # Tiempo Total
    story.append(Paragraph("TIEMPO TOTAL", styles['Section']))
    tiempo_text = '-'
    if correctivo.tiempo:
        total_seconds = int(correctivo.tiempo.total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        tiempo_text = f'{hours}h {minutes}m {seconds}s'
    
    tiempo_table = Table([[tiempo_text]], colWidths=[17*cm])
    tiempo_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f8f9fa')),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#dee2e6')),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 14),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
    ]))
    story.append(tiempo_table)
    story.append(Spacer(1, 10))
    
    # Descripcion de la averia
    story.append(Paragraph("DESCRIPCIÓN DE LA AVERÍA", styles['Section']))
    desc_text = correctivo.descripcion if correctivo.descripcion else 'Sin descripción'
    desc_table = Table([[desc_text]], colWidths=[17*cm], rowHeights=[60])
    desc_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.white),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#dee2e6')),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(desc_table)
    story.append(Spacer(1, 10))
    
    # Solucion
    story.append(Paragraph("SOLUCIÓN APLICADA", styles['Section']))
    sol_text = correctivo.solucion if correctivo.solucion else 'Sin solución registrada'
    sol_table = Table([[sol_text]], colWidths=[17*cm], rowHeights=[60])
    sol_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.white),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#dee2e6')),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(sol_table)
    story.append(Spacer(1, 10))
    
    # Deficiencias
    story.append(Paragraph("DEFICIENCIAS", styles['Section']))
    defic_data = [['Tipo', 'Severidad', 'Descripción', 'Fecha']]
    for d in correctivo.deficiencias.all():
        defic_data.append([
            d.get_tipo_display() if d.tipo else '-',
            d.get_severidad_display() if d.severidad else '-',
            d.descripcion if d.descripcion else '-',
            d.fecha.strftime('%d/%m/%Y %H:%M') if d.fecha else '-'
        ])
    if len(defic_data) == 1:
        defic_data.append(['-', '-', 'Sin deficiencias registradas', '-'])
    
    defic_table = Table(defic_data, colWidths=[3*cm, 3*cm, 8*cm, 3*cm])
    defic_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#dc3545')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#dee2e6')),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5),
    ]))
    story.append(defic_table)
    story.append(Spacer(1, 10))
    
    # Recambios
    story.append(Paragraph("REPUESTOS UTILIZADOS", styles['Section']))
    recam_data = [['Nombre', 'Cantidad', 'Fecha']]
    for r in correctivo.recambios.all():
        recam_data.append([
            r.nombre if r.nombre else '-',
            str(r.cantidad) if r.cantidad else '-',
            r.fecha.strftime('%d/%m/%Y %H:%M') if r.fecha else '-'
        ])
    if len(recam_data) == 1:
        recam_data.append(['-', '-', '-'])
    
    recam_table = Table(recam_data, colWidths=[10*cm, 3*cm, 4*cm])
    recam_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#dc3545')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#dee2e6')),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5),
    ]))
    story.append(recam_table)
    
    doc.build(story)
    
    response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="correctivo_{correctivo.codigo}.pdf"'
    return response
