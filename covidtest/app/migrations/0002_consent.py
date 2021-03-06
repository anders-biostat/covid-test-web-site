# Generated by Django 3.1.2 on 2021-01-22 14:46

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Consent',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('consent_type', models.CharField(max_length=50)),
                ('md5', models.CharField(max_length=200)),
                ('date', models.DateTimeField(auto_now_add=True)),
                ('registration', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='consents', to='app.registration')),
            ],
        ),
    ]
