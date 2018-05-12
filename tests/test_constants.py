# -*- coding: UTF-8 -*-
"""
Suite(s) of test cases for the `constants.py` module
"""
import os
import unittest
from unittest.mock import patch, MagicMock

from vlab_api_common import constants


class TestConstants(unittest.TestCase):
    """A suite of test cases for the constanst.py module"""

    def setUp(self):
        """Runs before every test case"""
        os.environ['PRODUCTION'] = ''

    @patch.object(constants.requests, 'get')
    def test_get_public_key_production(self, fake_get):
        """When in production, `get_public_key` does an API call to obtain the
        RSA key needed for validation Maestro Auth Tokens.
        """
        os.environ['PRODUCTION'] = 'true'
        fake_resp = MagicMock()
        fake_resp.json.return_value = {'content' : {'key' : "PUBLIC KEY"}}
        fake_get.return_value = fake_resp

        output = constants.get_public_key()
        expected = 'PUBLIC KEY'

        self.assertEqual(output, expected)

    @patch.object(constants.requests, 'get')
    def test_get_public_key_exception(self, fake_get):
        """When in production, `get_public_key` will raise an exception if unable
        to obtain the public RSA key.
        """
        os.environ['PRODUCTION'] = 'true'
        fake_get.return_value.raise_for_status.side_effect = RuntimeError('TESTING')

        self.assertRaises(RuntimeError, constants.get_public_key)

    def test_get_public_key_default(self):
        """The function `get_public_key` assumes a testing environment by default"""
        output = constants.get_public_key()
        expected = "testing"

        self.assertEqual(output, expected)

    def test_get_public_key_evn_var(self):
        """Setting the env var PRODUCTION to anything other than 'true' makes PRODUCTION false"""
        os.environ['PRODUCTION'] = 'TRUE' # must be all lower case
        output = constants.get_public_key()
        expected = 'testing'
        os.environ.pop('PRODUCTION', None)

        self.assertEqual(output, expected)


if __name__ == '__main__':
    unittest.main()
