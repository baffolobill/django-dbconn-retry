# -* encoding: utf-8 *-
import sys
import logging

from typing import Any
from unittest.mock import Mock

from django.db import connection, OperationalError, transaction
from django.db.backends.base.base import BaseDatabaseWrapper
from django.test import TestCase, TransactionTestCase

import django_dbconn_retry as ddr


logging.basicConfig(stream=sys.stderr)
logging.getLogger("django_dbconn_retry").setLevel(logging.DEBUG)
_log = logging.getLogger(__name__)


class FullErrorTests(TestCase):
    """
    This is SUPERHACKY. I couldn't find a better way to ensure that the
    database connections reliably fail. If I had been able to think of
    a better way, I'd have used it.
    """
    
    def setUp(self):
        _log.debug("[FullErrorTests] patching for setup")
        self.s_connect = BaseDatabaseWrapper.connect
        BaseDatabaseWrapper.connect = Mock(side_effect=OperationalError('fail testing'))
        BaseDatabaseWrapper.connection = property(lambda x: None, lambda x, y: None)

    def tearDown(self):
        _log.debug("[FullErrorTests] restoring")
        BaseDatabaseWrapper.connect = self.s_connect
        del BaseDatabaseWrapper.connection

    def test_prehook(self):
        cb = Mock(name='pre_reconnect_hook')
        ddr.pre_reconnect.connect(cb)
        self.assertRaises(OperationalError, connection.ensure_connection)
        self.assertTrue(cb.called)
        del connection._connection_retries

    def test_posthook(self):
        cb = Mock(name='post_reconnect_hook')
        ddr.post_reconnect.connect(cb)
        self.assertRaises(OperationalError, connection.ensure_connection)
        self.assertTrue(cb.called)
        del connection._connection_retries


def fix_connection(sender, *, dbwrapper, **kwargs):
    dbwrapper.connect = dbwrapper.s_connect


class ReconnectTests(TransactionTestCase):
    def test_ensure_closed(self):
        """
        Please note that sqlite3 database backend alwayes returns 
        for .is_usable() -> True. So that you cannot run tests with 
        sqlite backend.
        """
        from django.db import connection
        connection.close()
        
        # Not in atomic block, so that None
        # https://github.com/django/django/blob/60e52a047e55bc4cd5a93a8bd4d07baed27e9a22/django/db/backends/base/base.py#L269
        self.assertIsNone(connection.connection)  # should be true after setUp

    def test_prehook(self):
        cb = Mock(name='pre_reconnect_hook')
        ddr.pre_reconnect.connect(fix_connection)
        ddr.pre_reconnect.connect(cb)
        from django.db import connection
        connection.close()
        self.assertIsNone(connection.connection)
        
        connection.s_connect = connection.connect
        connection.connect = Mock(side_effect=OperationalError('reconnect testing'))
        connection.ensure_connection()
        
        self.assertTrue(cb.called)
        self.assertTrue(connection.is_usable())

    def test_posthook(self):
        cb = Mock(name='post_reconnect_hook')
        ddr.pre_reconnect.connect(fix_connection)
        ddr.post_reconnect.connect(cb)
        from django.db import connection
        connection.close()
        self.assertIsNone(connection.connection)

        connection.s_connect = connection.connect
        connection.connect = Mock(side_effect=OperationalError('reconnect testing'))
        connection.ensure_connection()

        self.assertTrue(cb.called)
        self.assertTrue(connection.is_usable())
