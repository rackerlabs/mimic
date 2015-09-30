# -*- test-case-name: mimic.test.test_nova -*-
"""
Defines create, delete, get, list servers and get images and flavors.
"""

from uuid import uuid4
import json

from characteristic import attributes
from six import text_type

from zope.interface import implementer

from twisted.python.urlpath import URLPath

from twisted.plugin import IPlugin
from twisted.web.http import CREATED, BAD_REQUEST

from mimic.canned_responses.nova import get_limit
from mimic.model.keypair_objects import GlobalKeyPairCollections, KeyPair
from mimic.rest.mimicapp import MimicApp
from mimic.catalog import Entry
from mimic.catalog import Endpoint
from mimic.imimic import IAPIMock
from mimic.model.behaviors import make_behavior_api
from mimic.model.nova_objects import (
    BadRequestError, GlobalServerCollections, LimitError, Server,
    bad_request, forbidden, not_found, server_creation)
from mimic.model.flavor_collections import GlobalFlavorCollection
from mimic.model.image_collections import GlobalImageCollection


@implementer(IAPIMock, IPlugin)
class NovaApi(object):

    """
    Rest endpoints for mocked Nova Api.
    """

    def __init__(self, regions=["ORD", "IAD", "DFW"]):
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


NovaControlApiRegionBehaviors = make_behavior_api(
    {'creation': server_creation})
"""
Handlers for CRUD operations on create server behaviors.

:ivar registry_collection: an instance of
    :class:`mimic.model.behaviors.BehaviorRegistryColelction`
"""


