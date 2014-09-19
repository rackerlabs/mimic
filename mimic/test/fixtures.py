"""
Define fixtures to provide common functionality for Mimic testing
"""
from mimic.test.helpers import request
from mimic.core import MimicCore
from mimic.resource import MimicRoot
from twisted.internet.task import Clock
import json
import treq


class APIMockHelper(object):
    """
    Provides common functionality for mimic tests
    """

    def __init__(self, test_case, apis):
        """
        Initialize a mimic core and the specified :obj:`mimic.imimic.IAPIMock`s
        :param apis: A list of :obj:`mimic.imimic.IAPIMock` objects to be initialized
        """
        self.core = MimicCore(Clock(), apis)
        self.root = MimicRoot(self.core).app.resource()
        # Pass in arbitrary username and password
        response = request(
            self, self.root, "POST", "/identity/v2.0/tokens",
            json.dumps({
                "auth": {
                    "passwordCredentials": {
                        "username": "test1",
                        "password": "test1password",
                    },
                }
            })
        )
        auth_response = test_case.successResultOf(response)
        self.service_catalog_json = test_case.successResultOf(
            treq.json_content(auth_response))
        self.uri = self.nth_endpoint_public(0)

    def nth_endpoint_public(self, n):
        """
        Return the publicURL for the ``n``th endpoint.
        :param int n: The index of the endpoint in the first catalog entry to return
        """
        return (
            self.service_catalog_json
            ['access']['serviceCatalog'][0]['endpoints'][n]['publicURL']
        )

    def get_service_endpoint(self, service_name, region=''):
        """
        Return the publicURL for the given service and region. Note that if there are multiple
        endpoints for a given region, the first will be returned, and if no region is specified,
        the first endpoint will be returned.
        :param unicode service_name: The name of the service for which to get an endpoint as
            listed in the service catalog
        :param unicode region: The service catalog region of the desired endpoint
        """
        for service in self.service_catalog_json['access']['serviceCatalog']:
            if service['name'] == service_name:
                for item in service['endpoints']:
                    if (item['region'] == region) or (region == ''):
                        return item['publicURL']
