"""
Define fixtures to provide common functionality for Mimic testing
"""

from __future__ import absolute_import, division, unicode_literals

from mimic.test.helpers import json_request
from mimic.core import MimicCore
from mimic.resource import MimicRoot
from twisted.internet.task import Clock


class TenantAuthentication(object):
    """
    Provides some functionality to help log into mimic identity with a
    particular username and password
    """
    def __init__(self, test_case, root, username, password):
        """
        Authenticate a particular user against the mimic root.

        :param root: The :class:`twisted.web.resource.IResource` at the root
            of the mimic API resource tree.

        :param username: the username to authenticate as
        :param password: the password with which to use to authenticate
        """
        _, self.service_catalog_json = test_case.successResultOf(json_request(
            test_case, root, b"POST", b"/identity/v2.0/tokens",
            {
                "auth": {
                    "passwordCredentials": {
                        "username": username,
                        "password": password,
                    },
                }
            }
        ))

    def get_tenant_id(self):
        """
        Return the tenant id from the service catalog
        """
        return self.service_catalog_json['access']['token']['tenant']['id']

    def get_service_endpoint(self, service_name, region=''):
        """
        Return the publicURL for the given service and region. Note that if
        there are multiple endpoints for a given region, the first will be
        returned, and if no region is specified, the first endpoint will be
        returned.
        :param unicode service_name: The name of the service for which to get
            an endpoint as listed in the service catalog.
        :param unicode region: The service catalog region of the desired
            endpoint.
        :raises: KeyError when unable to locate the service in the service
            catalog.
        """
        for service in self.service_catalog_json['access']['serviceCatalog']:
            if service['name'] == service_name:
                for item in service['endpoints']:
                    if (item['region'] == region) or (region == ''):
                        return item['publicURL']

        raise KeyError(
            "No such service '{0}' for region '{1}' in Service Catalog "
            "-'{2}'".format(
                service_name,
                region,
                self.service_catalog_json['access']['serviceCatalog']
            )
        )


class APIMockHelper(object):
    """
    Provides common functionality for mimic tests
    """

    def __init__(self, test_case, apis):
        """
        Initialize a mimic core and the specified :obj:`mimic.imimic.IAPIMock`s

        :param apis: A list of :obj:`mimic.imimic.IAPIMock` objects to be
            initialized
        """
        self.test_case = test_case
        self.clock = Clock()
        self.core = MimicCore(self.clock, apis)
        self.root = MimicRoot(self.core).app.resource()

        # Pass in arbitrary username and password
        self.auth = TenantAuthentication(test_case, self.root,
                                         "test1", "test1password")

        # map some attributes and methods
        self.service_catalog_json = self.auth.service_catalog_json
        self.get_service_endpoint = self.auth.get_service_endpoint

        # Tenant ID of test tenant authenticated against mimic identity
        self.tenant_id = self.auth.service_catalog_json["access"]["token"]["tenant"]["id"]
        service_name = apis[0].catalog_entries(self.tenant_id)[0].name
        self.uri = self.get_service_endpoint(service_name)


class APIDomainMockHelper(object):
    """
    Provides common functionality for testing API domain mocks
    """

    def __init__(self, test_case, domains):
        """
        Initialize a mimic core and the specified :obj:`mimic.imimic.IAPIMock`s

        :param domains: A list of :obj:`mimic.imimic.IAPIDomainMock` objects to
            be initialized
        """
        self.test_case = test_case
        self.clock = Clock()
        self.core = MimicCore(self.clock, [], domains=domains)
        self.root = MimicRoot(self.core).app.resource()

        self.uri = '/domain/{0}'.format(domains[0].domain())
