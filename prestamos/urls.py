from django.urls import path
from . import views
urlpatterns=[
 path('',views.inicio,name='inicio'),path('catalogo/',views.catalogo,name='catalogo'),
 path('login/',views.InicioSesion.as_view(),name='login'),path('logout/',views.salir,name='logout'),
 path('panel/',views.panel,name='panel'),path('equipos/',views.listado_equipos,name='equipos'),
 path('equipos/nuevo/',views.nuevo_equipo,name='nuevo_equipo'),path('equipos/<int:pk>/editar/',views.editar_equipo,name='editar_equipo'),
 path('equipos/<int:pk>/eliminar/',views.borrar_equipo,name='borrar_equipo'),
 path('prestamos/solicitar/',views.solicitar,name='solicitar'),path('prestamos/',views.historial,name='historial'),
 path('prestamos/<int:pk>/devolver/',views.devolver,name='devolver'),path('auditoria/',views.auditoria,name='auditoria')]
