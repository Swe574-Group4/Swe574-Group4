from django import template
from actions.models import Action

register = template.Library()

@register.simple_tag
def total_actions():
    return Action.objects.all().count()

@register.filter(name='follow')
def is_following_user(target, user):
   target_users = Action.objects.filter(target_id=target, verb=1)
   print("Target Users:", target_users)
   print("Target:", target)
   print("User:", user)
   for target_user in target_users:
       print("Target User:", target_user.user)
       print("User:", user)
       if str(target_user.user) in user.username:
           print(True)
           return True
   return False
