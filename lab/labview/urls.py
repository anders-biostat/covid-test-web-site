from django.urls import path

from . import views

app_name = 'labview'

urlpatterns = [
    path('', views.index, name='index'),
    path('checkin', views.probe_check_in, name='checkin'),
]