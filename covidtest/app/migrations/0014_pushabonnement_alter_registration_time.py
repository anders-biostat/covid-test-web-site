# Generated by Django 4.0.1 on 2022-02-17 01:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0013_auto_20220117_2314'),
    ]

    operations = [
        migrations.CreateModel(
            name='PushAbonnement',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('key', models.CharField(max_length=50)),
            ],
        ),
        migrations.AlterField(
            model_name='registration',
            name='time',
            field=models.DateTimeField(auto_now_add=True, null=True),
        ),
    ]
