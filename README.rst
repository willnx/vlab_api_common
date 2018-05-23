.. image:: https://travis-ci.org/willnx/vlab_api_common.svg?branch=master
   :target: https://travis-ci.org/willnx/vlab_api_common

###############
vlab_api_common
###############

Common logic used by every API within vLab - things like making response
shapes consistent, providing functionality for the ``describe`` parameter, etc.


****************************************
The ``requires`` and ``deny`` decorators
****************************************

These decorators are used together to create an `Access Control List <https://en.wikipedia.org/wiki/Access_control_list>`_
for your Flask API. You can layer these directorates however you want, but beware -
*"With great power comes great responsibility."*

Examples
========

Here are some examples of using the ``requires`` and ``deny`` decorators.

Basic Syntax
------------

To use the ``requires`` or ``deny`` decorators in your Flask API, simply add them
to your function before ``@app.route``. You should also accpet ``**kwargs`` because
additional information like the token and validation information will be passed
along.

This example will allow any user with a valid token access:

.. code-block:: python

   from vlab_api_common import requires, deny
   @requires()
   @app.route('/api/1/foo')
   def hello(**kwargs):
     return "hello world"


While this example shows how to forbid ``jordan`` access:

.. code-block:: python

   from vlab_api_common import requires, deny
   @deny(username='jordan')
   @app.route('/api/1/foo')
   def hello(**kwargs):
     return "hello world"

Verifying
---------

In this example, any user with a valid authentication token will be able to
perform an HTTP GET on the API end point.

.. code-block:: python

   @requires(verify=False)
   @app.route('/api/1/foo')
   def hello(**kwargs):
     return "hello world!"

The difference in this next example is that the ``requires`` decorator will check
with the configured vLab Authentication Service to ensure that the user has not
deleted their token:

.. code-block:: python

   @requires()
   @app.route('/api/1/foo')
   def hello(**kwargs):
     return "hello world!"

Notice how this is the default behavior. If you have a resource that's not very
sensitive, and have extremely high requirements on availability, consider explicitly
setting ``verify=False`` on the ``requires`` and ``deny`` decorators.

The ``verify`` keyword argument applies to both the ``requires`` and ``deny`` decorators.


OR-ing identities
------------------

You can specify multiple values in the ``requires`` and ``deny`` decorators.
When you specify more than one value in a single decorator, the identities
are ``OR`` ed. In other words, the moment an identity in the token matches a defined
value, the user is granted access.

In this example, if the user is named `bob` but he is not part of `Department A`,
then the user is still granted access:

.. code-block:: python

   @requires(username=('bob', 'sarah'), memberOf='Department A')
   @app.route('/api/1/foo')
   def hello(**kwargs):
     return "Hello World!"

AND-ing identities
-------------------

When you layer multiple ``requires`` and/or ``deny`` decorators together, you ``AND``
those decoratores. In other words, all decorators must return successfully for
the user to be granted access.

In this example, only ``forest`` and ``jenny`` from ``Department A`` will be granted
access. All other members within `Department A` will not be granted access

.. code-block:: python

   @requires(username=('forest', 'jenny'))
   @requires(memberOf='Department A')
   @app.route('/api/1/foo')
   def hello(**kwargs):
     return "hello forest or jenny from Department A!"
