from django.contrib import admin
from django.urls import path,include
urlpatterns=[path('admin/',admin.site.urls),path('',include('prestamos.urls'))]
admin.site.site_header='Laboratorios UNCP | Administración'
admin.site.site_title='Préstamos UNCP'
admin.site.index_title='Gestión del laboratorio'
