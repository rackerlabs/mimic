# -*- test-case-name: mimic.test.test_nova -*-
"""
Defines create, delete, get, list servers and get images and flavors.
"""

from uuid import uuid4
import json
import collections
import re
from itertools import cycle
from datetime import datetime
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
from mimic.util.helper import fmt as time_format

Request.defaultContentType = 'application/json'


@implementer(IAPIMock, IPlugin)
class NovaApi(object):
    """
    Rest endpoints for mocked Nova Api.
    """

    def __init__(self, regions=["ORD"]):
        """
        Create a NovaApi with an empty region cache, no servers or tenants yet.
        """
        self._regions = regions

    def catalog_entries(self, tenant_id):
        """
        List catalog entries for the Nova API.
        """
        return [
            Entry(
                tenant_id, "compute", "cloudServersOpenStack",
                [
                    Endpoint(tenant_id, region, text_type(uuid4()),
                             prefix="v2")
                    for region in self._regions
                ]
            )
        ]

    def resource_for_region(self, region, uri_prefix, session_store):
        """
        Get an :obj:`twisted.web.iweb.IResource` for the given URI prefix;
        implement :obj:`IAPIMock`.
        """
        return (NovaRegion(self, uri_prefix, session_store, region)
                .app.resource())


@implementer(IAPIMock)
class NovaInjectionApi(object):
    """
    An API for injecting alternate responses for specific tenants.

    :ivar _nova_api: A :obj:`NovaApi` instance.
    """

    def __init__(self, nova_api):
        """
        Create a NovaInjectionApi.
        """
        self._nova_api = nova_api

    def catalog_entries(self, tenant_id):
        return [Entry(
            tenant_id, "injection/compute", "mimicCompute",
            [Endpoint(tenant_id, each_region, text_type(uuid4()),
                      prefix="v1.0")
             for each_region in self._nova_api._regions]
        )]

    def resource_for_region(self, region, uri_prefix, session_store):
        return NovaInjector(self, region, uri_prefix,
                            session_store).app.resource()


class NovaInjector(object):
    """
    A region for :obj:`NovaInjectionApi`.

    :ivar str _region: The region we are controlling.
    :ivar str _uri_prefix: The URI prefix for this injector (note, not the
        prefix for the nova service...)
    :ivar _session_store: The :obj:`SessionStore` to get Nova sessions from.
    """

    app = MimicApp()

    def __init__(self, injection_api, region, uri_prefix, session_store):
        """
        

        :param _region: 

        :param _uri_prefix: 

        :param _session_store: 
        """
        self._injection_api = injection_api
        self._region = region
        self._uri_prefix = uri_prefix
        self._session_store = session_store

    @app.route("/v1.0/<tenant_id>", methods=["POST"])
    def inject(self, request, tenant_id):
        """
        
        """
        nova_session = (self._session_store
                        .session_for_tenant_id(tenant_id)
                        .data_for_api(
                            self._injection_api._nova_api,
                            lambda: collections.defaultdict(S_Cache))
        )[self._region]
        payload = json.loads(request.content.read())
        matcher = NovaMatcher.from_inject_json(payload)
        nova_session.add_matcher(matcher)
        request.setResponseCode(201)
        return b""


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



class DefaultNovaReaction(object):
    """
    
    """

    def response_for_creation(self, new_server_info):
        """
        
        """
        response_json = {
            'server': {
                "OS-DCF:diskConfig": new_server_info['OS-DCF:diskConfig'],
                "id": new_server_info['id'],
                "links": new_server_info['links'],
                "adminPass": "testpassword"
            }
        }
        return CreationResponse(response_json, 202)



class CustomNovaReaction(object):
    """
    A reaction to a server-creation request.
    """

    def __init__(self, create_response):
        """
        
        """
        self._create_response = create_response

    @classmethod
    def from_json(cls, reaction_json):
        """
        
        """
        return cls(reaction_json.get("create_response"))

    def response_for_creation(self, new_server_info):
        """
        
        """
        if self._create_response is None:
            return DefaultNovaReaction().response_for_creation(new_server_info)
        else:
            return CreationResponse(self._create_response["body"]["replace"],
                                    self._create_response["code"])



class NovaMatcher(object):
    """
    
    """

    def __init__(self, name_re, reactions):
        """
        
        """
        self._name_re = re.compile(name_re)
        self._reactions = cycle(reactions)

    @classmethod
    def from_inject_json(cls, inject_json):
        """
        
        """
        name_re = inject_json["match"]["name"]
        return cls(name_re, [
            CustomNovaReaction.from_json(reaction) for reaction in
            inject_json["reactions"]]
        )

    def does_match(self, server_request):
        """
        
        """
        return self._name_re.match(server_request['name'])

    def next_reaction(self):
        """
        
        """
        return next(self._reactions)


class S_Cache(dict):
    """
    Sketch: A replacement for s_cache-as-dictionary,
    s_cache-as-object-with-methods-and-attributes.  It's still a dictionary so
    that we can continue to treat it as one in the slightly crufty
    canned_responses module that expects dumb data structures rather than a
    structured object.
    """

    def __init__(self):
        """
        
        """
        self._matchers = []

    def add_matcher(self, matcher):
        """
        
        """
        self._matchers.append(matcher)

    def create_server(self, server_id, new_server_info):
        """
        Create a server, returning a :obj:`CreationResponse` that indicates the
        JSON body and HTTP response code.
        """
        self[server_id] = new_server_info
        for matcher in self._matchers:
            if matcher.does_match(new_server_info):
                reaction = matcher.next_reaction()
                break
        else:
            reaction = DefaultNovaReaction()

        return reaction.response_for_creation(new_server_info)


class CreationResponse(object):
    """
    A response to a server creation request.

    :ivar json: 
    :type json: 

    :ivar code: 
    :type code: 
    """

    def __init__(self, json, code):
        """
        

        :param json: 
        :type json: 

        :param code: 
        :type code: 
        """
        self.json = json
        self.code = code


class NovaRegion(object):
    """
    Klein routes for the API within a Cloud Servers region.

    :ivar dict _tenant_cache: a mapping of tenant_id (bytes) to a "server
        cache" (:obj:`S_Cache`), which itself maps server_id to a
        JSON-serializable data structure of the 'server' key of GET responses.
    """

    def __init__(self, api_mock, uri_prefix, session_store, name):
        """
        Create a nova region with a given URI prefix (used for generating URIs
        to servers).
        """
        self.uri_prefix = uri_prefix
        self._api_mock = api_mock
        self._session_store = session_store
        self._name = name

    def _server_cache_for_tenant(self, tenant_id):
        """
        Get the given server-cache object for the given tenant, creating one if
        there isn't one.
        """
        return (self._session_store.session_for_tenant_id(tenant_id)
                .data_for_api(self._api_mock,
                              lambda: collections.defaultdict(S_Cache))
                [self._name])

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
            s_cache=self._server_cache_for_tenant(tenant_id),
            current_time=datetime.utcfromtimestamp(
                self._session_store.clock.seconds()
            ).strftime(time_format)
        )
        request.setResponseCode(response_data[1])
        return json.dumps(response_data[0])

    @app.route('/v2/<string:tenant_id>/servers/<string:server_id>', methods=['GET'])
    def get_server(self, request, tenant_id, server_id):
        """
        Returns a generic get server response, with status 'ACTIVE'
        """
        response_data = get_server(
            server_id, self._server_cache_for_tenant(tenant_id),
            self._session_store.clock.seconds()
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

