import pytz

from django.utils import timezone
from django.utils.deprecation import MiddlewareMixin


class TimezoneMiddleware(MiddlewareMixin):

    def process_request(self, request):
        timezone.activate(pytz.timezone("Europe/Berlin"))
