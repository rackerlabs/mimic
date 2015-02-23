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
from mimic.model.nova_objects import GlobalServerCollections
from mimic.model.nova_behaviors import server_creation
from mimic.model.nova_behaviors import criteria_collection_from_request_criteria
from mimic.model.nova_behaviors import nova_criterion_factories
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
    Klien resources for the Nova Control plane API
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
        request.setResponseCode(CREATED)
        global_collection = self.api_mock.nova_api._get_session(
            self.session_store, tenant_id)
        behavior_description = json.loads(request.content.read())
        behavior = server_creation.create_behavior(
            behavior_description['name'], behavior_description['parameters'])
        criteria = criteria_collection_from_request_criteria(
            behavior_description['criteria'], nova_criterion_factories)
        region_collection = global_collection.collection_for_region(
            self.region)
        region_collection.register_creation_behavior_for_criteria(
            behavior, criteria
        )
        return b''


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
            return json.dumps(invalid_resource("Invalid JSON request body"))

        try:
            creation = (self._region_collection_for_tenant(tenant_id)
                        .request_creation(request, content, self.url))
        except ValueError:
            request.setResponseCode(400)
            return json.dumps(
                bad_request(
                    "OS-DCF:diskConfig must be either 'MANUAL' or 'AUTO'."))

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
