from django.db import models
from django.db.models.deletion import CASCADE
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.db.models import JSONField

# This model keeps all the actions in the application
# It is created separately from the main application.
# Even if you remove the application medicles,
# You can keep using this one.
class Action(models.Model):
    activity = (('1', 'Follow'),
                ('2', 'Unfollow'),
                ('3', 'Search'),
                ('4', 'Favourite'),
                ('5', 'Unfavourite'))

    user = models.ForeignKey('auth.User',
                             related_name='actions',
                             db_index=True,
                             on_delete=CASCADE)
    verb = models.CharField(max_length=255, choices=activity)
    target_ct = models.ForeignKey(ContentType,
                                  blank=True,
                                  null=True,
                                  related_name='target_obj',
                                  on_delete=models.CASCADE)
    target_id = models.PositiveIntegerField(null=True,
                                            blank=True,
                                            db_index=True)
    target = GenericForeignKey('target_ct', 'target_id')
    created = models.DateTimeField(auto_now_add=True,
                                db_index=True)
    action_json = JSONField(default=dict)

    class Meta:
        ordering = ('-created',)