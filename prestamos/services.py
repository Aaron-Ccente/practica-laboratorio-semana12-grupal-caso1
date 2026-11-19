from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone
from django.db.models import Sum
from .models import Equipo,Prestamo,Auditoria

def ip_cliente(request):
 return request.META.get('REMOTE_ADDR') or None

def auditar(request,accion,detalle=''):
 return Auditoria.objects.create(usuario=request.user if request.user.is_authenticated else None,ip=ip_cliente(request),accion=accion,detalle=str(detalle)[:255])

@transaction.atomic
def crear_prestamo(request,datos):
 equipo=Equipo.objects.select_for_update().get(pk=datos['equipo'].pk)
 docente=datos['docente']
 from django.contrib.auth import get_user_model
 usuario=get_user_model().objects.select_for_update().get(pk=docente.pk)
 if not usuario.is_active or not usuario.groups.filter(name='Docente').exists():raise ValidationError('El usuario seleccionado no es un docente activo.')
 if Prestamo.objects.filter(docente=usuario,estado=Prestamo.Estado.ACTIVO).count()>=3:raise ValidationError('El docente ya tiene tres préstamos activos.')
 ocupado=Prestamo.objects.filter(equipo=equipo,estado=Prestamo.Estado.ACTIVO).aggregate(total=Sum('cantidad'))['total'] or 0
 if equipo.estado!=Equipo.Estado.OPERATIVO or equipo.stock_total-ocupado<datos['cantidad']:raise ValidationError('Equipo no disponible o stock insuficiente.')
 if datos['fecha_devolucion_prevista']<=timezone.now():raise ValidationError('Fecha de devolución inválida.')
 prestamo=Prestamo(docente=usuario,equipo=equipo,cantidad=datos['cantidad'],fecha_devolucion_prevista=datos['fecha_devolucion_prevista'],observaciones=datos.get('observaciones',''),registrado_por=request.user)
 prestamo.full_clean();prestamo.save()
 auditar(request,'PRESTAMO',f'Préstamo {prestamo.pk}: {equipo.codigo}, cantidad {prestamo.cantidad}')
 return prestamo

@transaction.atomic
def devolver_prestamo(request,prestamo_id,datos):
 prestamo=Prestamo.objects.select_for_update().select_related('equipo').get(pk=prestamo_id)
 if prestamo.estado!=Prestamo.Estado.ACTIVO:raise ValidationError('Este préstamo ya fue devuelto.')
 if datos['fecha_devolucion_real']<prestamo.fecha_prestamo:raise ValidationError('La devolución no puede ser anterior al préstamo.')
 prestamo.fecha_devolucion_real=datos['fecha_devolucion_real'];prestamo.estado_retorno=datos['estado_retorno'];prestamo.estado=Prestamo.Estado.DEVUELTO
 comentario=datos.get('observaciones','')
 if comentario:prestamo.observaciones=(prestamo.observaciones+'\nDevolución: '+comentario).strip()
 prestamo.full_clean();prestamo.save()
 if datos['estado_retorno']!=Equipo.Estado.OPERATIVO:
  equipo=Equipo.objects.select_for_update().get(pk=prestamo.equipo_id)
  equipo.estado=datos['estado_retorno'];equipo.save(update_fields=['estado'])
 auditar(request,'DEVOLUCION',f'Préstamo {prestamo.pk} devuelto, estado: {prestamo.estado_retorno}')
 return prestamo
