from .settings_common import *

DEBUG = True


INSTALLED_APPS += (
    'debug_toolbar',
)

MIDDLEWARE += (
    'debug_toolbar.middleware.DebugToolbarMiddleware',
)

DEBUG_TOOLBAR = True

if DEBUG_TOOLBAR:
    def show_toolbar(request):
        return True

    DEBUG_TOOLBAR_CONFIG = {
        "SHOW_TOOLBAR_CALLBACK": show_toolbar,
        'INTERCEPT_REDIRECTS': False,
    }

EMAIL_PORT = 1025
