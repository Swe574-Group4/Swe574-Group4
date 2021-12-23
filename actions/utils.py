import datetime
from django.utils import timezone
from django.contrib.contenttypes.models import ContentType
from .models import Action


def create_action(user, verb, activity_json, target=None):
    # check for any similar aciton made in the last minute
    now = timezone.now()
    last_minute = now - datetime.timedelta(seconds=60)
    similar_actions = Action.objects.filter(user_id=user.id,
                                            verb=verb,
                                            created__gte=last_minute)
    if target:
        target_ct = ContentType.objects.get_for_model(target)
        print('target_ct',target_ct)
        if 'article' in str(target_ct) :
            print('if')
            similar_actions = similar_actions.filter(target_ct=target_ct,
                                                     target_id=target.article_id)
        else:
            print('else')
            similar_actions = similar_actions.filter(target_ct=target_ct,
                                                 target_id=target.id)
    if not similar_actions:
        # no existing actions found
        action = Action(user=user, verb=verb, target=target, action_json=activity_json)
        action.save()
        return True
    return False


def delete_action(user, verb, target=None):
    # no existing actions found
    action = Action.objects.filter(user_id=user.id, verb=verb, target_id=target.id)
    action.delete()
    return True