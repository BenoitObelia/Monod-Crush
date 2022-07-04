import logging

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        "console": {
            "()": "django.utils.log.ServerFormatter",
            'format': '{asctime} - {levelname:^8} - {name:^12} - {message}',
            'datefmt': '%H:%M:%S',
            'style': '{',
        },
        'file': {
            'format': '{asctime} - {levelname:^8} - {name:^12} - {message}',
            'datefmt': '%Y-%m-%d %H:%M:%S',
            'style': '{',
        },
        'discord': {
            'format': '{levelname:^8} - {name:^12} - {message}',
            'style': '{',
        },
    },
    'filters': {
        'user_or_ip': {
            '()': 'monodcrush.customLogging.UserOrIPFilter',
        },
        'require_debug_true': {
            '()': 'django.utils.log.RequireDebugTrue',
        },
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',

            'level': 'DEBUG',
            'filters': ['require_debug_true'],
            'formatter': 'console',
        },
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': 'log.log',
            'maxBytes': 1024 * 1024 * 100,
            'backupCount': 10,
            'encoding': 'utf8',
            'mode': 'a',

            'filters': ['require_debug_false'],
            'level': 'NOTSET',
            'formatter': 'file',
        },
        'discord': {
            'class': 'monodcrush.customLogging.DiscordHandler',
            "webhook_url": "https://discord.com/api/webhooks/954368771110359121/mS5dYS9CL2IGLMiWtZis2abb036YrSHWtNZ269xEZHyZSKzK19ss8zz0MWzKMNizvwYc",
            "notify_users_level": logging.WARNING,
            'notify_users': [381129168467001347],

            'level': 'INFO',
            'filters': ['require_debug_false'],
            'formatter': 'discord',
        },
    },
    'loggers': {
        'django': {
            'level': 'INFO',
            'handlers': ['console', 'file', 'discord'],
            'propagate': False,
        },
        "django.server": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
        "blog": {
            'level': 'DEBUG',
            'handlers': ['console', 'file', 'discord'],
            'propagate': False,
        },
    },
    'root': {
        'level': 'WARNING',
        'handlers': ['console', 'file', 'discord'],
        'propagate': False,
    },
}
