import logging
import json
from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from telebot import types
from bots.raviosta import bot, TARGET_CHAT_ID, _format_order_text

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


@csrf_exempt
def raviosta_order_api(request):
    """
    HTTP fallback endpoint for orders created when the Mini App is opened from
    the global attachment menu (sender context). Accepts JSON payload and
    forwards it to TARGET_CHAT_ID via the bot.
    """
    if request.method != "POST":
        return JsonResponse({"ok": False, "error": "POST required"}, status=405)

    try:
        data = json.loads(request.body.decode("utf-8"))
        logger.info("Raviosta order received via HTTP fallback")
    except Exception:
        logger.exception("Invalid JSON in raviosta_order_api")
        return JsonResponse({"ok": False, "error": "invalid json"}, status=400)

    try:
        text = _format_order_text(data)
        dest = TARGET_CHAT_ID or data.get("chat_id")
        if not dest:
            return JsonResponse({"ok": False, "error": "no destination chat"}, status=400)

        # Send order summary
        bot.send_message(dest, text)

        # Send location pin if available
        loc = data.get('location') or {}
        if loc.get('lat') and loc.get('lng'):
            bot.send_location(dest, latitude=loc['lat'], longitude=loc['lng'])

        return JsonResponse({"ok": True})
    except Exception:
        logger.exception("Failed to forward order from HTTP fallback")
        return JsonResponse({"ok": False, "error": "forward failed"}, status=500)
