import os
from datetime import timedelta
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from prestamos.models import Laboratorio,Equipo,Prestamo

class Command(BaseCommand):
 help='Genera datos ficticios de demostración de manera idempotente'
 @transaction.atomic
 def handle(self,*args,**kwargs):
  User=get_user_model()
  for nombre in ('Administrador','Docente','Asistente'):Group.objects.get_or_create(name=nombre)
  perfiles=[('admin_lab','Administrador'),('docente01','Docente'),('docente02','Docente'),('docente03','Docente'),('asistente01','Asistente')]
  demo_password=os.getenv('DEMO_PASSWORD')
  for nombre,rol in perfiles:
   u,creado=User.objects.get_or_create(username=nombre,defaults={'email':f'{nombre}@uncp.edu.pe','first_name':nombre.title()})
   u.groups.add(Group.objects.get(name=rol))
   if rol=='Administrador' and not u.is_staff:
    u.is_staff=True;u.is_superuser=True;u.save(update_fields=['is_staff','is_superuser'])
   if demo_password and creado:u.set_password(demo_password);u.save(update_fields=['password'])
  labs=[Laboratorio.objects.get_or_create(nombre=f'Laboratorio {i}')[0] for i in range(1,6)]
  nombres=[('Laptop Dell','Dell','Latitude','Laptop',3),('Proyector Epson','Epson','X49','Proyector',2),('Cámara Canon','Canon','EOS','Cámara',2),('Kit Arduino','Arduino','UNO','Kit',4),('Router Cisco','Cisco','2911','Router',2),('Switch TP-Link','TP-Link','SG108','Switch',2),('Laptop Lenovo','Lenovo','ThinkPad','Laptop',3),('Proyector BenQ','BenQ','MX560','Proyector',2),('Cámara Logitech','Logitech','C920','Cámara',2),('Kit Raspberry','Raspberry','Pi 4','Kit',3)]
  equipos=[]
  for i,(nombre,marca,modelo,categoria,stock) in enumerate(nombres,1):
   equipo,_=Equipo.objects.get_or_create(codigo=f'UNCP-{i:04d}',defaults={'nombre':nombre,'marca':marca,'modelo':modelo,'categoria':categoria,'laboratorio':labs[(i-1)%5],'ultimo_mantenimiento':timezone.localdate()-timedelta(days=i*9),'stock_total':stock})
   equipos.append(equipo)
  now=timezone.now()
  docentes=list(User.objects.filter(username__in=['docente01','docente02','docente03']).order_by('username'))
  asistente=User.objects.get(username='asistente01')
  for i in range(15):
   docente=docentes[i%3];equipo=equipos[i%10]
   # 3 activos por cada docente; 2 por equipo como máximo
   activo=i<9
   fecha=now-timedelta(days=12+i)
   prevista=(now-timedelta(days=3+i)) if activo and i%2==0 else (now+timedelta(days=2+i)) if activo else (fecha+timedelta(days=3))
   defaults={'docente':docente,'equipo':equipo,'cantidad':1,'fecha_prestamo':fecha,'fecha_devolucion_prevista':prevista,'estado':Prestamo.Estado.ACTIVO if activo else Prestamo.Estado.DEVUELTO,'fecha_devolucion_real':None if activo else (fecha+timedelta(days=2)),'estado_retorno':'' if activo else Equipo.Estado.OPERATIVO,'registrado_por':asistente}
   Prestamo.objects.get_or_create(observaciones=f'DEMO-PRESTAMO-{i+1:02d}',defaults=defaults)
  self.stdout.write(self.style.SUCCESS('Datos demo listos: 10 equipos, 5 usuarios, 15 préstamos (idempotente).'))
  if demo_password:self.stdout.write('Contraseña DEMO_PASSWORD aplicada solo a usuarios nuevos.')
  else:self.stdout.write(self.style.WARNING('Usuarios nuevos sin contraseña utilizable. Define DEMO_PASSWORD y vuelve a crear los usuarios o usa changepassword.'))
