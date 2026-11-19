import logging
from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse
from django.utils import timezone
from .models import Auditoria,Prestamo
logger=logging.getLogger(__name__)
class AuditoriaMiddleware:
 def __init__(self,get_response):self.get_response=get_response
 def __call__(self,request):
  if request.user.is_authenticated:
   if not request.user.is_active:
    from django.contrib.auth import logout
    logout(request)
    return redirect('login')
   if request.session.get('alertar_vencidos'):
    del request.session['alertar_vencidos']
    vencidos=Prestamo.objects.filter(docente=request.user,estado=Prestamo.Estado.ACTIVO,fecha_devolucion_prevista__lt=timezone.now()).count()
    if vencidos:messages.warning(request,f'Atención: tienes {vencidos} préstamo(s) vencido(s).')
  response=self.get_response(request)
  if response.status_code==403:
   u=request.user
   Auditoria.objects.create(usuario=u if u.is_authenticated else None,accion='ACCESO_DENEGADO',ip=request.META.get('REMOTE_ADDR') or None,detalle=request.path[:255])
   logger.warning('Acceso denegado: usuario=%s ruta=%s',u if u.is_authenticated else 'anónimo',request.path)
  return response
