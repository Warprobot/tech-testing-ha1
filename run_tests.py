#!/usr/bin/env python2.7
import contextlib

import os
import socket
import sys
import unittest
from source.tests.test_lib_init import InitTestCase

source_dir = os.path.join(os.path.dirname(__file__), 'source')
sys.path.insert(0, source_dir)

from tests.test_notification_pusher import NotificationPusherTestCase
from tests.test_redirect_checker import RedirectCheckerTestCase


def _create_connection(*args, **kwargs):
    raise AssertionError('Unmocked http request')


socket.create_connection = _create_connection


@contextlib.contextmanager
def mocked_connection():
    original_connection = socket.create_connection
    socket.create_connection = _create_connection
    yield
    socket.create_connection = original_connection


if __name__ == '__main__':
    suite = unittest.TestSuite((
        unittest.makeSuite(NotificationPusherTestCase),
        unittest.makeSuite(RedirectCheckerTestCase),
        unittest.makeSuite(InitTestCase),
    ))
    with mocked_connection():
        result = unittest.TextTestRunner().run(suite)
    sys.exit(not result.wasSuccessful())