@attributes(["api_mock", "uri_prefix", "session_store", "region"])
class NovaControlApiRegion(object):
    """
    Klein resources for the Nova Control plane API
    """
    app = MimicApp()

    @app.route('/v2/<string:tenant_id>/behaviors', branch=True)
    def handle_behaviors(self, request, tenant_id):
        """
        Return the behavior CRUD resource.
        """
        region_collection = self._collection_from_tenant(tenant_id)
        behavior_handler = NovaControlApiRegionBehaviors(
            region_collection.behavior_registry_collection)
        return behavior_handler.app.resource()

    @app.route("/v2/<string:tenant_id>/attributes/", methods=['POST'])
    def change_attributes(self, request, tenant_id):
        """
        Modify the specified attributes on existing servers.

        The request looks like this::

            {
                "status": {
                    "test_server_id_8482197407": "ERROR",
                    "test_server_id_0743289146": "BUILD"
                }
            }

        As more attributes are added, they should be additional top-level keys
        where "status" goes in this request.
        """
        region_collection = self._collection_from_tenant(tenant_id)
        attributes_description = json.loads(request.content.read())
        statuses_description = attributes_description["status"]
        servers = [region_collection.server_by_id(server_id)
                   for server_id in statuses_description]
        if None in servers:
            request.setResponseCode(BAD_REQUEST)
            return b''
        for server in servers:
            server.update_status(statuses_description[server.server_id])
        request.setResponseCode(CREATED)
        return b''

    def _collection_from_tenant(self, tenant_id):
        """
        Retrieve the server collection for this region for the given tenant.
        """
        return (self.api_mock.nova_api._get_session(self.session_store, tenant_id)
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

    def _image_collection_for_tenant(self, tenant_id):
        tenant_session = self._session_store.session_for_tenant_id(tenant_id)
        image_global_collection = tenant_session.data_for_api(
            "image_collection",
            lambda: GlobalImageCollection(tenant_id=tenant_id,
                                          clock=self._session_store.clock))
        image_region_collection = image_global_collection.collection_for_region(
            self._name)
        return image_region_collection

    def _keypair_collection_for_tenant(self, tenant_id):
        """
        Returns the keypairs for a region
        """
        tenant_session = self._session_store.session_for_tenant_id(tenant_id)
        kp_global_collection = tenant_session.data_for_api(
            "keypair_collection",
            lambda: GlobalKeyPairCollections(tenant_id=tenant_id,
                                             clock=self._session_store.clock))
        kp_region_collection = kp_global_collection.collection_for_region(
            self._name)
        return kp_region_collection

    app = MimicApp()

    @app.route('/v2/<string:tenant_id>/servers', methods=['POST'])
    def create_server(self, request, tenant_id):
        """
        Returns a generic create server response, with status 'ACTIVE'.
        """
        try:
            content = json.loads(request.content.read())
        except ValueError:
            return json.dumps(
                bad_request("Invalid JSON request body", request))

        try:
            creation = (self._region_collection_for_tenant(tenant_id)
                        .request_creation(request, content, self.url))
        except BadRequestError as e:
            return json.dumps(bad_request(e.nova_message, request))
        except LimitError as e:
            return json.dumps(forbidden(e.nova_message, request))

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
                name=request.args.get('name', [u""])[0],
                limit=request.args.get('limit', [None])[0],
                marker=request.args.get('marker', [None])[0]
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
                name=request.args.get('name', [u""])[0],
                limit=request.args.get('limit', [None])[0],
                marker=request.args.get('marker', [None])[0],
                changes_since=request.args.get('changes-since', [None])[0]
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
        return(self._image_collection_for_tenant(tenant_id)
               .get_image(request, image_id, absolutize_url=self.url))

    @app.route('/v2/<string:tenant_id>/images/detail', methods=['GET'])
    def get_server_image_list_with_details(self, request, tenant_id):
        """
        Returns a image list.
        """
        return (self._image_collection_for_tenant(tenant_id)
                .list_images(include_details=True, absolutize_url=self.url))

    @app.route('/v2/<string:tenant_id>/images', methods=['GET'])
    def get_server_image_list(self, request, tenant_id):
        """
        Returns a image list.
        """
        return(self._image_collection_for_tenant(tenant_id)
               .list_images(include_details=False, absolutize_url=self.url))

    @app.route('/v2/<string:tenant_id>/flavors/<string:flavor_id>', methods=['GET'])
    def get_flavor_details(self, request, tenant_id, flavor_id):
        """
        Returns a get flavor response, for any given flavorid
        """
        flavor_collection = GlobalFlavorCollection(tenant_id=tenant_id,
                                                   clock=self._session_store.clock)
        return (flavor_collection.collection_for_region(region_name=self._name)
                .get_flavor(request, flavor_id, absolutize_url=self.url))

    @app.route('/v2/<string:tenant_id>/flavors', methods=['GET'])
    def get_flavor_list(self, request, tenant_id):
        """
        Returns a list of flavor with the response code 200.
        docs: http://bit.ly/1eXTSDC
        TO DO: The length of flavor list can be set using the control plane.
               Also be able to set different flavor types in the future.
        """
        flavor_collection = GlobalFlavorCollection(tenant_id=tenant_id,
                                                   clock=self._session_store.clock)
        return (flavor_collection.collection_for_region(region_name=self._name)
                .list_flavors(include_details=False, absolutize_url=self.url))

    @app.route('/v2/<string:tenant_id>/flavors/detail', methods=['GET'])
    def get_flavor_list_with_details(self, request, tenant_id):
        """
        Returns a list of flavor details with the response code 200.
        TO DO: The length of flavor list can be set using the control plane.
               Also be able to set different flavor types in the future.
        """
        flavor_collection = GlobalFlavorCollection(tenant_id=tenant_id,
                                                   clock=self._session_store.clock)
        return (flavor_collection.collection_for_region(region_name=self._name)
                .list_flavors(include_details=True, absolutize_url=self.url))

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
            return json.dumps(not_found('Server does not exist', request))

        return ServerMetadata(server).app.resource()

    @app.route('/v2/<string:tenant_id>/servers/<string:server_id>/action', methods=['POST'])
    def perform_action(self, request, tenant_id, server_id):
        """
        Perform the requested action on the server
        """
        return self._region_collection_for_tenant(tenant_id).request_action(request, server_id, self.url)

    @app.route("/v2/<string:tenant_id>/os-keypairs", methods=['GET'])
    def get_key_pairs(self, request, tenant_id):
        """
        Returns current key pairs.
        http://docs.rackspace.com/servers/api/v2/cs-devguide/content/ListKeyPairs.html
        """
        return self._keypair_collection_for_tenant(tenant_id).json_list()

    @app.route("/v2/<string:tenant_id>/os-keypairs", methods=['POST'])
    def create_key_pair(self, request, tenant_id):
        """
        Returns a newly created key pair with the specified name.
        http://docs.rackspace.com/servers/api/v2/cs-devguide/content/UploadKeyPair.html
        """
        try:
            content = json.loads(request.content.read())
            keypair = content["keypair"]
            keypair_from_request = KeyPair(
                name=keypair["name"], public_key=keypair["public_key"])
        except (ValueError or KeyError):
            request.setResponseCode(400)
            return json.dumps(bad_request("Malformed request body", request))

        keypair_response = self._keypair_collection_for_tenant(
            tenant_id).create_keypair(keypair=keypair_from_request)
        return json.dumps(keypair_response)

    @app.route("/v2/<string:tenant_id>/os-keypairs/<string:keypairname>", methods=['DELETE'])
    def delete_key_pair(self, request, tenant_id, keypairname):
        """
        Removes a key by its name.
        http://docs.rackspace.com/servers/api/v2/cs-devguide/content/DeleteKeyPair.html
        """
        try:
            self._keypair_collection_for_tenant(
                tenant_id).remove_keypair(keypairname)
        except ValueError:
            request.setResponseCode(404)
            return json.dumps("KeyPair not found: " + keypairname)

        request.setResponseCode(202)


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
            return json.dumps(bad_request("Malformed request body", request))

        # more than one key is ok, non-"meta" keys are just ignored
        if 'metadata' not in content:
            return json.dumps(bad_request("Malformed request body", request))

        # When setting metadata, None is special for some reason
        if content['metadata'] is None:
            return json.dumps(bad_request(
                "Malformed request body. metadata must be object", request))

        try:
            Server.validate_metadata(content['metadata'])
        except BadRequestError as e:
            return json.dumps(bad_request(e.nova_message, request))
        except LimitError as e:
            return json.dumps(forbidden(e.nova_message, request))

        self._server.set_metadata(content['metadata'])
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
            return json.dumps(bad_request("Malformed request body", request))

        # more than one key is ok, non-"meta" keys are just ignored
        if 'meta' not in content or not isinstance(content['meta'], dict):
            return json.dumps(bad_request("Malformed request body", request))

        if len(content['meta']) > 1:
            return json.dumps(bad_request(
                "Request body contains too many items", request))

        if key not in content['meta']:
            return json.dumps(bad_request(
                "Request body and URI mismatch", request))

        try:
            self._server.set_metadata_item(key, content['meta'][key])
        except BadRequestError as e:
            return json.dumps(bad_request(e.nova_message, request))
        except LimitError as e:
            return json.dumps(forbidden(e.nova_message, request))

        # no matter how many keys were passed in, only the meta key is
        # returned
        return json.dumps({'meta': content['meta']})
