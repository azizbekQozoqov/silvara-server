from .views import index, webhook
from django.urls import path

urlpatterns = [
    path('', index),
    path('webhook/', webhook, name='telegram_webhook'),
]
