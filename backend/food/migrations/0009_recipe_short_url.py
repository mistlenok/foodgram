# Generated by Django 3.2.16 on 2024-09-08 20:37

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('food', '0008_remove_recipe_short_url'),
    ]

    operations = [
        migrations.AddField(
            model_name='recipe',
            name='short_url',
            field=models.CharField(blank=True, max_length=50, unique=True, verbose_name='Короткий URL'),
        ),
    ]
