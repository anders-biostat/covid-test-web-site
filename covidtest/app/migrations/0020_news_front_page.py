# Generated by Django 4.0.1 on 2022-05-16 00:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0019_pushabonnement'),
    ]

    operations = [
        migrations.AddField(
            model_name='news',
            name='front_page',
            field=models.BooleanField(default=False),
        ),
    ]
