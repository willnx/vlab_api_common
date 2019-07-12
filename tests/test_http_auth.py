# -*- coding: UTF-8 -*-
"""
Suite(s) of test for the http_auth.py module
"""
import os
import time
import unittest
from unittest.mock import patch, MagicMock

import jwt
import ujson

from vlab_api_common import http_auth


class TestAclInToken1(unittest.TestCase):
    """Test cases for the ``acl_in_token`` function for version 1 of Maestro Auth Tokens

    This function contains the bulk of business logic for the 'deny' and 'requires'
    dectorators, and as such, it has a pile of tests around it. If you make changes
    to the function, and these test break, your changes are most likely not
    backwards compatable. In this senario, you should try to leverage the versioning
    of the Maestro Auth Token to both A) Meet your need to change things, and B)
    maintain backwards compatibility. In other words, assume these test are right,
    and your changes are bad, and get others to agree with you before changing
    these tests.
    """

    def setUp(self):
        # You should never have to change this -- if you need a different token,
        # make one in your specific test case
        self.token = {'version' : 1,
                      'username': 'bob',
                      'memberOf' : ['some-group', 'other-group']}

    def test_defaults_false(self):
        """When no parameters are set, `acl_in_token` returns False."""
        output = http_auth.acl_in_token(self.token)
        self.assertFalse(output)

    def test_version(self):
        """When the version param equals the token version, `acl_in_token` returns True.
        """
        output = http_auth.acl_in_token(self.token, version=1)
        self.assertTrue(output)

    def test_version_array(self):
        """When the version param is a List and the token contains an element
        within that list, `acl_in_token` returns True.
        """
        output = http_auth.acl_in_token(self.token, version=[1,2])
        self.assertTrue(output)

    def test_version_false(self):
        """When the version param does not equal the token version, `acl_in_token`
        returns False.
        """
        output = http_auth.acl_in_token(self.token, version=1000)
        self.assertFalse(output)

    def test_version_array_false(self):
        """When the version param is a List, the token DOESN'T contain an element
        within that list, `acl_in_token` returns False.
        """
        output = http_auth.acl_in_token(self.token, version=[1000,1001])
        self.assertFalse(output)

    def test_username(self):
        """When the username param equals the token username, `acl_in_token` returns True.
        """
        output = http_auth.acl_in_token(self.token, username='bob')
        self.assertTrue(output)

    def test_username_array(self):
        """When the username param is a List and the token contains an element
        within that list, `acl_in_token` returns True.
        """
        output = http_auth.acl_in_token(self.token, username=['bob'])
        self.assertTrue(output)

    def test_username_false(self):
        """When the username param does not equal the token username, `acl_in_token`
        returns False.
        """
        output = http_auth.acl_in_token(self.token, username='somePerson')
        self.assertFalse(output)

    def test_username_array_false(self):
        """When the username param is a List and the token DOESN"T contain an element
        within that list, `acl_in_token` returns False.
        """
        output = http_auth.acl_in_token(self.token, username=['peep-A', 'bro'])
        self.assertFalse(output)

    def test_memberOf(self):
        """When the memberOf param equals the token memberOf, `acl_in_token` returns True."""
        output = http_auth.acl_in_token(self.token, memberOf='some-group')
        self.assertTrue(output)

    def test_memberOf_array(self):
        """When the memberOf param is a List and the token contains an element
        within that list, `acl_in_token` returns True."""
        output = http_auth.acl_in_token(self.token, memberOf=['some-group', 'a-group-never-heard-of'])
        self.assertTrue(output)

    def test_memberOf_false(self):
        """When the memberOf param value is a string, and that value DOESN'T
        exist within the memberOf token array, `acl_in_token` return False.
        """
        output = http_auth.acl_in_token(self.token, memberOf='a-group-never-heard-of')
        self.assertFalse(output)

    def test_memberOf_array_false(self):
        """When the memberOf param value is a List, and NONE of those values
        exist within the memberOf token array, `acl_in_token` returns False.
        """
        output = http_auth.acl_in_token(self.token, memberOf=['a-group-never-heard-of', 'some-other-crazy-group'])
        self.assertFalse(output)


