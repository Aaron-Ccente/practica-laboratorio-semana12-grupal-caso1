from django import forms
from django.utils import timezone
from django.utils.html import strip_tags
from django.core.exceptions import ValidationError
from django.contrib.auth.models import Group
from .models import Equipo,Prestamo

class EquipoForm(forms.ModelForm):
 class Meta:
  model=Equipo
  fields=['codigo','nombre','marca','modelo','categoria','estado','laboratorio','ultimo_mantenimiento','stock_total']
  widgets={'ultimo_mantenimiento':forms.DateInput(attrs={'type':'date'})}

class PrestamoForm(forms.ModelForm):
 class Meta:
  model=Prestamo
  fields=['docente','equipo','cantidad','fecha_devolucion_prevista','observaciones']
  widgets={'fecha_devolucion_prevista':forms.DateTimeInput(attrs={'type':'datetime-local'},format='%Y-%m-%dT%H:%M'),'observaciones':forms.Textarea(attrs={'rows':3})}
 def __init__(self,*args,usuario=None,**kwargs):
  super().__init__(*args,**kwargs)
  self.usuario=usuario
  self.fields['fecha_devolucion_prevista'].input_formats=['%Y-%m-%dT%H:%M','%Y-%m-%d %H:%M:%S']
  from django.contrib.auth import get_user_model
  User=get_user_model()
  self.fields['docente'].queryset=User.objects.filter(groups__name='Docente',is_active=True).distinct()
  self.fields['equipo'].queryset=Equipo.objects.filter(estado=Equipo.Estado.OPERATIVO)
  if usuario and usuario.groups.filter(name='Docente').exists() and not usuario.is_superuser:
   self.fields['docente'].queryset=User.objects.filter(pk=usuario.pk)
   self.fields['docente'].initial=usuario.pk
   self.fields['docente'].widget=forms.HiddenInput()
 def clean_observaciones(self):return strip_tags(self.cleaned_data.get('observaciones','')).strip()
 def clean_fecha_devolucion_prevista(self):
  valor=self.cleaned_data['fecha_devolucion_prevista']
  if valor<=timezone.now():raise ValidationError('La devolución debe estar en el futuro.')
  return valor
 def clean(self):
  datos=super().clean()
  docente=datos.get('docente');equipo=datos.get('equipo');cantidad=datos.get('cantidad')
  if self.usuario and self.usuario.groups.filter(name='Docente').exists() and not self.usuario.is_superuser and docente!=self.usuario:
   self.add_error('docente','Solo puedes solicitar préstamos a tu nombre.')
  if docente and Prestamo.objects.filter(docente=docente,estado=Prestamo.Estado.ACTIVO).exclude(pk=self.instance.pk).count()>=3:
   self.add_error('docente','El docente ya tiene tres préstamos activos.')
  if equipo:
   if equipo.estado!=Equipo.Estado.OPERATIVO:self.add_error('equipo','El equipo no está operativo.')
   if cantidad and cantidad>equipo.stock_disponible:self.add_error('cantidad','Cantidad superior al stock disponible.')
  return datos

class DevolucionForm(forms.Form):
 fecha_devolucion_real=forms.SplitDateTimeField(widget=forms.SplitDateTimeWidget(date_attrs={'type':'date'},time_attrs={'type':'time'}),initial=timezone.localtime)
 estado_retorno=forms.ChoiceField(choices=Equipo.Estado.choices,label='Estado al retornar')
 observaciones=forms.CharField(required=False,widget=forms.Textarea(attrs={'rows':3}))
 def clean_observaciones(self):return strip_tags(self.cleaned_data.get('observaciones','')).strip()
 def clean_fecha_devolucion_real(self):
  valor=self.cleaned_data['fecha_devolucion_real']
  if valor>timezone.now()+__import__('datetime').timedelta(minutes=1):raise ValidationError('No puede ser una fecha futura.')
  return valor
