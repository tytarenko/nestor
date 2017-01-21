from django.utils.deprecation import MiddlewareMixin

import social.apps.django_app.middleware


class SocialAuthExceptionMiddleware(
        social.apps.django_app.middleware.SocialAuthExceptionMiddleware,
        MiddlewareMixin):
    """Work around Django 1.10 middleware incompatibility."""

    pass
