from mimic.test.helpers import request
from mimic.core import MimicCore
from mimic.resource import MimicRoot
from twisted.internet.task import Clock
import json
import treq


class MimicTestFixture(object):
    """
    Provides common functionality for mimic tests
    """

    def __init__(self, test_case, apis):
        """
        apis is a list of the APIs to be initiated
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
        # The following section is specific to the legacy NovaAPI tests
        try:
            self.uri = self.nth_endpoint_public(0)
            self.server_name = 'test_server'
            create_server = request(
                self, self.root, "POST", self.uri + '/servers',
                json.dumps({
                    "server": {
                        "name": self.server_name,
                        "imageRef": "test-image",
                        "flavorRef": "test-flavor"
                    }
                }))
            self.create_server_response = test_case.successResultOf(create_server)
            create_server_response_body = test_case.successResultOf(
                treq.json_content(self.create_server_response))
            self.server_id = create_server_response_body['server']['id']
        except:
            pass

    def nth_endpoint_public(self, n):
        """
        Return the publicURL for the ``n``th endpoint.
        TODO: Consider that this might be a problem if you create more than one api
        """
        return (
            self.service_catalog_json
            ['access']['serviceCatalog'][0]['endpoints'][n]['publicURL']
        )

    def get_service_endpoint(self, service_name, region=''):
        """
        Return the publicURL for the given service and region. Note that if there are multiple
        endpoints for a given region, the first will be returned, and if no region is specified,
        the first endpoint will be returned. If the service_name or region are not in the catalog,
        this function will produce and exception
        """
        for service in self.service_catalog_json['access']['serviceCatalog']:
            if service['name'] == service_name:
                for item in service['endpoints']:
                    if (item['region'] == region) or (region == ''):
                        return item['publicURL']
