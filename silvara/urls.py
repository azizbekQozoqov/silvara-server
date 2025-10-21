from .views import index, webhook, raviosta_bot, raviosta_order_api
from django.urls import path

urlpatterns = [
    path('', index),
    path('webhook/', webhook, name='telegram_webhook'),
    path('raviosta/bot/', raviosta_bot, name='raviosta_bot'),
    path('raviosta/order', raviosta_order_api, name='raviosta_order_api'),
]
