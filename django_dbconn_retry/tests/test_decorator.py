import sys
import logging
import psycopg2
from unittest.mock import Mock

from django.conf import settings
from django.db import connection, OperationalError, transaction
from django.db.backends.base.base import BaseDatabaseWrapper
from django.test import TestCase, TransactionTestCase

import django_dbconn_retry as ddr


logging.basicConfig(stream=sys.stderr)
logging.getLogger("django_dbconn_retry").setLevel(logging.DEBUG)
_log = logging.getLogger(__name__)


class DBRetryDecoratorTests(TestCase):
    # def setUp(self):
    #     _log.debug("[DBRetryDecoratorTests] patching for setup")
    #     self.s_connect = BaseDatabaseWrapper.connect
    #     BaseDatabaseWrapper.connect = Mock(side_effect=OperationalError('fail testing'))
    #     BaseDatabaseWrapper.connection = property(lambda x: None, lambda x, y: None)  # type: ignore

    # def tearDown(self):
    #     _log.debug("[DBRetryDecoratorTests] restoring")
    #     BaseDatabaseWrapper.connect = self.s_connect
    #     del BaseDatabaseWrapper.connection

    def test_retry_works(self):
        hit = [0]

        @ddr.db_retry(tries=2, delay=1)
        def decorated_func():
            hit[0] += 1
            raise OperationalError
        
        with self.assertRaises(OperationalError):
            decorated_func()
        self.assertEqual(hit[0], 2)

    def test_retry_doesnt_work_for_other_exceptions(self):
        """
        db_retry() takes care only about OperationalError exception.
        Other exceptions re-raised immediately 
        """
        hit = [0]

        @ddr.db_retry(tries=100, delay=1)
        def decorated_func():
            hit[0] += 1
            1 / 0
        
        with self.assertRaises(ZeroDivisionError):
            decorated_func()
        self.assertEqual(hit[0], 1)


class RetryWithChangedSettingsTestCase(TransactionTestCase):
    def setUp(self):
        self.orig_host = connection.settings_dict['HOST']

    def tearDown(self):
        connection.settings_dict['HOST'] = self.orig_host

    def test_retry_real(self):
        hit = [0]

        @ddr.db_retry(tries=5, delay=1)
        def decorated_func():
            hit[0] += 1

            if hit[0] == 3:
                connection.settings_dict['HOST'] = self.orig_host

            connection.cursor().execute("SELECT 1")
        
        connection.close()
        connection.settings_dict['HOST'] = 'asdfasdfasdf'
        decorated_func()

        self.assertEqual(hit[0], 3)
