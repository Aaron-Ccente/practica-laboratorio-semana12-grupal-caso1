from django.contrib.auth.decorators import user_passes_test
from django.core.exceptions import PermissionDenied

def tiene_rol(user,rol):
 return user.is_authenticated and (user.is_superuser or user.groups.filter(name=rol).exists())

def rol_requerido(*roles):
 def decorator(view):
  from functools import wraps
  @wraps(view)
  def wrapped(request,*args,**kwargs):
   if not request.user.is_authenticated:
    from django.shortcuts import redirect
    from django.contrib.auth.views import redirect_to_login
    return redirect_to_login(request.get_full_path())
   if not any(tiene_rol(request.user,rol) for rol in roles):raise PermissionDenied('No tienes permisos para esta acción.')
   return view(request,*args,**kwargs)
  return wrapped
 return decorator
