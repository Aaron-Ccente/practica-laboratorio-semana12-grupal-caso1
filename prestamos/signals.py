from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver
@receiver(user_logged_in)
def marcar_alerta(sender,request,user,**kwargs):
 request.session['alertar_vencidos']=True
