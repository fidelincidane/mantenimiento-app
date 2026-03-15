from django.urls import path
from . import views

urlpatterns = [
    path('', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('automatismos/', views.lista_automatismos, name='automatismos'),
    path('automatismo/crear/', views.crear_automatismo, name='crear_automatismo'),
    
    # Preventivos
    path('preventivo/nuevo/', views.crear_preventivo, name='crear_preventivo'),
    path('preventivo/<int:id>/', views.detalle_preventivo, name='detalle_preventivo'),
    path('preventivo/<int:id>/finalizar/', views.finalizar_preventivo, name='finalizar_preventivo'),
    path('preventivo/<int:id>/parar/', views.parar_preventivo, name='parar_preventivo'),
    path('preventivo/<int:id>/reanudar/', views.reanudar_preventivo, name='reanudar_preventivo'),
    path('preventivo/<int:id>/deficiencia/', views.agregar_deficiencia, name='agregar_deficiencia'),
    path('preventivo/<int:id>/recambio/', views.agregar_recambio, name='agregar_recambio'),
    path('preventivo/<int:id>/foto/', views.agregar_foto, name='agregar_foto'),
    
    # Correctivos
    path('correctivo/nuevo/', views.crear_correctivo, name='crear_correctivo'),
    path('correctivo/<int:id>/', views.detalle_correctivo, name='detalle_correctivo'),
    path('correctivo/<int:id>/finalizar/', views.finalizar_correctivo, name='finalizar_correctivo'),
    path('correctivo/<int:id>/parar/', views.parar_correctivo, name='parar_correctivo'),
    path('correctivo/<int:id>/reanudar/', views.reanudar_correctivo, name='reanudar_correctivo'),
    path('correctivo/<int:id>/deficiencia/', views.agregar_deficiencia_correctivo, name='agregar_deficiencia_correctivo'),
    path('correctivo/<int:id>/recambio/', views.agregar_recambio_correctivo, name='agregar_recambio_correctivo'),
    path('correctivo/<int:id>/foto/', views.agregar_foto_correctivo, name='agregar_foto_correctivo'),
    
    # Historial
    path('historial/', views.historial, name='historial'),
    path('historial/preventivo/<str:codigo_pds>/', views.detalle_historial_preventivo, name='detalle_historial_preventivo'),
    path('historial/correctivo/<str:codigo_pds>/', views.detalle_historial_correctivo, name='detalle_historial_correctivo'),
]
