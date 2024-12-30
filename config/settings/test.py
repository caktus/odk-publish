from .base import *  # noqa

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# task_always_eager
CELERY_TASK_ALWAYS_EAGER = True
# task_eager_propagates
CELERY_TASK_EAGER_PROPAGATES = True