# -*- coding: UTF-8 -*-
"""
Suite(s) of test cases for the ``constants.py`` module
"""
import os
import unittest
from unittest.mock import patch, MagicMock

from requests.exceptions import ConnectionError

from vlab_api_common import constants


class TestConstants(unittest.TestCase):
    """A suite of test cases for the constanst.py module"""

    def setUp(self):
        """Runs before every test case"""
        os.environ['PRODUCTION'] = ''

    def test_get_encryption_data(self):
        """Defaults to assuming a local dev/unit test enviroment - does no I/O"""
        output = constants.get_encryption_data()
        expected = ('testing', 'HS256', 'string')
        self.assertEqual(output, expected)

    @patch.object(constants.requests, 'get')
    def test_get_encryption_data_production(self, fake_get):
        """When in production, ``get_encryption_data`` does an API call to obtain the
        RSA key needed for validation vLab Auth Tokens.
        """
        os.environ['PRODUCTION'] = 'true'
        fake_resp = MagicMock()
        fake_resp.json.return_value = {'content' : {'key' : "PUBLIC KEY",
                                                    'algorithm' : 'RS512',
                                                    'format' : "pem"}}
        fake_get.return_value = fake_resp

        key, algorithm, format = constants.get_encryption_data()
        expected = 'PUBLIC KEY'

        self.assertEqual(key, expected)

    @patch.object(constants.requests, 'get')
    def test_get_encryption_data_beta(self, fake_get):
        """When running a beta server, ``get_encryption_data`` does an API call to obtain the
        RSA key needed for validation vLab Auth Tokens, but accept a self-signed TLS cert.
        """
        os.environ['PRODUCTION'] = 'beta'
        fake_resp = MagicMock()
        fake_resp.json.return_value = {'content' : {'key' : "PUBLIC KEY",
                                                    'algorithm' : 'RS512',
                                                    'format' : "pem"}}
        fake_get.return_value = fake_resp

        key, algorithm, format = constants.get_encryption_data()
        expected = 'PUBLIC KEY'
        _, verify_arg = fake_get.call_args

        self.assertFalse(verify_arg['verify'])

    @patch.object(constants.time, 'sleep')
    @patch.object(constants.requests, 'get')
    def test_get_encryption_data_retries(self, fake_get, fake_sleep):
        """When dynamically obtaining the encryption information, the function
        will retry upon connection error.
        """
        os.environ['PRODUCTION'] = 'beta'
        fake_resp = MagicMock()
        fake_resp.json.return_value = {'content' : {'key' : "PUBLIC KEY",
                                                    'algorithm' : 'RS512',
                                                    'format' : "pem"}}
        fake_get.side_effect = [ConnectionError('testing'), fake_resp]

        key, algorithm, format = constants.get_encryption_data()
        expected = 'PUBLIC KEY'

        self.assertEqual(key, expected)
        fake_sleep.assert_called()

    @patch.object(constants.time, 'sleep')
    @patch.object(constants.requests, 'get')
    def test_get_encryption_data_raises(self, fake_get, fake_sleep):
        """Raises RuntimeError if completely unable to dynamically obtain encryption
        information.
        """
        os.environ['PRODUCTION'] = 'beta'
        fake_resp = MagicMock()
        fake_resp.json.return_value = {'content' : {'key' : "PUBLIC KEY",
                                                    'algorithm' : 'RS512',
                                                    'format' : "pem"}}
        fake_get.side_effect = [ConnectionError('testing') for x in range(15)]

        with self.assertRaises(RuntimeError):
            constants.get_encryption_data()



if __name__ == '__main__':
    unittest.main()