class TestGetTokenFromHeader(unittest.TestCase):
    """A suite of test cases for the ``get_token_from_header`` function"""

    @patch.object(http_auth, 'request')
    def test_get_token_from_header(self, fake_request):
        """The function `get_token_from_header` works as expected"""
        claims = {'exp' : time.time() + 10000,
                  'iss' : http_auth.const.AUTH_TOKEN_ISSUER,
                  'version' : 1,
                 }
        token = jwt.encode(claims,
                           http_auth.const.AUTH_TOKEN_PUB_KEY,
                           algorithm=http_auth.const.AUTH_TOKEN_ALGORITHM)
        fake_request.headers.get.return_value = token

        output = http_auth.get_token_from_header()

        self.assertEqual(output, claims)

    @patch.object(http_auth, 'request')
    def test_get_token_from_header_no_token(self, fake_request):
        """The function `get_token_from_header` raises ValueError when no token is supplied."""
        fake_request.headers.get.return_value = None

        self.assertRaises(ValueError, http_auth.get_token_from_header)

    @patch.object(http_auth, 'request')
    def test_get_v2_token_from_header_ok(self, fake_request):
        """The function `get_token_from_header` validates client_ip when using v2 tokens"""
        claims = {'exp' : time.time() + 10000,
                  'iss' : http_auth.const.AUTH_TOKEN_ISSUER,
                  'version' : 2,
                  'client_ip' : '127.0.0.1',
                 }
        token = jwt.encode(claims,
                           http_auth.const.AUTH_TOKEN_PUB_KEY,
                           algorithm=http_auth.const.AUTH_TOKEN_ALGORITHM)
        fake_request.headers.get.return_value = token
        fake_request.headers.getlist.return_value = ['127.0.0.1']

        output = http_auth.get_token_from_header()

        self.assertEqual(output, claims)

    @patch.object(http_auth, 'request')
    def test_get_v2_token_from_header_no_forward(self, fake_request):
        """The function `get_token_from_header` validates client_ip when using v2 tokens"""
        claims = {'exp' : time.time() + 10000,
                  'iss' : http_auth.const.AUTH_TOKEN_ISSUER,
                  'version' : 2,
                  'client_ip' : '127.0.0.1',
                 }
        token = jwt.encode(claims,
                           http_auth.const.AUTH_TOKEN_PUB_KEY,
                           algorithm=http_auth.const.AUTH_TOKEN_ALGORITHM)
        fake_request.headers.get.return_value = token
        fake_request.headers.getlist.return_value = []
        fake_request.remote_addr = '127.0.0.1'

        output = http_auth.get_token_from_header()

        self.assertEqual(output, claims)

    @patch.object(http_auth, 'request')
    def test_get_v2_token_from_header_hijacked(self, fake_request):
        """The function `get_token_from_header` raises ValueError if the token comes form a different client ip"""
        claims = {'exp' : time.time() + 10000,
                  'iss' : http_auth.const.AUTH_TOKEN_ISSUER,
                  'version' : 2,
                  'client_ip' : '127.0.0.1',
                 }
        token = jwt.encode(claims,
                           http_auth.const.AUTH_TOKEN_PUB_KEY,
                           algorithm=http_auth.const.AUTH_TOKEN_ALGORITHM)
        fake_request.headers.get.return_value = token
        fake_request.headers.getlist.return_value = []
        fake_request.remote_addr = '8.8.8.8'

        self.assertRaises(ValueError, http_auth.get_token_from_header)


