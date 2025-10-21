from .views import index, webhook, raviosta_bot
from django.urls import path

urlpatterns = [
    path('', index),
    path('webhook/', webhook, name='telegram_webhook'),
    path('raviosta/bot/', raviosta_bot, name='raviosta_bot'),
]
