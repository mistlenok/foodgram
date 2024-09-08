# Generated by Django 3.2.16 on 2024-09-07 21:57

import django.db.models.expressions
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('food', '0004_auto_20240908_0019'),
    ]

    operations = [
        migrations.AddConstraint(
            model_name='follow',
            constraint=models.CheckConstraint(check=models.Q(('user', django.db.models.expressions.F('following'))), name='user_and_following_are_different'),
        ),
    ]
