import django_tables2 as tables
from .models import Sample

class SampleTable(tables.Table):
    class Meta:
        model = Sample
        template_name = "django_tables2/bootstrap.html"
        attrs = {"class": "ui table"}