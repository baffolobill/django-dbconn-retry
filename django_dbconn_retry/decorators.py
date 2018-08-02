"""
This retry decorator based on code from:
https://github.com/invl/retry
"""
import logging
import random
import time
from functools import partial

from django.db import utils as django_db_utils
from django.db.transaction import get_connection  # Private Django API!!!

logging_logger = logging.getLogger(__name__)
_operror_types = (django_db_utils.OperationalError,)

try:
    import psycopg2
except ImportError:
    pass
else:
    _operror_types += (psycopg2.OperationalError,)

try:
    import sqlite3
except ImportError:
    pass
else:
    _operror_types += (sqlite3.OperationalError,)

try:
    import MySQLdb
except ImportError:
    pass
else:
    _operror_types += (MySQLdb.OperationalError,)


def __retry_internal(f, tries=-1, delay=0, max_delay=None, backoff=1, jitter=0,
                     logger=logging_logger):
    """
    Executes a function and retries it if it failed.
    :param f: the function to execute.
    :param tries: the maximum number of attempts. default: -1 (infinite).
    :param delay: initial delay between attempts. default: 0.
    :param max_delay: the maximum value of delay. default: None (no limit).
    :param backoff: multiplier applied to delay between attempts. default: 1 (no backoff).
    :param jitter: extra seconds added to delay between attempts. default: 0.
                   fixed if a number, random if a range tuple (min, max)
    :param logger: logger.warning(fmt, error, delay) will be called on failed attempts.
                   default: retry.logging_logger. if None, logging is disabled.
    :returns: the result of the f function.
    """
    _tries, _delay = tries, delay
    while _tries:
        try:
            return f()
        except Exception as e:
            if not isinstance(e, _operror_types):
                logger.exception(
                    "Database connection failed, but not due to a known error "
                    "for dbconn_retry."
                    )
                raise
            
            _tries -= 1
            if not _tries:
                raise

            if logger is not None:
                logger.warning(
                    '%s, retrying in %s seconds...', 
                    e, _delay
                    )

            time.sleep(_delay)
            _delay *= backoff

            if isinstance(jitter, tuple):
                _delay += random.uniform(*jitter)
            else:
                _delay += jitter

            if max_delay is not None:
                _delay = min(_delay, max_delay)


def db_retry(using=None, tries=None, delay=None, max_delay=None, backoff=1, jitter=0, logger=logging_logger):
    """Returns a retry decorator.
    :param using: database alias from settings.DATABASES.
    :param tries: the maximum number of attempts.
                  -1 means infinite.
                  None - get from current connection.
                  default: DATABASES[using].get('MAX_RETRIES', 1).
    :param delay: initial delay between attempts.
                  None - get from current connection.
                  default: DATABASES[using].get('RETRY_DELAY_SECONDS', 0).
    :param max_delay: the maximum value of delay. default: None (no limit).
    :param backoff: multiplier applied to delay between attempts. default: 1 (no backoff).
    :param jitter: extra seconds added to delay between attempts. default: 0.
                   fixed if a number, random if a range tuple (min, max)
    :param logger: logger.warning(fmt, error, delay) will be called on failed attempts.
                   default: retry.logging_logger. if None, logging is disabled.
    :returns: a retry decorator.
    """

    if tries is None or delay is None:
        connection = get_connection(using=using)
        if tries is None:
            tries = connection.settings_dict.get("MAX_RETRIES", 1)
        if delay is None:
            # RETRY_DELAY_SECONDS might be None, so that added this "or 0"
            delay = connection.settings_dict.get("RETRY_DELAY_SECONDS", 0) or 0

    def wrap(f):
        def wrapped_f(*fargs, **fkwargs):
            args = fargs if fargs else list()
            kwargs = fkwargs if fkwargs else dict()

            return __retry_internal(
                partial(f, *args, **kwargs), tries, delay, max_delay, backoff, 
                jitter, logger
                )
        return wrapped_f
    return wrap
