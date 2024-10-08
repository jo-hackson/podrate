"""
WSGI config for podrateSite project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/howto/deployment/wsgi/
"""

import os, sys

sys.path.append('/var/app/current/podrateSite')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'podrateSite.settings')

from django.core.wsgi import get_wsgi_application

application = get_wsgi_application()
