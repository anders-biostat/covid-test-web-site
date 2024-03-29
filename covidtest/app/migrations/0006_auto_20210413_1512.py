# Generated by Django 3.1.8 on 2021-04-13 15:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("app", "0005_auto_20210413_0926"),
    ]

    operations = [
        migrations.AlterField(
            model_name="samplerecipient",
            name="recipient_type",
            field=models.CharField(
                blank=True,
                choices=[
                    ("offers tests regularly to their staff", "Institution"),
                    (
                        "one-off or recurring event where students are tested",
                        "Teaching Event",
                    ),
                    ("invoice goes to the organizer of the event", "One-Off Event"),
                ],
                max_length=255,
                null=True,
            ),
        ),
    ]
