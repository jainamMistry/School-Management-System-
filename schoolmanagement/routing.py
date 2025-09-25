from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from django.urls import path, include
from school.routing import websocket_urlpatterns

application = ProtocolTypeRouter({
    'http': None,  # Django's ASGI application will handle HTTP requests
    'websocket': AuthMiddlewareStack(
        URLRouter(
            websocket_urlpatterns
        )
    ),
})
