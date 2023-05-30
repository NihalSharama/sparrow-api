from django.urls import path
from .consumers import ChatChannel,Signalling

websocket_urlpatterns = [path(
    "ws/chat/",
    ChatChannel.as_asgi(),
),

path(
    "ws/signalling/",
    Signalling.as_asgi(),
),
]
