# -*- coding: UTF-8 -*-
"""
This module contains logic that's common across many vLab services that respond
with JSON.
"""
from copy import deepcopy
from functools import wraps
from datetime import datetime

import ujson
from flask_classy import FlaskView, request

from .std_logger import get_logger
from .constants import const

logger = get_logger(__name__, loglevel='INFO')


v1_RESPONSE = { "$schema": "http://json-schema.org/draft-04/schema#",
                "type": "object",
                "properties": {
                    "error": {
                        "type": ["string", "null"],
                    },
                    "content": {
                        "type": "object",
                        "properties": {}
                    },
                    "params": {
                        "type": "object",
                        "properties": {}
                    }
                },
                "required": [
                    "error",
                    "content",
                    "params"
                    ]
              }

class BaseView(FlaskView):
    """Base class that provides consistent shape for API Responses

    All of the vLab API end points should have a view derived from this class.
    It enables us to meet our API contract for response schema without
    having every thing "under the sun" implement the entire schema contract.

    Your methods should only have to return a section of the schema (as json)
    and the HTTP status code.

    Usage Example::

        class FooView(BaseView):
            route_base = '/api/1/foo'

            def get(self):
                # GET on http://localhost:5000/api/1/foo
                return ujson.dumps({'content' : 'woot'}), 200

            def wooter(self):
                # GET on http://localhost:5000/api/1/foo/wooter
                return ujson.dumps({'content' : "yahoo"}), 200
    """
    route_base     = RuntimeError('You Must set this!')
    trailing_slash = False

    def after_request(self, name, response):
        """
        This is the method that sets our header to application/json and
        modifies any response to meet our API contract before actually sending
        the response to the client.

        :Returns: flask.wrappers.Response

        :params name: The name of the function/method that was called before this one
        :type name: String

        :param response: The partial response we modify to meet our API contract
        :type response: flask.wrappers.Response
        """
        base = {'error' : None, 'content' : {}, 'params' : dict(request.args)}
        try:
            data = ujson.loads(response.get_data())
        except ValueError:
            return response

        user = data.pop('user', 'unset')
        if not ('poll' in request.full_path and response.status_code == 206):
            #127.0.0.1 - frank [10/Oct/2000:13:55:36 -0700] "GET /apache_pb.gif HTTP/1.0" 200 2326  "http://www.example.com/start.html" "Mozilla/4.08 [en] (Win98; I ;Nav)"
            r_time = datetime.strftime(datetime.utcnow(), "%d/%b/%Y:%H:%M:%S -0000")
            try:
                client_ip = request.headers.getlist("X-Forwarded-For")[0]
            except IndexError:
                client_ip = request.remote_addr
            logger.info('{0} - {1} [{2}] "{3} {4} {5}" {6} {7} "{8}" "{9}"'.format(client_ip,
                                                                                   user,
                                                                                   r_time,
                                                                                   request.method,
                                                                                   request.full_path,
                                                                                   request.environ.get('SERVER_PROTOCOL'),
                                                                                   response.status_code,
                                                                                   response.content_length,
                                                                                   request.referrer,
                                                                                   request.user_agent.string))
        base.update(data)
        response.set_data(ujson.dumps(base))
        response.headers['Content-Type'] = 'application/json'
        response.headers.add('Link', '<{0}{1}?describe=true>; rel=help'.format(const.VLAB_URL, self.route_base))
        return response


def describe(**schemas):
    """Handles use of the 'describe' param on requests

    This decorator is expected to be used on the 'GET' method. It takes a pile
    of schemas that define what your end points expect (json-wise) for every
    HTTP method implemented.

    For body content, simply supply the schema via the method name.
    Example::
        @describe(get=MY_SCHEMA)
        def get(self):
            "GET doesn't take any query args"
            pass

    For arguments, supply the schema via the method name with '_args' appended.
    Example::
        @describe(get_args=MY_ARGS_SCHEMA)
        def get(self):
            "GET doesn't take any body content"
            pass

    Also, don't forget to define your other HTTP methods on your 'get' method::
        @describe(get=GET_SCHEMA, post=POST_SCHEMA)
        def get(self):
            "Some docstring"
            pass
    """
    def real_decorator(func):
        @wraps(func)
        def inner(*args, **kwargs):
            if 'describe' in request.args:
                default = {'body' : {}, 'response' : v1_RESPONSE, 'args' : {}}
                the_schema = {}
                for method in schemas:
                    if method.endswith('args'):
                        action = method.split('_')[0]
                        the_schema.setdefault(action, deepcopy(default))
                        the_schema[action]['args'] = schemas[method]
                    else:
                        the_schema.setdefault(method, deepcopy(default))
                        the_schema[method]['body'] = schemas[method]
                return ujson.dumps({'content':the_schema}), 200, {'Content-Type': 'application/json'}
            else:
                return func(*args, **kwargs)
        return inner
    return real_decorator
