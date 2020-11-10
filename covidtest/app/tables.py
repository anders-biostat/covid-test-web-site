import django_tables2 as tables
from .models import Sample

class SampleTable(tables.Table):
    bag = tables.Column(empty_values=())
    get_status = tables.Column(empty_values=())

    def render_bag(self, value):
        return value.name

    def render_get_status(self, value):
        if value:
            return value.status
        else:
            return '—'

    class Meta:
        model = Sample
        template_name = "django_tables2/semantic.html"
        attrs = {"class": "ui table"}