from django.urls import path, include
from rest_framework import routers
from django.contrib.auth import views as auth_views
from . import views_lab, views_public, views_api

app_name = 'app'

router = routers.DefaultRouter()
router.register(r'samples', views_api.SampleViewSet, basename="samples")
router.register(r'events', views_api.EventViewSet)
router.register(r'rsakeys', views_api.RSAKeyViewSet)
router.register(r'registrations', views_api.RegistrationViewSet)
router.register(r'bags', views_api.BagViewSet)
router.register(r'keysamples', views_api.KeySamplesViewSet)


urlpatterns = [
    path('', views_public.index, name='index'),
    path('consent', views_public.consent, name='consent'),
    path('query', views_public.results_query, name='results_query'),
    path('instructions', views_public.instructions, name='instructions'),
    path('information', views_public.information, name='information'),
    path('register', views_public.register, name='register'),
    path('pages/<str:page>', views_public.pages, name='pages'),

    path('lab', views_lab.index, name='lab_index'),
    path('lab/login', auth_views.LoginView.as_view(), {'template_name': 'lab/login.html'}, name='login'),
    path('lab/checkin', views_lab.sample_check_in, name='checkin'),
    path('lab/rack', views_lab.sample_edit_rack, name='edit_rack'),
    path('lab/samples/detail', views_lab.sample_detail, name='query'),
    path('lab/samples', views_lab.SampleListView.as_view(), name='sample_list'),
    path('lab/dashboard', views_lab.dashboard, name='dashboard'),
    path('version', views_lab.version, name='version'),

    path('api/', include(router.urls)),
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework'))
]