# -*- test-case-name: mimic.test.test_nova -*-
"""
Defines create, delete, get, list servers and get images and flavors.
"""

from uuid import uuid4
import json

from characteristic import attributes
from six import text_type

from zope.interface import implementer

from twisted.web.server import Request

from twisted.python.urlpath import URLPath

from twisted.plugin import IPlugin
from twisted.web.http import CREATED

from mimic.canned_responses.nova import get_limit, get_image, get_flavor
from mimic.rest.mimicapp import MimicApp
from mimic.catalog import Entry
from mimic.catalog import Endpoint
from mimic.imimic import IAPIMock
from mimic.model.nova_objects import (
    BadRequestError, GlobalServerCollections, LimitError, Server)
from mimic.util.helper import bad_request

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

    def _get_session(self, session_store, tenant_id):
        """
        Retrieve or create a new Nova session from a given tenant identifier
        and :obj:`SessionStore`.

        For use with ``data_for_api``.

        Temporary hack; see this issue
        https://github.com/rackerlabs/mimic/issues/158
        """
        return (
            session_store.session_for_tenant_id(tenant_id)
            .data_for_api(self, lambda: GlobalServerCollections(
                tenant_id=tenant_id,
                clock=session_store.clock
            ))
        )


@implementer(IAPIMock, IPlugin)
@attributes(["nova_api"])
class NovaControlApi(object):

    """
    Rest endpoints for the Nova Control Api.
    """

    def catalog_entries(self, tenant_id):
        """
        List catalog entries for the Nova API.
        """
        return [
            Entry(
                tenant_id, "compute", "cloudServersBehavior",
                [
                    Endpoint(tenant_id, region, text_type(uuid4()),
                             prefix="v2")
                    for region in self.nova_api._regions
                ]
            )
        ]

    def resource_for_region(self, region, uri_prefix, session_store):
        """
        Get an :obj:`twisted.web.iweb.IResource` for the given URI prefix;
        implement :obj:`IAPIMock`.
        """
        return (NovaControlApiRegion(api_mock=self, uri_prefix=uri_prefix,
                                     session_store=session_store, region=region)
                .app.resource())


