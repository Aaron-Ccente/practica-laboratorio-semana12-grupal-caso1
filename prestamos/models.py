from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone

class Laboratorio(models.Model):
 nombre=models.CharField(max_length=90,unique=True)
 def __str__(self): return self.nombre

class Equipo(models.Model):
 class Estado(models.TextChoices):
  OPERATIVO='operativo','Operativo'
  MANTENIMIENTO='mantenimiento','Mantenimiento'
  BAJA='baja','Dado de baja'
 codigo=models.CharField(max_length=35,unique=True,verbose_name='Código patrimonial')
 nombre=models.CharField(max_length=120)
 marca=models.CharField(max_length=80)
 modelo=models.CharField(max_length=80)
 categoria=models.CharField(max_length=80)
 estado=models.CharField(max_length=20,choices=Estado.choices,default=Estado.OPERATIVO)
 laboratorio=models.ForeignKey(Laboratorio,on_delete=models.PROTECT,related_name='equipos')
 ultimo_mantenimiento=models.DateField(null=True,blank=True)
 stock_total=models.PositiveIntegerField(default=1,validators=[MinValueValidator(1)])
 def __str__(self): return f'{self.codigo} · {self.nombre}'
 @property
 def stock_disponible(self):
  ocupado=self.prestamos.filter(estado=Prestamo.Estado.ACTIVO).aggregate(t=models.Sum('cantidad'))['t'] or 0
  return max(0,self.stock_total-ocupado)
 @property
 def dias_desde_mantenimiento(self):
  return (timezone.localdate()-self.ultimo_mantenimiento).days if self.ultimo_mantenimiento else None

class Prestamo(models.Model):
 class Estado(models.TextChoices):
  ACTIVO='activo','Activo'
  DEVUELTO='devuelto','Devuelto'
 docente=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.PROTECT,related_name='prestamos_docente')
 equipo=models.ForeignKey(Equipo,on_delete=models.PROTECT,related_name='prestamos')
 cantidad=models.PositiveIntegerField(default=1,validators=[MinValueValidator(1)])
 fecha_prestamo=models.DateTimeField(default=timezone.now)
 fecha_devolucion_prevista=models.DateTimeField()
 fecha_devolucion_real=models.DateTimeField(null=True,blank=True)
 estado=models.CharField(max_length=10,choices=Estado.choices,default=Estado.ACTIVO)
 observaciones=models.TextField(blank=True)
 estado_retorno=models.CharField(max_length=20,choices=Equipo.Estado.choices,blank=True)
 registrado_por=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.SET_NULL,null=True,blank=True,related_name='prestamos_registrados')
 class Meta:
  ordering=['-fecha_prestamo']
 def __str__(self): return f'Préstamo #{self.pk} | {self.equipo.codigo}'
 @property
 def vencido(self): return self.estado==self.Estado.ACTIVO and self.fecha_devolucion_prevista<timezone.now()
 @property
 def dias_retraso(self):
  fin=self.fecha_devolucion_real or timezone.now()
  if fin<=self.fecha_devolucion_prevista:return 0
  if self.estado==self.Estado.ACTIVO or self.fecha_devolucion_real:
   return (fin.date()-self.fecha_devolucion_prevista.date()).days or 1
  return 0
 def clean(self):
  errors={}
  if self.fecha_prestamo and self.fecha_devolucion_prevista and self.fecha_devolucion_prevista<=self.fecha_prestamo:
   errors['fecha_devolucion_prevista']='Debe ser posterior al préstamo.'
  if self.estado==self.Estado.DEVUELTO and not self.fecha_devolucion_real:
   errors['fecha_devolucion_real']='Una devolución debe tener fecha real.'
  if errors:raise ValidationError(errors)

class Auditoria(models.Model):
 usuario=models.ForeignKey(settings.AUTH_USER_MODEL,null=True,blank=True,on_delete=models.SET_NULL)
 fecha=models.DateTimeField(default=timezone.now,db_index=True)
 ip=models.GenericIPAddressField(null=True,blank=True)
 accion=models.CharField(max_length=100)
 detalle=models.CharField(max_length=255,blank=True)
 class Meta:ordering=['-fecha']
 def __str__(self):return f'{self.fecha} {self.accion}'
