"""
ASGI config for chat project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.0/howto/deployment/asgi/
"""

import os

from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from websocket.router import websocket_urlpatterns
from channels.auth import AuthMiddlewareStack

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "chat.settings")

application = ProtocolTypeRouter({
    'websocket': 
    AuthMiddlewareStack(
        URLRouter(
            websocket_urlpatterns
        )
    ),
    'http': get_asgi_application(),
    
})

app = application