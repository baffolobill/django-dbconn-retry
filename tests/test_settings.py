import sys

SECRET_KEY = 'fake-key'

INSTALLED_APPS = [
    'django_dbconn_retry',
    'tests',
]

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'dbconntest',
        'USER': 'dbconntest',
        'HOST': 'localhost',
        'PASSWORD': 'dbconntest',
    }
}


LOGGING = {
    "version": 1,
    'disable_existing_loggers': False,
    "formatters": {
        "verbose": {
            "()": 'colorlog.ColoredFormatter',
            "format": "%(log_color)s%(levelname)-8s %(message)s",
            "datefmt": "%a, %d %b %Y %H:%M:%S",
            "log_colors": {
                'DEBUG':    'bold_black',
                'INFO':     'white',
                'WARNING':  'yellow',
                'ERROR':    'red',
                'CRITICAL': 'bold_red',
            },
        },
    },
    "handlers": {
        "console": {
            "level": "DEBUG",
            "class": "logging.StreamHandler",
            "formatter": "verbose",
            "stream": sys.stdout,
        },
    },
    "loggers": {
        "": {
            "handlers": ["console"],
            "level": "DEBUG",
            "propagate": True,
        },
    }
}
