# -*- coding: UTF-8 -*-
"""
This module contains variables that do not change during run time. The
idea is to only ever build one source of truth (be it a binary, or package), and
execute that same built thing regardless of the run time environment.
"""
import time
from os import environ
from urllib.parse import urljoin
from collections import namedtuple, OrderedDict

import requests
from requests.exceptions import ConnectionError

VLAB_URL = environ.get('VLAB_URL', 'https://localhost')


def get_encryption_data():
    """Dynamically obtain the Auth token public key and encryption algorithm.

    This function will make an API call to the auth server upon service start up
    when the environment variable ``PRODUCTION`` is set to ``true`` or ``beta``.
    The value of ``beta`` allows for the auth server to use a self-signed TLS cert.
    This function will attempt upwards of 10 times (once every second) to connect
    to the auth server, and raise a RuntimeError if it's unable to connect.
    This makes services more robust upon startup due to the dependence on the
    auth server being ready for API requests.

    :Returns: Tuple

    :Raises: RuntimeError
    """
    if not environ.get('PRODUCTION', False) in ('true', 'beta'):
        # This must be a local dev box
        return "testing", "HS256", "string"
    elif environ.get('PRODUCTION', False) == 'beta':
        # Must be a beta/integration server; so we're using self-signed TLS certs
        verify = False
    elif environ.get('PRODUCTION', False) == 'true':
        verify = True
    # Retries to address race when all services start up at once
    for _ in range(10):
        try:
            resp = requests.get(urljoin(VLAB_URL,'/api/1/auth/key'), verify=verify)
        except ConnectionError:
            time.sleep(1)
        else:
            resp.raise_for_status()
            data = resp.json()
            break
    else:
        error = "Unable to connect to auth server"
        raise RuntimeError(error)
    return data['content']['key'], data['content']['algorithm'], data['content']['format']


PUBLIC_KEY, ALGORITHM, KEY_FORMAT = get_encryption_data()

DEFINED = OrderedDict([
            ('VLAB_URL', VLAB_URL),
            ('AUTH_TOKEN_ALGORITHM', ALGORITHM),
            ('AUTH_TOKEN_PUB_KEY', PUBLIC_KEY),
            ('AUTH_TOKEN_KEY_FORMAT', KEY_FORMAT),
            ('AUTH_TOKEN_ISSUER', VLAB_URL),
            ('AUTH_TOKEN_VERSION', int(environ.get('AUTH_TOKEN_VERSION', 1))),
          ])

Constants = namedtuple('Constants', list(DEFINED.keys()))

# The '*' expands the list, just liked passing a function *args
const = Constants(*list(DEFINED.values()))
