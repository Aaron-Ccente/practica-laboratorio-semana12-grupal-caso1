from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView,LogoutView
from django.core.exceptions import ValidationError,PermissionDenied
from django.db.models import Count
from django.http import Http404
from django.shortcuts import get_object_or_404,redirect,render
from django.utils import timezone
from django.views.decorators.http import require_POST
from .models import Equipo,Prestamo,Auditoria
from .forms import EquipoForm,PrestamoForm,DevolucionForm
from .permissions import rol_requerido,tiene_rol
from .services import crear_prestamo,devolver_prestamo,auditar

class InicioSesion(LoginView):
 template_name='registration/login.html'
 redirect_authenticated_user=True

@require_POST
def salir(request):
 from django.contrib.auth import logout
 logout(request)
 messages.success(request,'Has cerrado sesión.')
 return redirect('inicio')

def inicio(request):
 return render(request,'prestamos/inicio.html',{'total_equipos':Equipo.objects.count(),'operativos':Equipo.objects.filter(estado='operativo').count()})

def catalogo(request):
 equipos=Equipo.objects.select_related('laboratorio').all().order_by('nombre')
 q=request.GET.get('q','').strip()
 if q:
  from django.db.models import Q
  equipos=equipos.filter(Q(nombre__icontains=q)|Q(codigo__icontains=q)|Q(categoria__icontains=q))
 return render(request,'prestamos/catalogo.html',{'equipos':equipos,'q':q})

@login_required
def panel(request):
 if tiene_rol(request.user,'Administrador'):
  return render(request,'prestamos/panel.html',{'tipo':'Administrador','total_equipos':Equipo.objects.count(),'total_prestamos':Prestamo.objects.count(),'activos':Prestamo.objects.filter(estado='activo').count(),'vencidos':Prestamo.objects.filter(estado='activo',fecha_devolucion_prevista__lt=timezone.now()).count()})
 if tiene_rol(request.user,'Docente'):
  propios=Prestamo.objects.filter(docente=request.user)
  return render(request,'prestamos/panel.html',{'tipo':'Docente','activos':propios.filter(estado='activo').count(),'vencidos':propios.filter(estado='activo',fecha_devolucion_prevista__lt=timezone.now()).count()})
 if tiene_rol(request.user,'Asistente'):
  return render(request,'prestamos/panel.html',{'tipo':'Asistente','activos':Prestamo.objects.filter(estado='activo').count(),'vencidos':Prestamo.objects.filter(estado='activo',fecha_devolucion_prevista__lt=timezone.now()).count()})
 raise PermissionDenied('Sin rol autorizado.')

@rol_requerido('Administrador','Asistente')
def listado_equipos(request):
 return render(request,'prestamos/catalogo.html',{'equipos':Equipo.objects.select_related('laboratorio'),'administrar':True})

@rol_requerido('Administrador')
def nuevo_equipo(request):
 form=EquipoForm(request.POST or None)
 if request.method=='POST' and form.is_valid():
  equipo=form.save();auditar(request,'CREAR_EQUIPO',equipo.codigo)
  messages.success(request,'Equipo creado correctamente.');return redirect('equipos')
 return render(request,'prestamos/formulario.html',{'form':form,'titulo':'Registrar equipo'})

@rol_requerido('Administrador')
def editar_equipo(request,pk):
 equipo=get_object_or_404(Equipo,pk=pk)
 form=EquipoForm(request.POST or None,instance=equipo)
 if request.method=='POST' and form.is_valid():
  form.save();auditar(request,'EDITAR_EQUIPO',equipo.codigo)
  messages.success(request,'Equipo actualizado.');return redirect('equipos')
 return render(request,'prestamos/formulario.html',{'form':form,'titulo':'Editar equipo'})

@rol_requerido('Administrador')
def borrar_equipo(request,pk):
 equipo=get_object_or_404(Equipo,pk=pk)
 if request.method=='POST':
  if equipo.prestamos.exists():
   messages.error(request,'No se puede eliminar un equipo con historial de préstamos.');return redirect('equipos')
  codigo=equipo.codigo;equipo.delete();auditar(request,'ELIMINAR_EQUIPO',codigo)
  messages.success(request,'Equipo eliminado.');return redirect('equipos')
 return render(request,'prestamos/confirmar.html',{'objeto':equipo})

@rol_requerido('Docente','Asistente','Administrador')
def solicitar(request):
 form=PrestamoForm(request.POST or None,usuario=request.user)
 if request.method=='POST' and form.is_valid():
  try:
   prestamo=crear_prestamo(request,form.cleaned_data)
  except ValidationError as exc:
   form.add_error(None,exc)
  else:
   messages.success(request,f'Préstamo #{prestamo.pk} registrado.');return redirect('historial')
 return render(request,'prestamos/formulario.html',{'form':form,'titulo':'Solicitar préstamo'})

@rol_requerido('Asistente')
def devolver(request,pk):
 prestamo=get_object_or_404(Prestamo.objects.select_related('docente','equipo'),pk=pk)
 if prestamo.estado!=Prestamo.Estado.ACTIVO:raise Http404('Préstamo ya devuelto.')
 form=DevolucionForm(request.POST or None)
 if request.method=='POST' and form.is_valid():
  try:devolver_prestamo(request,prestamo.pk,form.cleaned_data)
  except ValidationError as exc:form.add_error(None,exc)
  else:
   messages.success(request,'Devolución registrada.');return redirect('historial')
 return render(request,'prestamos/formulario.html',{'form':form,'titulo':f'Devolver préstamo #{pk}'})

@rol_requerido('Docente','Asistente','Administrador')
def historial(request):
 prestamos=Prestamo.objects.select_related('docente','equipo','equipo__laboratorio')
 if tiene_rol(request.user,'Docente') and not tiene_rol(request.user,'Administrador') and not tiene_rol(request.user,'Asistente'):
  prestamos=prestamos.filter(docente=request.user)
 return render(request,'prestamos/historial.html',{'prestamos':prestamos})

@rol_requerido('Administrador')
def auditoria(request):
 return render(request,'prestamos/auditoria.html',{'registros':Auditoria.objects.select_related('usuario')[:200]})
