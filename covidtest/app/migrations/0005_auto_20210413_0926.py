# Generated by Django 3.1.8 on 2021-04-13 09:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0004_auto_20210413_0915'),
    ]

    operations = [
        migrations.AlterField(
            model_name='samplerecipient',
            name='recipient_type',
            field=models.CharField(blank=True, choices=[('Institution', 'offers tests regularly to their staff'), ('Teaching Event', 'one-off or recurring event where students are tested'), ('One-Off Event', 'invoice goes to the organizer of the event')], max_length=255, null=True),
        ),
    ]
