# Generated by Django 3.1.1 on 2021-12-20 16:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('actions', '0004_auto_20211220_1228'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='action',
            options={'ordering': ('-created',)},
        ),
        migrations.AlterField(
            model_name='action',
            name='action_json',
            field=models.JSONField(default=dict),
        ),
        migrations.AlterField(
            model_name='action',
            name='verb',
            field=models.CharField(choices=[('1', 'Follow'), ('2', 'Unfollow'), ('3', 'Search'), ('4', 'Favourite'), ('5', 'Unfavourite')], max_length=255),
        ),
    ]
