# -*- coding: UTF-8 -*-
"""
This module contains variables that do not change during run time. The
idea is to only ever build one source of truth (be it a binary, or package), and
execute that same built thing regardless of the run time environment.
"""
from os import environ
from urllib.parse import urljoin
from collections import namedtuple, OrderedDict

import requests
VLAB_URL = environ.get('VLAB_URL', 'https://localhost')


def get_public_key():
    """Obtains the public key for token decryption

    This function leverages an environment variable to determine if the code is
    being testing, or running in production. This serves two needs::

        1) Dynamically obtain the RSA public key on service deploy for token
           decryption and verification.
        2) Unit test our microservices - thus the "no I/O allowed" rule

    The choice between the environment variable meaning "Yes we are testing" or
    "Yes we are in production" boils down to the "lesser of two evils" and the
    choice to default to "Yes we are testing" was made because our production
    framework is already configured to dealing with env vars -- that would be
    a new concept to the testing framework.
    """
    if not environ.get('PRODUCTION', False) in ('true', 'beta'):
        # This must be a local dev box
        return "testing"
    elif environ.get('PRODUCTION', False) == 'beta':
        # Must be a beta/integration server; so we're using self-signed TLS certs
        verify = False
    elif environ.get('PRODUCTION', False) == 'true':
        verify = True
    resp = requests.get(urljoin(VLAB_URL,'/api/1/auth/key'), verify=verify)
    resp.raise_for_status()
    data = resp.json()
    return data['content']['key']


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