@attributes(["api_mock", "uri_prefix", "session_store", "region"])
class NovaControlApiRegion(object):
    """
    Klein resources for the Nova Control plane API
    """
    app = MimicApp()

    @app.route('/v2/<string:tenant_id>/behaviors/creation/', methods=['POST'])
    def register_creation_behavior(self, request, tenant_id):
        """
        Register the specified behavior to cause a future server creation
        operation to behave in the described way.

        The request looks like this::

            {
                # list of criteria for which requests will behave in the
                # described way
                "criteria": [
                    {"tenant_id": "maybe_fail_.*"},
                    {"server_name": "failing_server_.*"},
                    {"metadata": {"key_we_should_have": "fail",
                                  "key_we_should_not_have": null}}
                ],
                # what kind of behavior: in this case, "fail the request"
                "name": "fail",
                # parameters for the behavior: in this case,
                # "return a 404 with a message".
                "parameters": {
                    "code": 404,
                    "message": "Stuff is broken, what"
                }
            }
        """

        behavior_description = json.loads(request.content.read())
        region_collection = self._collection_from_tenant(tenant_id)
        region_collection.create_behavior_registry.register_from_json(
            behavior_description
        )
        request.setResponseCode(CREATED)
        return b''

    def _collection_from_tenant(self, tenant_id):
        """
        Retrieve the server collection for this region for the given tenant.
        """
        return (self.api_mock.nova_api
                ._get_session(self.session_store, tenant_id)
                .collection_for_region(self.region))



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

    def url(self, suffix):
        """
        Generate a URL to an object within the Nova URL hierarchy, given the
        part of the URL that comes after.
        """
        return str(URLPath.fromString(self.uri_prefix).child(suffix))

    def _region_collection_for_tenant(self, tenant_id):
        """
        Get the given server-cache object for the given tenant, creating one if
        there isn't one.
        """
        return (self._api_mock._get_session(self._session_store, tenant_id)
                .collection_for_region(self._name))

    app = MimicApp()

    @app.route('/v2/<string:tenant_id>/servers', methods=['POST'])
    def create_server(self, request, tenant_id):
        """
        Returns a generic create server response, with status 'ACTIVE'.
        """
        try:
            content = json.loads(request.content.read())
        except ValueError:
            request.setResponseCode(400)
            return json.dumps(bad_request("Invalid JSON request body"))

        try:
            creation = (self._region_collection_for_tenant(tenant_id)
                        .request_creation(request, content, self.url))
        except BadRequestError as e:
            request.setResponseCode(400)
            return json.dumps(bad_request(e.nova_message))
        except LimitError as e:
            request.setResponseCode(403)
            return json.dumps({
                "forbidden": {
                    "message": e.nova_message,
                    "code": 403
                }
            })

        return creation

    @app.route('/v2/<string:tenant_id>/servers/<string:server_id>', methods=['GET'])
    def get_server(self, request, tenant_id, server_id):
        """
        Returns a generic get server response, with status 'ACTIVE'
        """
        return (
            self._region_collection_for_tenant(tenant_id)
            .request_read(request, server_id, self.url)
        )

    @app.route('/v2/<string:tenant_id>/servers', methods=['GET'])
    def list_servers(self, request, tenant_id):
        """
        Returns list of servers that were created by the mocks, with the given
        name.
        """
        return (
            self._region_collection_for_tenant(tenant_id)
            .request_list(
                request, include_details=False, absolutize_url=self.url,
                name=request.args.get('name', [u""])[0]
            )
        )

    @app.route('/v2/<string:tenant_id>/servers/detail', methods=['GET'])
    def list_servers_with_details(self, request, tenant_id):
        """
        Returns list of servers that were created by the mocks, with details
        such as the metadata.
        """
        return (
            self._region_collection_for_tenant(tenant_id)
            .request_list(
                request, include_details=True, absolutize_url=self.url,
                name=request.args.get('name', [u""])[0]
            )
        )

    @app.route('/v2/<string:tenant_id>/servers/<string:server_id>',
               methods=['DELETE'])
    def delete_server(self, request, tenant_id, server_id):
        """
        Returns a 204 response code, for any server id'
        """
        return (
            self._region_collection_for_tenant(tenant_id)
            .request_delete(request, server_id)
        )

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
        Returns the IP addresses for the specified server.
        """
        return (
            self._region_collection_for_tenant(tenant_id).request_ips(
                request, server_id
            )
        )

    @app.route('/v2/<string:tenant_id>/servers/<string:server_id>/metadata',
               branch=True)
    def handle_server_metadata(self, request, tenant_id, server_id):
        """
        Handle metadata requests associated with a particular server.  Server
        not found error message verified as of 2015-04-23 against Rackspace
        Nova.
        """
        server = (self._region_collection_for_tenant(tenant_id)
                  .server_by_id(server_id))
        if server is None:
            request.setResponseCode(404)
            return json.dumps({
                'itemNotFound': {
                    'message': 'Server does not exist',
                    'code': 404
                }
            })
        return ServerMetadata(server).app.resource()


class ServerMetadata(object):

    """
    Klein routes for a particular server's metadata.
    """

    def __init__(self, server):
        """
        Handle requests having to deal a server's metadata.  No URIs
        are generated or used.
        """
        self._server = server

    app = MimicApp()

    @app.route('/', methods=['GET'])
    def list_metadata(self, request):
        """
        List all metadata associated with a server.
        """
        return json.dumps({'metadata': self._server.metadata})

    @app.route('/', methods=['PUT'])
    def set_metadata(self, request):
        """
        Set the metadata for the specified server - this replaces whatever
        metadata was there.  The resulting metadata is not a union of the
        previous metadata and the new metadata - it is *just* the new
        metadata.

        The body must look like:

        ``{"metadata": {...}}``

        although

        ``{"metadata": {...}, "other": "garbage", "keys": "included"}``

        is ok too.

        All the response messages and codes have been verified as of
        2015-04-23 against Rackspace Nova.
        """
        try:
            content = json.loads(request.content.read())
        except ValueError:
            request.setResponseCode(400)
            return json.dumps(bad_request("Malformed request body"))

        # more than one key is ok, non-"meta" keys are just ignored
        if 'metadata' not in content:
            request.setResponseCode(400)
            return json.dumps(bad_request("Malformed request body"))

        # When setting metadata, None is special for some reason
        if content['metadata'] is None:
            request.setResponseCode(400)
            return json.dumps(bad_request(
                "Malformed request body. metadata must be object"))

        try:
            Server.validate_metadata(content['metadata'])
        except BadRequestError as e:
            request.setResponseCode(400)
            return json.dumps(bad_request(e.nova_message))
        except LimitError as e:
            request.setResponseCode(403)
            return json.dumps({
                "forbidden": {
                    "message": e.nova_message,
                    "code": 403
                }
            })

        self._server.metadata = content['metadata']
        return json.dumps({'metadata': content['metadata']})

    @app.route('/<key>', methods=['PUT'])
    def set_metadata_item(self, request, key):
        """
        Set a metadata item.  The body must look like:

        ``{"meta": {<key>: value}}``

        although

        ``{"meta": {<key>: value}, "other": "garbage", "keys": "included"}``

        is ok too.

        All the response messages and codes have been verified as of
        2015-04-23 against Rackspace Nova.
        """
        try:
            content = json.loads(request.content.read())
        except ValueError:
            request.setResponseCode(400)
            return json.dumps(bad_request("Malformed request body"))

        # more than one key is ok, non-"meta" keys are just ignored
        if 'meta' not in content or not isinstance(content['meta'], dict):
            request.setResponseCode(400)
            return json.dumps(bad_request("Malformed request body"))

        if len(content['meta']) > 1:
            request.setResponseCode(400)
            return json.dumps(bad_request(
                "Request body contains too many items"))

        if key not in content['meta']:
            request.setResponseCode(400)
            return json.dumps(bad_request("Request body and URI mismatch"))

        try:
            self._server.set_metadata_item(key, content['meta'][key])
        except BadRequestError as e:
            request.setResponseCode(400)
            return json.dumps(bad_request(e.nova_message))
        except LimitError as e:
            request.setResponseCode(403)
            return json.dumps({
                "forbidden": {
                    "message": e.nova_message,
                    "code": 403
                }
            })

        # no matter how many keys were passed in, only the meta key is
        # returned
        return json.dumps({'meta': content['meta']})
