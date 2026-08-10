"""WSGI entrypoint.

DJANGO_SETTINGS_MODULE comes from the process environment (set in the image and
in compose): reading it here would put an os.environ call outside the settings
schema.
"""

from django.core.wsgi import get_wsgi_application

application = get_wsgi_application()
