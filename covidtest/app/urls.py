from django.urls import path, include
from rest_framework import routers
from . import views_lab, views_public, views_api

app_name = 'app'

router = routers.DefaultRouter()
router.register(r'samples', views_api.SampleViewSet)
router.register(r'events', views_api.EventViewSet)
router.register(r'keys', views_api.KeyViewSet)
router.register(r'registrations', views_api.RegistrationViewSet)
router.register(r'keysamples', views_api.KeySamplesViewSet)


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

    path('api/', include(router.urls)),
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework'))
]