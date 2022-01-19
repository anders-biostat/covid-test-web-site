from django.contrib.auth import views as auth_views
from django.views.generic.base import TemplateView
from django.urls import include, path
from django.views.decorators.csrf import csrf_exempt
from rest_framework import routers

from . import views_api, views_lab, views_public, views_consent

app_name = "app"

router = routers.DefaultRouter()
router.register(r"samples", views_api.SampleViewSet, basename="samples")
router.register(r"events", views_api.EventViewSet)
router.register(r"rsakeys", views_api.RSAKeyViewSet)
router.register(
    r"registrations", views_api.RegistrationViewSet, basename="registrations"
)
router.register(r"register", views_api.RegistrationEncryptViewSet, basename="register")
router.register(r"bags", views_api.BagViewSet)
router.register(r"keysamples", views_api.KeySamplesViewSet)


urlpatterns = [
    #path("", views_public.index, name="index"),
    path("", views_public.results_query_slim, name="index"),
    path("news/archive", views_public.news_archive, name="news_archive"),
    path("consent/age/", views_consent.AgeGroupFormView.as_view(), name="consent_age"),
    path("consent/", views_consent.ConsentView.as_view(), name="consent"),
    path("results", views_public.results_query, name="results_query"),
    path("instructions", views_public.instructions, name="instructions"),
    path("information", views_public.information, name="information"),
    path("register", views_public.register, name="register"),
    path("certificate", views_public.get_certificate, name="get_certificate"),
    path(
        "test-results",
        views_public.get_result_from_certificate,
        name="results_from_certificate",
    ),
    path("pages/<str:page>", views_public.pages, name="pages"),
    path(
        "lab/access-denied",
        TemplateView.as_view(template_name="lab/access-denied.html"),
        name="access_denied",
    ),
    path("lab", views_lab.index, name="lab_index"),
    path(
        "lab/login",
        auth_views.LoginView.as_view(),
        {"template_name": "lab/login.html"},
        name="login",
    ),
    path(
        "lab/logout",
        auth_views.LogoutView.as_view(next_page="app:login"),
        name="logout",
    ),
    path("lab/checkin", views_lab.sample_check_in, name="checkin"),
    # path(
    #     "lab/samples/detail_snippet",
    #     views_lab.sample_details_snippet,
    #     name="sample_details_snippet",
    # ),
    path("lab/samples/detail", views_lab.sample_detail, name="query"),
    path("lab/samples/update_status", views_lab.update_status, name="update_status"),
    # path("lab/samples", views_lab.SampleListView.as_view(), name="sample_list"),
    path("lab/bag-search", views_lab.bag_search_statistics, name="bag_search"),
    path("lab/bag-handout", views_lab.bag_handout, name="bag_handout"),
    path("lab/status-preview", views_lab.status_preview, name="status_preview"),
    # Unused, might be activated on future releases
    # path("lab/dashboard", views_lab.dashboard, name="dashboard"),
    path("version", views_lab.version, name="version"),
    path("api/", include(router.urls)),
    path("api-auth/", include("rest_framework.urls", namespace="rest_framework")),
    path(
        "external-login",
        csrf_exempt(views_api.authorize_and_request_data),
        name="external_login",
    ),
    path(
        "api/vd/sample",
        csrf_exempt(views_api.VirusDetectiveSampleView.as_view()),
        name="create_update_sample",
    ),
]
