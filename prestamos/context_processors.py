from .permissions import tiene_rol
def roles(request):
 u=request.user
 return {'es_admin':tiene_rol(u,'Administrador'),'es_docente':tiene_rol(u,'Docente'),'es_asistente':tiene_rol(u,'Asistente')}
