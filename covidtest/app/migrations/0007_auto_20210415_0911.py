# Generated by Django 3.1.8 on 2021-04-15 09:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("app", "0006_auto_20210413_1512"),
    ]

    operations = [
        migrations.AddField(
            model_name="bag",
            name="created_on",
            field=models.DateTimeField(auto_now_add=True, null=True),
        ),
        migrations.AddField(
            model_name="bag",
            name="updated_on",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name="news",
            name="created_on",
            field=models.DateTimeField(auto_now_add=True, null=True),
        ),
        migrations.AlterField(
            model_name="samplerecipient",
            name="created_on",
            field=models.DateTimeField(auto_now_add=True, null=True),
        ),
    ]