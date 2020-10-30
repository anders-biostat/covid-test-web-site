from django.urls import path

from . import views

app_name = 'labview'

urlpatterns = [
    path('', views.index, name='index'),
    path('checkin', views.sample_check_in, name='checkin'),
    path('rack', views.sample_edit_rack, name='edit_rack'),
    path('query', views.sample_query, name='query'),
    path('barcodes', views.generate_barcodes, name='barcodes'),
]