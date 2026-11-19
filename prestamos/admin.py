from django.contrib import admin,messages
from django.db.models import Count
from django.core.mail import send_mail
from django.utils.html import format_html
from django.utils import timezone
from .models import Laboratorio,Equipo,Prestamo,Auditoria
from .permissions import tiene_rol
from .services import auditar

@admin.register(Laboratorio)
class LaboratorioAdmin(admin.ModelAdmin):
 search_fields=['nombre']

@admin.action(description='Marcar como en mantenimiento')
def poner_mantenimiento(modeladmin,request,queryset):
 cantidad=queryset.update(estado=Equipo.Estado.MANTENIMIENTO)
 for equipo in queryset:auditar(request,'MANTENIMIENTO',equipo.codigo)
 modeladmin.message_user(request,f'{cantidad} equipo(s) actualizados.')

@admin.register(Equipo)
class EquipoAdmin(admin.ModelAdmin):
 list_display=['codigo','nombre','categoria','laboratorio','estado_visual','stock_total','disponibles','dias_mantenimiento']
 list_filter=['laboratorio','estado','categoria']
 search_fields=['codigo','nombre','categoria']
 list_select_related=['laboratorio']
 actions=[poner_mantenimiento]
 def estado_visual(self,obj):
  colores={'operativo':'#17844b','mantenimiento':'#c77708','baja':'#b82727'}
  return format_html('<strong style="color:{}">{}</strong>',colores[obj.estado],obj.get_estado_display())
 estado_visual.short_description='Estado'
 def disponibles(self,obj):return obj.stock_disponible
 def dias_mantenimiento(self,obj):return obj.dias_desde_mantenimiento if obj.dias_desde_mantenimiento is not None else 'Sin registro'
 dias_mantenimiento.short_description='Días desde mantenimiento'
 def has_delete_permission(self,request,obj=None):return tiene_rol(request.user,'Administrador')
 def delete_model(self,request,obj):
  codigo=obj.codigo
  super().delete_model(request,obj)
  auditar(request,'ELIMINAR_EQUIPO',codigo)
 def delete_queryset(self,request,queryset):
  codigos=list(queryset.values_list('codigo',flat=True))
  super().delete_queryset(request,queryset)
  for codigo in codigos:auditar(request,'ELIMINAR_EQUIPO',codigo)

@admin.action(description='Enviar recordatorio de devolución')
def enviar_recordatorios(modeladmin,request,queryset):
 enviados=0
 for prestamo in queryset.select_related('docente','equipo').filter(estado=Prestamo.Estado.ACTIVO):
  if prestamo.docente.email:
   send_mail('Recordatorio de devolución UNCP',f'Recuerda devolver {prestamo.equipo.nombre} antes del {prestamo.fecha_devolucion_prevista:%d/%m/%Y %H:%M}.',None,[prestamo.docente.email]);enviados+=1
 auditar(request,'RECORDATORIOS',f'{enviados} recordatorios simulados')
 modeladmin.message_user(request,f'{enviados} recordatorios enviados a consola.')

@admin.register(Prestamo)
class PrestamoAdmin(admin.ModelAdmin):
 list_display=['id','docente','equipo','fecha_prestamo','fecha_devolucion_prevista','estado','dias_retraso']
 list_filter=['fecha_prestamo','fecha_devolucion_prevista','estado','docente']
 search_fields=['equipo__codigo','docente__username','docente__first_name','docente__last_name']
 list_select_related=['docente','equipo']
 actions=[enviar_recordatorios]
 readonly_fields=['registrado_por','fecha_devolucion_real','estado_retorno']
 def get_queryset(self,request):
  qs=super().get_queryset(request)
  if tiene_rol(request.user,'Administrador') or tiene_rol(request.user,'Asistente'):return qs
  if tiene_rol(request.user,'Docente'):return qs.filter(docente=request.user)
  return qs.none()
 def has_view_permission(self,request,obj=None):
  return tiene_rol(request.user,'Administrador') or tiene_rol(request.user,'Asistente') or (obj is not None and obj.docente_id==request.user.pk)
 def has_add_permission(self,request):return False # usar formulario con validaciones transaccionales
 def has_change_permission(self,request,obj=None):return False
 def has_delete_permission(self,request,obj=None):return False

@admin.register(Auditoria)
class AuditoriaAdmin(admin.ModelAdmin):
 list_display=['fecha','usuario','ip','accion','detalle']
 list_filter=['accion','fecha']
 search_fields=['usuario__username','accion','detalle']
 readonly_fields=['usuario','fecha','ip','accion','detalle']
 def has_module_permission(self,request):return tiene_rol(request.user,'Administrador')
 def has_view_permission(self,request,obj=None):return tiene_rol(request.user,'Administrador')
 def has_add_permission(self,request):return False
 def has_change_permission(self,request,obj=None):return False
 def has_delete_permission(self,request,obj=None):return False
