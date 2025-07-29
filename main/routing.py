from django.urls import re_path
from main.consumers import OrderTrackingConsumer, RestaurantOrderConsumer

websocket_urlpatterns = [
    # User order tracking WebSocket
    re_path(r'ws/orders/', OrderTrackingConsumer.as_asgi()),
    
    # Restaurant order management WebSocket
    re_path(r'ws/restaurant/(?P<restaurant_id>[0-9a-f-]+)/orders/', RestaurantOrderConsumer.as_asgi()),
]