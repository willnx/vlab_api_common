# -*- coding: UTF-8 -*-
"""
A group of test suites for the flask_common module
"""

import unittest
from unittest.mock import patch, MagicMock

import ujson
from flask import Flask
from jsonschema import Draft4Validator, ValidationError, validate

from vlab_api_common import flask_common
from vlab_api_common.http_auth import generate_v2_test_token, requires


GET_SCHEMA = { "$schema": "http://json-schema.org/draft-04/schema#",
                "type": "object",
                "properties" : {
                    "stuff" : {"type" : "string"},
                }
              }
GET_SCHEMA_ARGS = { "$schema": "http://json-schema.org/draft-04/schema#",
                    "properties" : {
                        "limit" : {"type" : "number",
                                   "minimum" : 1,
                        }
                    }
                  }
DESCRIBE_METHOD_SCHEMA = { "$schema": "http://json-schema.org/draft-04/schema#",
                            "properties" : {
                                "body" : {"type": "object"},
                                "response" : {"type" : "object"},
                                "args" : {"type" : "object"}
                            }
                         }



class MyView(flask_common.BaseView):
    """Because BaseView requires subclassing to work"""
    route_base = '/test'

    @flask_common.describe(get=GET_SCHEMA, get_args=GET_SCHEMA_ARGS)
    def get(self):
        """The GET docstring"""
        return ujson.dumps({'content': 'GET OK'})

    def post(self):
        """The POST docstring"""
        return '<not>json</not>'


class SchemaView(flask_common.BaseView):
    """So we can test ``validate_input``"""
    route_base = '/schema'

    PUT = { "$schema": "http://json-schema.org/draft-04/schema#",
            "properties" : {
                "foo" : {"type": "string"}
            },
            "required" : ['foo']
          }

    @requires(verify=False, version=2)
    @flask_common.validate_input(PUT)
    def put(self, *args, **kwargs):
        return 'woot', 200


class TestValidateInput(unittest.TestCase):
    """A suite of tests for the ``validate_input`` function"""
    @classmethod
    def setUp(cls):
        """Runs before each test case"""
        app = Flask('schema')
        SchemaView.register(app)
        app.config['TESTING'] = True
        cls.app = app.test_client()
        cls.token = generate_v2_test_token(username='bob')

    def test_ok(self):
        """``validate_input`` handles valid schemas correctly"""
        resp = self.app.put('/schema', json={'foo' : 'yup'}, headers={'X-Auth': self.token})

        self.assertEqual(resp.status_code, 200)

    def test_no_body(self):
        """``validate_intput`` returns HTTP 400 if no JSON is sent with the request"""
        resp = self.app.put('/schema',  headers={'X-Auth': self.token})

        self.assertEqual(resp.status_code, 400)

    def test_bad_intput(self):
        """``validate_intput`` returns HTTP 400 if supplied with invalid input"""
        resp = self.app.put('/schema', json={'bar' : 'nope'}, headers={'X-Auth': self.token})

        self.assertEqual(resp.status_code, 400)



class TestFlaskCommon(unittest.TestCase):
    """
    A suite of test cases for the flask_common package
    """

    def setUp(self):
        """Runs before each test case"""
        app = Flask(__name__)
        MyView.register(app)
        app.config['TESTING'] = True
        self.app = app.test_client()

    def test_get_json_header(self):
        """The Content-Type is set to 'applicaiton/json' automatically"""
        resp = self.app.get('/test')

        result = resp.headers['Content-Type']
        expected = 'application/json'

        self.assertEqual(result, expected)

    def test_get_json_content(self):
        """The content returned meets our JSON contract resp shape"""
        resp = self.app.get('/test')

        result = ujson.loads(resp.data)
        expected = {'content': 'GET OK', 'error': None, 'params': {}}

        self.assertEqual(result, expected)

    def test_get_params_returned(self):
        """The params supplied on the request are returned by the response"""
        resp = self.app.get('/test?myparam=true')

        data = ujson.loads(resp.data)
        params = data['params']
        expected = {'myparam' : 'true'}

        self.assertEqual(params, expected)

    def test_describe_schema(self):
        """The response from supplying the 'describe' param still matches our default schema"""
        resp = self.app.get('/test?describe')

        result = ujson.loads(resp.data)
        try:
            validate(result, flask_common.v1_RESPONSE)
            response_schema_ok = True
        except ValidationError:
            response_schema_ok = False

        self.assertTrue(response_schema_ok)

    def test_v1_response_schema(self):
        """The default shape we return for every JSON response has a valid schema"""
        try:
            Draft4Validator.check_schema(flask_common.v1_RESPONSE)
            response_schema_ok = True
        except ValidationError:
            response_schema_ok = False

        self.assertTrue(response_schema_ok)

    def test_describe_method_schema(self):
        """Every supported method has the same schema"""
        resp = self.app.get('/test?describe')

        result = ujson.loads(resp.data)
        method_shape = result['content']['get']
        try:
            validate(method_shape, DESCRIBE_METHOD_SCHEMA)
            response_schema_ok = True
        except ValidationError:
            response_schema_ok = False

        self.assertTrue(response_schema_ok)

    def test_not_json(self):
        """The BaseView object doesn't blow up if JSON is not the response content"""
        resp = self.app.post('/test')
        expected = 200

        self.assertEqual(resp.status_code, expected)


def fake_requires(token):
    """"A pass-through decorator to mimic ``requires`` passing the auth token for testing"""
    def fake_decorator(func):
        def inner(*args, **kwargs):
            kwargs['token'] = token
            return func(*args, **kwargs)
        return inner
    return fake_decorator


if __name__ == '__main__':
    unittest.main()
