from datetime import timedelta
from unittest.mock import patch
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.test import TestCase,override_settings
from django.urls import reverse
from django.utils import timezone
from .forms import PrestamoForm
from .models import Equipo,Laboratorio,Prestamo,Auditoria
from .services import crear_prestamo,devolver_prestamo

class PruebaCaso1(TestCase):
 @classmethod
 def setUpTestData(cls):
  cls.docentes=Group.objects.create(name='Docente')
  cls.asistentes=Group.objects.create(name='Asistente')
  cls.admins=Group.objects.create(name='Administrador')
  User=get_user_model()
  cls.docente=User.objects.create_user('profesor',password='Prueba123!')
  cls.otro=User.objects.create_user('otro',password='Prueba123!')
  cls.asistente=User.objects.create_user('asistente',password='Prueba123!')
  cls.administrador=User.objects.create_user('jefe',password='Prueba123!',is_staff=True)
  cls.docente.groups.add(cls.docentes);cls.otro.groups.add(cls.docentes);cls.asistente.groups.add(cls.asistentes);cls.administrador.groups.add(cls.admins)
  cls.lab=Laboratorio.objects.create(nombre='Lab 1')
  cls.equipo=Equipo.objects.create(codigo='ABC001',nombre='Laptop',marca='Dell',modelo='X',categoria='Laptop',laboratorio=cls.lab,stock_total=3)
 def datos(self,**kw):
  d={'docente':self.docente,'equipo':self.equipo,'cantidad':1,'fecha_devolucion_prevista':timezone.now()+timedelta(days=2),'observaciones':'<b>Texto</b>'}
  d.update(kw);return d
 def req(self,user):
  from django.test import RequestFactory
  r=RequestFactory().post('/prestamos/solicitar/');r.user=user
  return r
 def test_equipo_codigo_unico(self):
  with self.assertRaises(IntegrityError):Equipo.objects.create(codigo='ABC001',nombre='Duplicado',marca='M',modelo='M',categoria='C',laboratorio=self.lab)
 def test_prestamo_y_stock(self):
  p=crear_prestamo(self.req(self.docente),self.datos())
  self.assertEqual(self.equipo.stock_disponible,2)
  self.assertEqual(p.docente,self.docente)
  self.assertTrue(Auditoria.objects.filter(accion='PRESTAMO').exists())
 def test_no_mas_de_tres(self):
  for i in range(3):crear_prestamo(self.req(self.docente),self.datos())
  with self.assertRaises(ValidationError):crear_prestamo(self.req(self.docente),self.datos())
 def test_rechaza_stock(self):
  with self.assertRaises(ValidationError):crear_prestamo(self.req(self.docente),self.datos(cantidad=5))
 def test_rechaza_no_operativo(self):
  self.equipo.estado='mantenimiento';self.equipo.save()
  with self.assertRaises(ValidationError):crear_prestamo(self.req(self.docente),self.datos())
 def test_validacion_fecha(self):
  form=PrestamoForm(data={'docente':self.docente.pk,'equipo':self.equipo.pk,'cantidad':1,'fecha_devolucion_prevista':(timezone.now()-timedelta(days=1)).strftime('%Y-%m-%dT%H:%M'),'observaciones':'texto'},usuario=self.asistente)
  self.assertFalse(form.is_valid())
 def test_sanitizacion(self):
  form=PrestamoForm(data={'docente':self.docente.pk,'equipo':self.equipo.pk,'cantidad':1,'fecha_devolucion_prevista':(timezone.now()+timedelta(days=2)).strftime('%Y-%m-%dT%H:%M'),'observaciones':'<script>alert(1)</script>'},usuario=self.asistente)
  self.assertTrue(form.is_valid(),form.errors)
  self.assertNotIn('<script>',form.cleaned_data['observaciones'])
 def test_devolucion(self):
  p=crear_prestamo(self.req(self.docente),self.datos())
  devolver_prestamo(self.req(self.asistente),p.pk,{'fecha_devolucion_real':timezone.now(),'estado_retorno':'operativo','observaciones':'bien'})
  p.refresh_from_db();self.assertEqual(p.estado,'devuelto');self.assertEqual(self.equipo.stock_disponible,3)
  self.assertTrue(Auditoria.objects.filter(accion='DEVOLUCION').exists())
 def test_docente_ve_solo_historial(self):
  Prestamo.objects.create(docente=self.otro,equipo=self.equipo,fecha_devolucion_prevista=timezone.now()+timedelta(days=3))
  self.client.force_login(self.docente)
  resp=self.client.get(reverse('historial'))
  self.assertEqual(resp.status_code,200)
  self.assertEqual(len(resp.context['prestamos']),0)
 def test_permisos_devolucion(self):
  p=Prestamo.objects.create(docente=self.docente,equipo=self.equipo,fecha_devolucion_prevista=timezone.now()+timedelta(days=3))
  self.client.force_login(self.docente)
  self.assertEqual(self.client.get(reverse('devolver',args=[p.pk])).status_code,403)
  self.assertTrue(Auditoria.objects.filter(accion='ACCESO_DENEGADO').exists())
 def test_permisos_eliminar(self):
  self.client.force_login(self.asistente)
  self.assertEqual(self.client.get(reverse('borrar_equipo',args=[self.equipo.pk])).status_code,403)
 def test_login_logout(self):
  self.assertTrue(self.client.login(username='profesor',password='Prueba123!'))
  self.assertEqual(self.client.post(reverse('logout')).status_code,302)
  self.assertNotIn('_auth_user_id',self.client.session)
 def test_sesion(self):
  from django.conf import settings
  self.assertEqual(settings.SESSION_COOKIE_AGE,1800)
  self.assertTrue(settings.SESSION_COOKIE_HTTPONLY)
  self.assertTrue(settings.SESSION_SAVE_EVERY_REQUEST)
 def test_middleware_alerta_vencidos(self):
  Prestamo.objects.create(docente=self.docente,equipo=self.equipo,fecha_devolucion_prevista=timezone.now()-timedelta(days=1))
  self.client.login(username='profesor',password='Prueba123!')
  response=self.client.get(reverse('panel'),follow=True)
  self.assertContains(response,'préstamo(s) vencido(s)')
 def test_admin_configuracion(self):
  from django.contrib import admin
  from .admin import enviar_recordatorios,poner_mantenimiento
  a=admin.site._registry[Prestamo];e=admin.site._registry[Equipo]
  self.assertIn('estado',a.list_filter)
  self.assertIn(enviar_recordatorios,a.actions)
  self.assertIn(poner_mantenimiento,e.actions)
 def test_catalogo_publico(self):
  self.assertEqual(self.client.get(reverse('catalogo')).status_code,200)
 def test_docente_no_puede_prestar_a_otro(self):
  f=PrestamoForm(data={'docente':self.otro.pk,'equipo':self.equipo.pk,'cantidad':1,'fecha_devolucion_prevista':(timezone.now()+timedelta(days=2)).strftime('%Y-%m-%dT%H:%M')},usuario=self.docente)
  self.assertFalse(f.is_valid())
