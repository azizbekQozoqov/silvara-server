import logging
from django.shortcuts import render
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from telebot import types
from bots.raviosta import bot

logger = logging.getLogger('silvara')


# Index view
def index(request):
    logger.debug("Rendering index page")
    return render(request, 'silvara/index.html')


def raviosta_bot(request):
    """Render the Telegram Mini App page for Raviosta."""
    logger.debug("Rendering raviosta/bot.html")
    return render(request, 'raviosta/bot.html')

# Webhook view for Telegram bot
@csrf_exempt
def webhook(request):
    if request.method == "POST":
        try:
            body = request.body.decode("utf-8")
            logger.debug("Received webhook POST: %s bytes", len(body))
            update = types.Update.de_json(body)
            bot.process_new_updates([update])
            logger.info("Webhook update processed successfully")
        except Exception:
            logger.exception("Failed to process webhook update")
    return HttpResponse("OK")
