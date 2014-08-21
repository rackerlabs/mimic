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
class NovaErrorInjection(object):
    """
    Construct an error injector as a separate service in the service catalog.
    """

    def __init__(self, nova_api):
        """
        Construct a NovaErrorInjection around a :obj:`NovaApi`.
        """
        self.nova_api = nova_api


    def catalog_entries(self, tenant_id):
        """
        Construct a single catalog entry.
        """
        return [
            Entry(
                tenant_id, "mimic-control-compute",
                "computeMimicErrorInjection",
                [
                    Endpoint(tenant_id, "all", text_type(uuid4()),
                             prefix="mimic-v2"),
                ]
            )
        ]


    def resource_for_region(self):
        """
        TODO: implement some control APIs.
        """
        return None


@implementer(IAPIMock, IPlugin)
class NovaApi(object):
    """
    Rest endpoints for mocked Nova Api.

    :ivar dict _region_cache: A mapping of (region (bytes)) to a tenant cache;
        see :pyobj:`NovaRegion`
    """

    def __init__(self):
        """
        Create a NovaApi with an empty region cache, no servers or tenants yet.
        """
        self._region_cache = {}

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

    def resource_for_region(self, region, uri_prefix):
        """
        Get an :obj:`twisted.web.iweb.IResource` for the given URI prefix;
        implement :obj:`IAPIMock`.
        """
        return NovaRegion(
            uri_prefix, self._region_cache.setdefault(region, {})
        ).app.resource()

    def control_plane(self):
        """
        
        """
        return MimicNova()


def _list_servers(request, tenant_id, s_cache, details=False):
    """
    Return a list of servers, possibly filtered by name, possibly with details
    """
    server_name = None
    if 'name' in request.args:
        server_name = request.args['name'][0]
    response_data = list_server(tenant_id, s_cache, server_name,
                                details=details)
    request.setResponseCode(response_data[1])
    return json.dumps(response_data[0])

class Matcher(object):
    """
    
    """

    def does_match_server(self, server_id, server_info):
        """
        
        """
        return (self.condition.matches_id(server_id) or
                self.condition.matches_metadata(server_info['metadata']))



class S_Cache(dict):
    """
    
    """
    def __init__(self):
        """
        
        """
        self.matchers = []


    def add_failure_matcher(self, condition, response):
        """
        
        """
        self.matchers.append(Matcher(condition, response))


    def server_creation_check(self, server_id, server_info):
        """
        
        """
        for matcher in self.matchers:
            if matcher.does_match_server(server_id, server_info):
                return matcher.response_for_server(server_id, server_info)
        return None



class NovaRegion(object):
    """
    Klein routes for the API within a Cloud Servers region.

    :ivar dict _tenant_cache: a mapping of tenant_id (bytes) to a "server
        cache" (dictionary), which itself maps server_id to a JSON-serializable
        data structure of the 'server' key of GET responses.
    """

    def __init__(self, uri_prefix, tenant_cache):
        """
        Create a nova region with a given URI prefix (used for generating URIs
        to servers).
        """
        self.uri_prefix = uri_prefix
        self._tenant_cache = tenant_cache

    def _server_cache_for_tenant(self, tenant_id):
        """
        Get the given server-cache object for the given tenant, creating one if
        there isn't one.
        """
        return self._tenant_cache.setdefault(tenant_id, S_Cache())

    app = MimicApp()

    @app.route('/v2/<string:tenant_id>/servers', methods=['POST'])
    def create_server(self, request, tenant_id):
        """
        Returns a generic create server response, with status 'ACTIVE'.
        """
        server_id = 'test-server{0}-id-{0}'.format(str(randrange(9999999999)))
        content = json.loads(request.content.read())
        response_data = create_server(
            tenant_id, content['server'], server_id,
            self.uri_prefix,
            s_cache=self._server_cache_for_tenant(tenant_id)
        )
        request.setResponseCode(response_data[1])
        return json.dumps(response_data[0])

    @app.route('/v2/<string:tenant_id>/servers/<string:server_id>', methods=['GET'])
    def get_server(self, request, tenant_id, server_id):
        """
        Returns a generic get server response, with status 'ACTIVE'
        """
        response_data = get_server(
            server_id, s_cache=self._server_cache_for_tenant(tenant_id)
        )
        request.setResponseCode(response_data[1])
        return json.dumps(response_data[0])

    @app.route('/v2/<string:tenant_id>/servers', methods=['GET'])
    def list_servers(self, request, tenant_id):
        """
        Returns list of servers that were created by the mocks, with the given
        name.
        """
        return _list_servers(request, tenant_id,
                             s_cache=self._server_cache_for_tenant(tenant_id))

    @app.route('/v2/<string:tenant_id>/servers/detail', methods=['GET'])
    def list_servers_with_details(self, request, tenant_id):
        """
        Returns list of servers that were created by the mocks, with details
        such as the metadata.
        """
        return _list_servers(request, tenant_id, details=True,
                             s_cache=self._server_cache_for_tenant(tenant_id))

    @app.route('/v2/<string:tenant_id>/servers/<string:server_id>', methods=['DELETE'])
    def delete_server(self, request, tenant_id, server_id):
        """
        Returns a 204 response code, for any server id'
        """
        response_data = delete_server(
            server_id, s_cache=self._server_cache_for_tenant(tenant_id)
        )
        request.setResponseCode(response_data[1])
        return json.dumps(response_data[0])

    @app.route('/v2/<string:tenant_id>/images/<string:image_id>', methods=['GET'])
    def get_image(self, request, tenant_id, image_id):
        """
        Returns a get image response, for any given imageid
        """
        response_data = get_image(
            image_id, s_cache=self._server_cache_for_tenant(tenant_id)
        )
        request.setResponseCode(response_data[1])
        return json.dumps(response_data[0])

    @app.route('/v2/<string:tenant_id>/flavors/<string:flavor_id>', methods=['GET'])
    def get_flavor(self, request, tenant_id, flavor_id):
        """
        Returns a get flavor response, for any given flavorid
        """
        response_data = get_flavor(
            flavor_id,
            s_cache=self._server_cache_for_tenant(tenant_id)
        )
        request.setResponseCode(response_data[1])
        return json.dumps(response_data[0])

    @app.route('/v2/<string:tenant_id>/limits', methods=['GET'])
    def get_limit(self, request, tenant_id):
        """
        Returns a get flavor response, for any given flavorid
        """
        request.setResponseCode(200)
        return json.dumps(
            get_limit(s_cache=self._server_cache_for_tenant(tenant_id))
        )

    @app.route('/v2/<string:tenant_id>/servers/<string:server_id>/ips', methods=['GET'])
    def get_ips(self, request, tenant_id, server_id):
        """
        Returns a get flavor response, for any given flavorid.
        (currently the GET ips works only after a GET server after the server is created)
        """
        response_data = list_addresses(
            server_id,
            s_cache=self._server_cache_for_tenant(tenant_id)
        )
        request.setResponseCode(response_data[1])
        return json.dumps(response_data[0])
