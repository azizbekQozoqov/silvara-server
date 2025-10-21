# Logging in this project

This Django project uses Python's logging with a rotating file handler and console output.

- Log directory: `logs/`
  - `django.log`: general application logs
  - `errors.log`: errors from `django.request` and 5xx responses
- Console logs: always enabled, level controlled by `LOG_LEVEL` env var

Environment variables:
- `DEBUG`: `true`/`false` (affects default log level)
- `LOG_LEVEL`: override log level (e.g., `INFO`, `DEBUG`, `WARNING`)
- `TELEBOT_LOG_LEVEL`: level for `telebot` logger (default `WARNING`)

To tail logs during development:

```sh
# macOS/Linux
tail -f logs/django.log | sed -E 's/\x1b\[[0-9;]*m//g'
```

Instrumentation:
- Request logging middleware: `core.middleware.RequestLoggingMiddleware` logs method, path, status, and duration.
- App logs: use `logger = logging.getLogger('silvara')` in app modules.

Change level per module by editing `LOGGING['loggers']` in `core/settings.py`.