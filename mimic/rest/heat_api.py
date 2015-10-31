# -*- test-case-name: mimic.test.test_heat -*-
"""
Defines Cloud Orchestration endpoints.
"""
import json
from six import text_type
from uuid import uuid4

from zope.interface import implementer

from twisted.plugin import IPlugin

from twisted.python.urlpath import URLPath

from mimic.catalog import Entry
from mimic.catalog import Endpoint
from mimic.imimic import IAPIMock
from mimic.model.heat_objects import GlobalStackCollections
from mimic.rest.mimicapp import MimicApp
from mimic.util.helper import json_from_request


@implementer(IAPIMock, IPlugin)
class HeatApi(object):
    """
    API mock for Heat.
    """

    def __init__(self, regions=["ORD"]):
        """
        Create a HeatApi.
        """
        self._regions = regions

    def catalog_entries(self, tenant_id):
        """
        Catalog entry for Heat endpoints.
        """
        return [
            Entry(tenant_id, "orchestration", "cloudOrchestration",
                  [
                      Endpoint(tenant_id, region, text_type(uuid4()),
                               prefix="v1")
                      for region in self._regions
                  ])
        ]

    def resource_for_region(self, region, uri_prefix, session_store):
        """
        Get an :obj:`twisted.web.iweb.IResource` for the given URI prefix;
        implement :obj:`IAPIMock`.
        """
        return (HeatRegion(api_mock=self, uri_prefix=uri_prefix,
                           region_name=region, session_store=session_store)
                .app.resource())

    def _get_session(self, session_store, tenant_id):
        """
        Retrieve or create a new Heat session from a given tenant identifier
        and :obj:`SessionStore`.

        For use with ``data_for_api``.

        Temporary hack; see this issue
        https://github.com/rackerlabs/mimic/issues/158
        """
        session = session_store.session_for_tenant_id(tenant_id)
        return session.data_for_api(self, lambda: GlobalStackCollections(
            tenant_id=tenant_id,
        ))


class HeatRegion(object):
    """
    Rest endpoints for mocked Heat API.
    """

    def __init__(self, api_mock, uri_prefix, region_name, session_store):
        """
        Create a HeatRegion.
        """
        self._api_mock = api_mock
        self._region_name = region_name
        self._session_store = session_store
        self.uri_prefix = uri_prefix

    def _region_collection_for_tenant(self, tenant_id):
        """
        Retrieves the RegionalStackCollection for a tenant.
        """
        return (self._api_mock._get_session(self._session_store, tenant_id)
                .collection_for_region(self._region_name))

    def url(self, suffix):
        """
        Generate a URL to an object within the Heat URL hierarchy, given the
        part of the URL that comes after.
        """
        return str(URLPath.fromString(self.uri_prefix)
                   .child(suffix.encode("utf-8")))

    app = MimicApp()

    @app.route('/v1/<string:tenant_id>/stacks', methods=['POST'])
    def create_stack(self, request, tenant_id):
        """
        Creates a stack.
        See http://api.rackspace.com/api-ref-orchestration.html#stack_create
        """
        region_collection = self._region_collection_for_tenant(tenant_id)
        content = json_from_request(request)
        return region_collection.request_creation(request, content,
                                                  absolutize_url=self.url)

    @app.route('/v1/<string:tenant_id>/stacks', methods=['GET'])
    def list_stacks(self, request, tenant_id):
        """
        Lists stacks. Supports inclusion of query parameters.
        See http://api.rackspace.com/api-ref-orchestration.html#stack_list
        """
        def extract_show_deleted():
            """
            Extracts boolean flag for showing deleted stacks from query string.
            """
            show_deleted = request.args.get(b'show_deleted', [b"False"])[0]
            return show_deleted.lower() == b'true'

        def extract_tags():
            """
            Extracts tags from request's query string.
            """
            tags = request.args.get(b'tags', [None])[0]
            return [tag.decode("utf-8")
                    for tag in (tags.split(b',') if tags else [])]

        return self._region_collection_for_tenant(tenant_id).request_list(
            show_deleted=extract_show_deleted(),
            tags=extract_tags(),
            absolutize_url=self.url)

    @app.route(
        '/v1/<string:tenant_id>/stacks/<string:stack_name>/<string:stack_id>',
        methods=['DELETE'])
    def delete_stack(self, request, tenant_id, stack_name, stack_id):
        """
        Deletes a stack.
        See http://api.rackspace.com/api-ref-orchestration.html#stack_delete
        """
        region_collection = self._region_collection_for_tenant(tenant_id)
        return region_collection.request_deletion(request, stack_name, stack_id)

    @app.route('/v1/<string:tenant_id>/validate', methods=['POST'])
    def validate_template(self, request, tenant_id):
        """
        Validates a template.
        See http://api.rackspace.com/api-ref-orchestration.html#template_validate
        """
        content = json_from_request(request)

        if 'template' in content or 'template_url' in content:
            request.setResponseCode(200)
            response = json.dumps({"Parameters": "parameters would go here"})
        else:
            request.setResponseCode(400)
            response = ("Bad request! template or template_url should be in "
                        "the request.")

        return response
