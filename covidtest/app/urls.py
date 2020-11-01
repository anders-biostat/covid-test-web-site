from django.urls import path

from . import views_lab, views_public

app_name = 'app'

urlpatterns = [
    path('', views_public.index, name='index'),
    path('consent', views_public.consent, name='consent'),
    path('query', views_public.results_query, name='results_query'),
    path('instructions', views_public.instructions, name='instructions'),
    path('information', views_public.information, name='information'),
    path('register', views_public.register, name='register'),
    path('pages/<str:page>', views_public.pages, name='pages'),

    path('checkin', views_lab.sample_check_in, name='checkin'),
    path('rack', views_lab.sample_edit_rack, name='edit_rack'),
    path('query', views_lab.sample_query, name='query'),
    path('barcodes', views_lab.generate_barcodes, name='barcodes'),
]