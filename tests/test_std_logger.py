# -*- coding: UTF-8 -*-
"""
A test suite for the get_logger function
"""
import unittest
import logging

from vlab_api_common import get_logger, get_task_logger


class TestGetLogger(unittest.TestCase):
    """A suite of test cases for the 'get_logger' function"""

    def test_get_logger(self):
        """get_logger returns an instance of Pythons stdlib logging.Logger object"""
        logger = get_logger('single_logger')
        self.assertTrue(isinstance(logger, logging.Logger))

    def test_get_logger_one_handler(self):
        """
        We don't add a handler (causing spam multiple line outputs for a single msg)
        every time you call get_logger for the same logging object.
        """
        logger1 = get_logger('many_loggers')
        logger2 = get_logger('many_loggers')

        handlers = len(logger2.handlers)
        expected = 1

        self.assertEqual(handlers, expected)

class TestGetTaskLogger(unittest.TestCase):
    """A suite of test cases for the 'get_task_logger' function"""

    def test_get_task_logger(self):
        """``get_task_logger`` returns an instance of logging.LoggerAdapter"""
        log = get_task_logger(txn_id='myId', task_id='aabbcc')
        self.assertTrue(isinstance(log, logging.LoggerAdapter))

    def test_get_task_logger_contains(self):
        """``get_task_logger`` contains the txn_id and task_id"""
        log = get_task_logger(txn_id='myId', task_id='aabbcc')

        format = log.logger.handlers[0].formatter._fmt
        expected_format = '%(asctime)s [%(txn_id)s] [%(task_id)s]: %(message)s'
        expected_extra = {'txn_id': 'myId', 'task_id': 'aabbcc'}

        self.assertEqual(format, expected_format)
        self.assertEqual(log.extra, expected_extra)


if __name__ == "__main__":
    unittest.main()
