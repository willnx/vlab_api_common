# -*- coding: UTF-8 -*-
"""
This module implements vLab Compossible ACLs for use with `Flask <http://flask.pocoo.org/>`_
based services.

At a very high level, there are two basic way to limit access: permit access based
on some identity, or forbid access based on some identity. This module
does that via two decorators, ``requires`` and ``deny`` which can be used as many
times as desired for a single API end point.
"""
import copy
from functools import wraps

import ujson
import requests
from flask_classy import request, Response
from jwt import ExpiredSignatureError, decode, encode

from vlab_api_common.constants import const


def requires(username=None, memberOf=None, version=const.AUTH_TOKEN_VERSION, verify=True):
    """A decorator for granting access to an API because a user contains some specific
    identity information.

    :Returns: Function
    """
    def real_decorator(func):
        @wraps(func)
        def inner(*args, **kwargs):
            if kwargs.get('token', None) is None:
                try:
                    fresh_token = get_token_from_header()
                    kwargs['token'] = fresh_token
                except ExpiredSignatureError:
                    data = {'error' : 'No Valid Session Found'}
                    resp = Response(ujson.dumps(data))
                    resp.headers.add('Link', '<{0}{1}>; rel=authorization'.format(const.VLAB_URL, '/api/1/auth'))
                    resp.status_code = 401
                    return resp

            if verify is True and kwargs.get('verified', False) is False:
                resp = requests.get('{}{}'.format(const.VLAB_URL, '/api/1/auth'), params={'token': kwargs['token']})
                if not resp.ok:
                    return resp.content, resp.status
                else:
                    kwargs['verified'] = True

            if acl_in_token(kwargs['token'], username=username, memberOf=memberOf, version=version):
                return func(*args, **kwargs)
            else:
                resp = {'error' : 'user {} does not have access'.format(kwargs['token']['username'])}
                return ujson.dumps(resp), 403
        return inner
    return real_decorator


def deny(username=None, memberOf=None, version=None, verify=True):
    """A decorator for forbidding access to an API because a user contains some
    specific identity information

    :Returns: Function
    """
    def real_decorator(func):
        @wraps(func)
        def inner(*args, **kwargs):
            if kwargs.get('token', None) is None:
                try:
                    fresh_token = get_token_from_header()
                    kwargs['token'] = fresh_token
                except ExpiredSignatureError:
                    data = {'error' : 'No Valid Session Found'}
                    resp = Response(ujson.dumps(data))
                    resp.headers.add('Link', '<{0}{1}>; rel=authorization'.format(const.VLAB_URL, '/api/1/auth'))
                    resp.status_code = 401
                    return resp

            if verify is True and kwargs.get('verified', False) is False:
                resp = requests.get('{}{}'.format(const.VLAB_URL, '/api/1/auth'), params={'token': kwargs['token']})
                if not resp.ok:
                    return resp.content, resp.status
                else:
                    kwargs['verified'] = True

            if acl_in_token(kwargs['token'], username=username, memberOf=memberOf, version=version):
                resp = {'error' : 'user {} does not have access'.format(kwargs['token']['username'])}
                return ujson.dumps(resp), 403
            else:
                return func(*args, **kwargs)
        return inner
    return real_decorator


def acl_in_token(token, username=None, memberOf=None, roles=None, version=None):
    """Determines if an ACL overlaps with the identity contained by an Auth Token

    :Returns: Boolean
    """
    for key, value in copy.deepcopy(locals()).items():
        if key == 'token' or value is None:
            continue
        elif isinstance(value, str) or isinstance(value, int):
            if isinstance(token[key], list):
                return value in token[key]
            else:
                return value == token[key]
        elif isinstance(token[key], list) and isinstance(value, list):
            # if the lists share common elements
            if set(token[key]).intersection(set(value)):
                return True
        else:
            # value is a list, and the token key must be an element within that list
            if token[key] in value:
                return True
    else:
        return False


def get_token_from_header():
    """Pulls the vLab Auth Token from the HTTP header, and decrypts it.

    :Returns: Dictionary

    :Raises: ExpiredSignatureError
    """
    try:
        serialized_token = request.headers.get('X-Auth')
    except AttributeError:
        # no token in header
        raise ExpiredSignatureError('No auth token in HTTP header')
    else:
        return decode(serialized_token,
                      const.AUTH_TOKEN_PUB_KEY,
                      algorithms=const.AUTH_TOKEN_ALGORITHM,
                      issuer=const.AUTH_TOKEN_ISSUER,
                      leeway=10) # 10 Seconds fuzzy window for clock skewing


def generate_test_token(username='pat', memberOf=None, version=1, expires_at=9999999999999, issued_at=0):
    """Creates a test token that works with the `requires` and `deny` decorators
    for unit testing.

    :param username: The username of your test subject, muhahahaha!
    :type username: String

    :param memberOf: The group your test subject belongs to.
    :type memberOf: List

    :param version: The version of the token to generate
    :type version: Integer

    :param expires_at: The EPOC timestamp when the token expires
    :type expires_at: Integer/Float

    :param issued_at: The EPOC timestamp when the token was created
    :type issued_at: Integer/Float
    """
    if memberOf is None:
        memberOf = ['some-group']

    claims = {'exp' : expires_at,
              'iat' : issued_at,
              'iss' : const.AUTH_TOKEN_ISSUER,
              'username' : username,
              'version' : version,
              'memberOf' : memberOf,
             }
    return encode(claims, const.AUTH_TOKEN_PUB_KEY, algorithm=const.AUTH_TOKEN_ALGORITHM)
