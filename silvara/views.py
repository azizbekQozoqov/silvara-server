from django.shortcuts import render
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from telebot import types
from bots.raviosta import bot


# Index view
def index(request):
    return render(request, 'silvara/index.html')

# Webhook view for Telegram bot
@csrf_exempt
def webhook(request):
    if request.method == "POST":
        update = types.Update.de_json(request.body.decode("utf-8"))
        bot.process_new_updates([update])
    return HttpResponse("OK")
