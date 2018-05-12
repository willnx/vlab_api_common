# -*- coding: UTF-8 -*-
"""
A test suite for the get_logger function
"""
import unittest
import logging

from vlab_api_common import get_logger


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



if __name__ == "__main__":
    unittest.main()