class TestDecorators(unittest.TestCase):
    """A suite of test cases for ``requires`` and ``deny`` decorators"""

    def setUp(self):
        """Runs before every test case"""
        self.token = {'username' : 'bob-the-builder',
                      'version' : 1,
                      'memberOf' : ['some-group']}

    @patch.object(http_auth, 'requests')
    @patch.object(http_auth, 'get_token_from_header')
    def test_requires(self, fake_get_token_from_header, fake_requests):
        """The `requires` decorator works for the most basic use case"""
        fake_get_token_from_header.return_value = self.token

        @http_auth.requires()
        def fake_func(*args, **kwargs):
            return True

        output = fake_func()
        self.assertTrue(output)

    @patch.object(http_auth, 'requests')
    @patch.object(http_auth, 'get_token_from_header')
    def test_requires_invalid_token(self, fake_get_token_from_header, fake_requests):
        """The `requires` bails early if the token is invalid or missing"""
        fake_get_token_from_header.side_effect = ValueError('TESTING')

        @http_auth.requires()
        def fake_func(*args, **kwargs):
            return True

        resp = fake_func()

        output = (ujson.loads(resp.get_data()), resp.status_code)
        expected = ({"error":"TESTING"}, 401)

        self.assertEqual(output, expected)

    @patch.object(http_auth, 'requests')
    @patch.object(http_auth, 'get_token_from_header')
    def test_requires_expired_token(self, fake_get_token_from_header, fake_requests):
        """The `requires` bails early if the token is already expired"""
        fake_get_token_from_header.side_effect = jwt.ExpiredSignatureError('TESTING')

        @http_auth.requires()
        def fake_func(*args, **kwargs):
            return True

        resp = fake_func()

        output = (ujson.loads(resp.get_data()), resp.status_code)
        expected = ({"error":"No Valid Session Found"}, 401)

        self.assertEqual(output, expected)

    @patch.object(http_auth, 'requests')
    @patch.object(http_auth, 'get_token_from_header')
    def test_requires_token_error(self, fake_get_token_from_header, fake_requests):
        """The `requires` returns an unauthorized error if the token decryption fails"""
        fake_get_token_from_header.side_effect = jwt.exceptions.InvalidTokenError('TESTING')

        @http_auth.requires()
        def fake_func(*args, **kwargs):
            return True

        resp = fake_func()

        output = (ujson.loads(resp.get_data()), resp.status_code)
        expected = ({"error":"Invalid auth token supplied"}, 401)

        self.assertEqual(output, expected)

    @patch.object(http_auth, 'requests')
    @patch.object(http_auth, 'get_token_from_header')
    def test_requires_authorization_link(self, fake_get_token_from_header, fake_requests):
        """The `requires` decorator auto sets the Link header for Unauthorized"""
        fake_get_token_from_header.side_effect = jwt.ExpiredSignatureError('TESTING')

        @http_auth.requires()
        def fake_func(*args, **kwargs):
            return True

        resp = fake_func()

        found = resp.headers['Link']
        expected = '<https://localhost/api/1/auth>; rel=authorization'

        self.assertEqual(found, expected)

    @patch.object(http_auth, 'requests')
    @patch.object(http_auth, 'get_token_from_header')
    def test_requires_no_access(self, fake_get_token_from_header, fake_requests):
        """The `requires` bails early if the user doesn't meet the ACL requirement"""
        self.token['version'] = 9001
        fake_get_token_from_header.return_value = self.token

        @http_auth.requires(version=7)
        def fake_func(*args, **kwargs):
            return True

        json_output, http_status_code = fake_func()
        output = (ujson.loads(json_output), http_status_code)
        expected = ({"error":"user bob-the-builder does not have access"}, 403)

        self.assertEqual(output, expected)

    @patch.object(http_auth, 'requests')
    @patch.object(http_auth, 'get_token_from_header')
    def test_requires_layered(self, fake_get_token_from_header, fake_requests):
        """The `requires` decorator only pulls the token once if used multiple times"""
        fake_get_token_from_header.return_value = self.token

        @http_auth.requires()
        @http_auth.requires()
        @http_auth.requires()
        def fake_func(*args, **kwargs):
            return True

        fake_func()

        self.assertEqual(fake_get_token_from_header.call_count, 1)

    @patch.object(http_auth, 'requests')
    @patch.object(http_auth, 'get_token_from_header')
    def test_requires_complex(self, fake_get_token_from_header, fake_requests):
        """The `requires` decorator works for more complex ACLs"""
        fake_get_token_from_header.return_value = self.token

        @http_auth.requires(username=['bob', 'sarah'])
        @http_auth.requires(memberOf=['some-group', 'another-group'])
        def fake_func(*args, **kwargs):
            return True

        output = fake_func()
        expected = True

        self.assertEqual(output, expected)

    @patch.object(http_auth, 'requests')
    @patch.object(http_auth, 'get_token_from_header')
    def test_requires_verify_once(self, fake_get_token_from_header, fake_requests):
        """The `requires` decorator only verifies the token once with more comples ACLs"""
        fake_get_token_from_header.return_value = self.token

        @http_auth.requires(username=['andy', 'sarah'])
        @http_auth.requires(memberOf=['some-group', 'another-group'])
        def fake_func(*args, **kwargs):
            return True

        fake_func()

        self.assertEqual(fake_requests.get.call_count, 1)

    @patch.object(http_auth, 'requests')
    @patch.object(http_auth, 'get_token_from_header')
    def test_requires_verify_fail(self, fake_get_token_from_header, fake_requests):
        """The `requires` decorator returns the status and content when verification fails"""
        fake_get_token_from_header.return_value = self.token
        fake_resp = MagicMock()
        fake_resp.ok = False
        fake_resp.content = 'testing'
        fake_resp.status = 401
        fake_requests.get.return_value = fake_resp

        @http_auth.requires(username=['andy', 'sarah'])
        @http_auth.requires(memberOf=['some-group', 'another-group'])
        def fake_func(*args, **kwargs):
            return True

        output = fake_func()
        expected = ('testing', 401)

        self.assertEqual(output, expected)

    @patch.object(http_auth, 'requests')
    @patch.object(http_auth, 'get_token_from_header')
    def test_deny_basic(self, fake_get_token_from_header, fake_requests):
        """The `deny` decorator only denies access based on the ACL"""
        # the token is defined to be "bob-the-builder", not "some-jerk"
        fake_get_token_from_header.return_value = self.token

        @http_auth.deny(username='some-jerk')
        def fake_func(*args, **kwargs):
            return True

        output = fake_func()
        expected = True

        self.assertEqual(output, expected)

    @patch.object(http_auth, 'requests')
    @patch.object(http_auth, 'get_token_from_header')
    def test_deny_no_access(self, fake_get_token_from_header, fake_requests):
        """The `deny` decorator can block access based on identity"""
        fake_get_token_from_header.return_value = self.token

        @http_auth.deny(username='bob-the-builder')
        def fake_func(*args, **kwargs):
            return True

        json_output, http_status = fake_func()

        output = (ujson.loads(json_output), http_status)
        expected = ({'error' : 'user bob-the-builder does not have access'}, 403)

        self.assertEqual(output, expected)

    @patch.object(http_auth, 'requests')
    @patch.object(http_auth, 'get_token_from_header')
    def test_deny_expired_token(self, fake_get_token_from_header, fake_requests):
        """The `deny` bails early if the token is already expired"""
        fake_get_token_from_header.side_effect = jwt.ExpiredSignatureError('TESTING')

        @http_auth.deny()
        def fake_func(*args, **kwargs):
            return True

        resp = fake_func()

        output = (ujson.loads(resp.get_data()), resp.status_code)
        expected = ({"error":"No Valid Session Found"}, 401)

        self.assertEqual(output, expected)

    @patch.object(http_auth, 'requests')
    @patch.object(http_auth, 'get_token_from_header')
    def test_deny_token_error(self, fake_get_token_from_header, fake_requests):
        """The `deny` returns an unauthorized error if the token decryption fails"""
        fake_get_token_from_header.side_effect = jwt.exceptions.InvalidTokenError('TESTING')

        @http_auth.deny()
        def fake_func(*args, **kwargs):
            return True

        resp = fake_func()

        output = (ujson.loads(resp.get_data()), resp.status_code)
        expected = ({"error":"Invalid auth token supplied"}, 401)

        self.assertEqual(output, expected)

    @patch.object(http_auth, 'requests')
    @patch.object(http_auth, 'get_token_from_header')
    def test_deny_invalid_token(self, fake_get_token_from_header, fake_requests):
        """The `deny` bails early if the token is invalid/missing"""
        fake_get_token_from_header.side_effect = ValueError('TESTING')

        @http_auth.deny()
        def fake_func(*args, **kwargs):
            return True

        resp = fake_func()

        output = (ujson.loads(resp.get_data()), resp.status_code)
        expected = ({"error":"TESTING"}, 401)

        self.assertEqual(output, expected)

    @patch.object(http_auth, 'requests')
    @patch.object(http_auth, 'get_token_from_header')
    def test_deny_authorization_link(self, fake_get_token_from_header, fake_requests):
        """The `deny` decorator auto sets the Link header for Unauthorized"""
        fake_get_token_from_header.side_effect = jwt.ExpiredSignatureError('TESTING')

        @http_auth.deny()
        def fake_func(*args, **kwargs):
            return True

        resp = fake_func()

        found = resp.headers['Link']
        expected = '<https://localhost/api/1/auth>; rel=authorization'

        self.assertEqual(found, expected)

    @patch.object(http_auth, 'requests')
    @patch.object(http_auth, 'get_token_from_header')
    def test_deny_layered(self, fake_get_token_from_header, fake_requests):
        """The `deny` decorator only pulls the token once if used multiple times"""
        fake_get_token_from_header.return_value = self.token

        @http_auth.deny()
        @http_auth.deny()
        @http_auth.deny()
        def fake_func(*args, **kwargs):
            return True

        fake_func()

        self.assertEqual(fake_get_token_from_header.call_count, 1)

    @patch.object(http_auth, 'requests')
    @patch.object(http_auth, 'get_token_from_header')
    def test_deny_complex(self, fake_get_token_from_header, fake_requests):
        """The `deny` decorator works for more complex ACLs"""
        fake_get_token_from_header.return_value = self.token

        @http_auth.deny(username=['andy', 'sarah'])
        @http_auth.deny(memberOf=['some-group', 'another-group'])
        def fake_func(*args, **kwargs):
            return True

        json_output, http_status_code = fake_func()

        output = (ujson.loads(json_output), http_status_code)
        expected = ({'error': 'user bob-the-builder does not have access'}, 403)

        self.assertEqual(output, expected)

    @patch.object(http_auth, 'requests')
    @patch.object(http_auth, 'get_token_from_header')
    def test_deny_verify_once(self, fake_get_token_from_header, fake_requests):
        """The `deny` decorator only verifies the token once with more comples ACLs"""
        fake_get_token_from_header.return_value = self.token

        @http_auth.deny(username=['andy', 'sarah'])
        @http_auth.deny(memberOf=['some-group', 'another-group'])
        def fake_func(*args, **kwargs):
            return True

        fake_func()

        self.assertEqual(fake_requests.get.call_count, 1)

    @patch.object(http_auth, 'requests')
    @patch.object(http_auth, 'get_token_from_header')
    def test_deny_verify_fail(self, fake_get_token_from_header, fake_requests):
        """The `deny` decorator returns the status and content when verification fails"""
        fake_get_token_from_header.return_value = self.token
        fake_resp = MagicMock()
        fake_resp.ok = False
        fake_resp.content = 'testing'
        fake_resp.status = 401
        fake_requests.get.return_value = fake_resp

        @http_auth.deny(username=['andy', 'sarah'])
        @http_auth.deny(memberOf=['some-group', 'another-group'])
        def fake_func(*args, **kwargs):
            return True

        output = fake_func()
        expected = ('testing', 401)

        self.assertEqual(output, expected)


class TestGenerateTestToken(unittest.TestCase):
    """A suite of test cases for the `generate_test_token` function"""


    def test_basic_usage(self):
        """Verifies that `generate_test_token` returns an expected token"""
        token = http_auth.generate_test_token()

        self.assertTrue(isinstance(token, bytes))

    def test_v2_token(self):
        """Verifies that ``generate_v2_test_token`` returns an expected token"""
        token = http_auth.generate_v2_test_token()

        self.assertTrue(isinstance(token, bytes))


if __name__ == '__main__':
    unittest.main()
