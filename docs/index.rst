Welcome to Mimic's documentation!
=================================

Mimic is an API-compatible mock service for `Openstack Compute`_ and
Rackspace's implementation of `Identity`_ and `Cloud Load Balancers`_. It is
backed by in-memory data structure rather than a potentially expensive
database.

Mimic helps with:

* fast set-up
* instant response
* cost efficient
* enables offline development
* enables ability to test unusual behaviors/errors of an api
* acts as a central repository for mocked responses from services


Documentation
-------------
.. toctree::
    :maxdepth: 2

    development/index
    changelog


.. _`Openstack Compute`: http://docs.openstack.org/api/openstack-compute/2/content/
.. _`Identity`: http://docs.rackspace.com/auth/api/v2.0/auth-client-devguide/content/Overview-d1e65.html
.. _`Cloud Load Balancers`: http://docs.rackspace.com/loadbalancers/api/v1.0/clb-devguide/content/Overview-d1e82.html
