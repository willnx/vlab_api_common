# -*- coding: UTF-8 -*-
"""
This module contains run time variables that do not change during run time. The
idea is to only ever build one source of truth (be it a binary, or package), and
execute that same built thing regardless of the runtime environment.
"""
from os import environ, path
from collections import namedtuple, OrderedDict

import requests
VLAB_URL = environ.get('VLAB_URL', 'https://localhost')


def get_public_key():
    """Obtains the public RSA key for token decryption

    This function leverages an environement varible to determine if the code is
    being testing, or running in production. This serves two needs::

        1) Dynamically obtain the RSA public key on service deploy for token
           decryption and varification.
        2) Unit test our microservices - thus the "no I/O allowed" rule

    The choice between the environment varible meaning "Yes we are testing" or
    "Yes we are in production" boils down to the "lesser of two evils" and the
    choice to default to "Yes we are testing" was made because our production
    framework is already configured to dealing with env vars -- that would be
    a new concept to the testing framework.
    """
    if environ.get('PRODUCTION', False) == 'true':
        resp = requests.get(path.join(VLAB_URL,'/api/1/auth/key'))
        resp.raise_for_status()
        data = resp.json()
        return data['content']['key']
    else:
        # assume we are testing
        return "testing"

DEFINED = OrderedDict([
            ('VLAB_URL', VLAB_URL),
            ('AUTH_TOKEN_ALGORITHM', environ.get('AUTH_TOKEN_ALGORITHM', 'HS256')),
            ('AUTH_TOKEN_PUB_KEY', get_public_key()),
            ('AUTH_TOKEN_KEY_FORMAT', 'pem'),
            ('AUTH_TOKEN_ISSUER', VLAB_URL),
            ('AUTH_TOKEN_VERSION', int(environ.get('AUTH_TOKEN_VERSION', 1))),
          ])

Constants = namedtuple('Constants', list(DEFINED.keys()))

# The '*' expands the list, just liked passing a function *args
const = Constants(*list(DEFINED.values()))
