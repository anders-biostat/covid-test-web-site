import django_tables2 as tables
from .models import Sample

class SampleTable(tables.Table):
    bag = tables.Column(empty_values=())
    status = tables.Column(empty_values=())
    updated_on = tables.Column(empty_values=())

    def render_bag(self, value):
        return value.name

    def render_status(self, record):
        if record.get_status():
            return record.get_status().status
        else:
            return None

    def render_updated_on(self, record):
        status = record.get_status()
        if status:
            return status.updated_on
        else:
            return None

    class Meta:
        model = Sample
        template_name = "django_tables2/semantic.html"
        attrs = {"class": "ui table"}