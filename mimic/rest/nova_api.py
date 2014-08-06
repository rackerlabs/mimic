"""
Defines create, delete, get, list servers and get images and flavors.
"""

from uuid import uuid4
import json
from random import randrange

from six import text_type

from zope.interface import implementer

from twisted.web.server import Request

from twisted.plugin import IPlugin

from mimic.canned_responses.nova import (get_server, list_server, get_limit,
                                         create_server, delete_server,
                                         get_image, get_flavor, list_addresses)
from mimic.rest.mimicapp import MimicApp
from mimic.catalog import Entry
from mimic.catalog import Endpoint
from mimic.imimic import IAPIMock

Request.defaultContentType = 'application/json'


@implementer(IAPIMock, IPlugin)
class NovaApi(object):
    """
    Rest endpoints for mocked Nova Api.
    """

    def catalog_entries(self, tenant_id):
        """
        List catalog entries for the Nova API.
        """
        return [
            Entry(
                tenant_id, "compute", "cloudServersOpenStack",
                [
                    Endpoint(tenant_id, "ORD", text_type(uuid4()), prefix="v2")
                ]
            )
        ]

    def resource_for_region(self, uri_prefix):
        """
        Get an :obj:`twisted.web.iweb.IResource` for the given URI prefix;
        implement :obj:`IAPIMock`.
        """
        return NovaRegion(uri_prefix).app.resource()


def _list_servers(request, tenant_id, details=False):
    """
    Return a list of servers, possibly filtered by name, possibly with details
    """
    server_name = None
    if 'name' in request.args:
        server_name = request.args['name'][0]
    response_data = list_server(tenant_id, server_name, details=details)
    request.setResponseCode(response_data[1])
    return json.dumps(response_data[0])


class NovaRegion(object):
    """
    Klein routes for the API within a Cloud Servers region.
    """

    def __init__(self, uri_prefix):
        """
        Create a nova region with a given URI prefix (used for generating URIs
        to servers).
        """
        self.uri_prefix = uri_prefix

    app = MimicApp()

    @app.route('/v2/<string:tenant_id>/servers', methods=['POST'])
    def create_server(self, request, tenant_id):
        """
        Returns a generic create server response, with status 'ACTIVE'.
        """
        server_id = 'test-server{0}-id-{0}'.format(str(randrange(9999999999)))
        content = json.loads(request.content.read())
        response_data = create_server(tenant_id, content['server'], server_id,
                                      self.uri_prefix)
        request.setResponseCode(response_data[1])
        return json.dumps(response_data[0])

    @app.route('/v2/<string:tenant_id>/servers/<string:server_id>', methods=['GET'])
    def get_server(self, request, tenant_id, server_id):
        """
        Returns a generic get server response, with status 'ACTIVE'
        """
        response_data = get_server(server_id)
        request.setResponseCode(response_data[1])
        return json.dumps(response_data[0])

    @app.route('/v2/<string:tenant_id>/servers', methods=['GET'])
    def list_servers(self, request, tenant_id):
        """
        Returns list of servers that were created by the mocks, with the given name.
        """
        return _list_servers(request, tenant_id)

    @app.route('/v2/<string:tenant_id>/servers/detail', methods=['GET'])
    def list_servers_with_details(self, request, tenant_id):
        """
        Returns list of servers that were created by the mocks, with details such as the metadata.
        """
        return _list_servers(request, tenant_id, details=True)

    @app.route('/v2/<string:tenant_id>/servers/<string:server_id>', methods=['DELETE'])
    def delete_server(self, request, tenant_id, server_id):
        """
        Returns a 204 response code, for any server id'
        """
        response_data = delete_server(server_id)
        request.setResponseCode(response_data[1])
        return json.dumps(response_data[0])

    @app.route('/v2/<string:tenant_id>/images/<string:image_id>', methods=['GET'])
    def get_image(self, request, tenant_id, image_id):
        """
        Returns a get image response, for any given imageid
        """
        response_data = get_image(image_id)
        request.setResponseCode(response_data[1])
        return json.dumps(response_data[0])

    @app.route('/v2/<string:tenant_id>/flavors/<string:flavor_id>', methods=['GET'])
    def get_flavor(self, request, tenant_id, flavor_id):
        """
        Returns a get flavor response, for any given flavorid
        """
        response_data = get_flavor(flavor_id)
        request.setResponseCode(response_data[1])
        return json.dumps(response_data[0])

    @app.route('/v2/<string:tenant_id>/limits', methods=['GET'])
    def get_limit(self, request, tenant_id):
        """
        Returns a get flavor response, for any given flavorid
        """
        request.setResponseCode(200)
        return json.dumps(get_limit())

    @app.route('/v2/<string:tenant_id>/servers/<string:server_id>/ips', methods=['GET'])
    def get_ips(self, request, tenant_id, server_id):
        """
        Returns a get flavor response, for any given flavorid.
        (currently the GET ips works only after a GET server after the server is created)
        """
        response_data = list_addresses(server_id)
        request.setResponseCode(response_data[1])
        return json.dumps(response_data[0])
