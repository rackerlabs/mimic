# -*- test-case-name: mimic.test.test_loadbalancer -*-
"""
Defines add node and delete node from load balancers
"""
import json
from uuid import uuid4
from six import text_type
from zope.interface import implementer
from twisted.web.server import Request
from twisted.plugin import IPlugin
from mimic.canned_responses.loadbalancer import del_load_balancer
from mimic.rest.mimicapp import MimicApp
from mimic.imimic import IAPIMock
from mimic.catalog import Entry
from mimic.catalog import Endpoint

from mimic.model.clb_objects import GlobalCLBCollections
from random import randrange

from mimic.util.helper import invalid_resource, json_dump
from characteristic import attributes


Request.defaultContentType = 'application/json'


@implementer(IAPIMock, IPlugin)
class LoadBalancerApi(object):
    """
    This class registers the load balancer API in the service catalog.
    It does NOT implement individual endpoints.
    """
    def __init__(self, regions=["ORD"]):
        """
        Create an API with the specified regions.
        """
        self._regions = regions
        self.session_store = None

    def catalog_entries(self, tenant_id):
        """
        Cloud load balancer entries.
        """
        return [
            Entry(tenant_id, "rax:load-balancer", "cloudLoadBalancers",
                  [
                      Endpoint(tenant_id, region, text_type(uuid4()),
                               prefix="v2")
                      for region in self._regions
                  ])
        ]

    def resource_for_region(self, region, uri_prefix, session_store):
        """
        Get an :obj:`twisted.web.iweb.IResource` for the given URI prefix;
        implement :obj:`IAPIMock`.
        """
        self.session_store = session_store
        lb_region = LoadBalancerRegion(self, uri_prefix, session_store,
                                       region)
        return lb_region.app.resource()

    def _get_session(self, session_store, tenant_id):
        """
        Retrieve or create a new LoadBalancer session from a given tenant identifier
        and :obj:`SessionStore`.

        For use with ``data_for_api``.

        Temporary hack; see this issue
        https://github.com/rackerlabs/mimic/issues/158
        """
        return (
            session_store.session_for_tenant_id(tenant_id)
            .data_for_api(self, lambda: GlobalCLBCollections(
                tenant_id=tenant_id,
                clock=session_store.clock
            ))
        )


@implementer(IAPIMock, IPlugin)
@attributes(["lb_api"])
class LoadBalancerControlApi(object):
    """
    This class registers the load balancer controller API in the service
    catalog.  It does NOT implement individual endpoints.
    """
    def catalog_entries(self, tenant_id):
        """
        Cloud load balancer controller endpoints.
        """
        return [
            Entry(
                tenant_id, "rax:load-balancer", "cloudLoadBalancerControl",
                [
                    Endpoint(tenant_id, region, text_type(uuid4()), prefix="v2")
                    for region in self.lb_api._regions
                ]
            )
        ]

    def resource_for_region(self, region, uri_prefix, session_store):
        """
        Get an :obj:`twisted.web.iweb.IResource` for the given URI prefix;
        implement :obj:`IAPIMock`.
        """
        lbc_region = LoadBalancerControlRegion(api_mock=self, uri_prefix=uri_prefix,
                                               session_store=self.lb_api.session_store, region=region)
        return lbc_region.app.resource()


@attributes(["api_mock", "uri_prefix", "session_store", "region"])
class LoadBalancerControlRegion(object):
    """
    Klein routes for load balancer's control API within a particular region.
    """

    app = MimicApp()

    def session(self, tenant_id):
        """
        Gets a session for a particular tenant, creating one if there isn't
        one.
        """
        tenant_session = self._session_store.session_for_tenant_id(tenant_id)
        clb_global_collection = tenant_session.data_for_api(
            self._api_mock,
            lambda: GlobalCLBCollections(
                tenant_id=tenant_id,
                clock=self._session_store.clock))
        clb_region_collection = clb_global_collection.collection_for_region(
            self.region_name)
        return clb_region_collection

    def _collection_from_tenant(self, tenant_id):
        """
        Retrieve the server collection for this region for the given tenant.
        """
        return (self.api_mock.lb_api._get_session(self.session_store, tenant_id)
                .collection_for_region(self.region))

    @app.route('/v2/<string:tenant_id>/loadbalancer/<int:clb_id>/setAttr', methods=['POST'])
    def set_attributes(self, request, tenant_id, clb_id):
        """
        Alters the supported attributes of the CLB to supported values.  To
        return things back to normal, you'll first need to list the CLB to get
        any original values yourself.
        """
        regional_lbs = self._collection_from_tenant(tenant_id)
        if clb_id not in regional_lbs:
            request.setResponseCode(404)
            return json.dumps({
                "message": "Tenant {} doesn't own load balancer {}".format(
                    tenant_id, clb_id
                ),
                "code": 404,
            })

        try:
            content = json.loads(request.content.read())
        except ValueError:
            request.setResponseCode(400)
            return json.dumps(invalid_resource("Invalid JSON request body"))

        if "status" in content:
            if content["status"] not in [
                "ACTIVE", "ERROR", "PENDING_DELETE", "PENDING_UPDATE"
            ]:
                request.setResponseCode(400)
                return json.dumps({
                    "message": "Invalid status.",
                    "code": 400,
                })

        regional_lbs.set_attributes(clb_id, content)
        request.setResponseCode(204)
        return b''


class LoadBalancerRegion(object):
    """
    Klein routes for load balancer API methods within a particular region.
    """

    app = MimicApp()

    def __init__(self, api_mock, uri_prefix, session_store, region_name):
        """
        Fetches the load balancer id for a failure, invalid scenarios and
        the count on the number of time 422 should be returned on add node.
        """
        self.uri_prefix = uri_prefix
        self.region_name = region_name
        self._api_mock = api_mock
        self._session_store = session_store

    def session(self, tenant_id):
        """
        Gets a session for a particular tenant, creating one if there isn't
        one.
        """
        tenant_session = self._session_store.session_for_tenant_id(tenant_id)
        clb_global_collection = tenant_session.data_for_api(
            self._api_mock,
            lambda: GlobalCLBCollections(
                tenant_id=tenant_id,
                clock=self._session_store.clock))
        clb_region_collection = clb_global_collection.collection_for_region(
            self.region_name)
        return clb_region_collection

    @app.route('/v2/<string:tenant_id>/loadbalancers', methods=['POST'])
    def add_load_balancer(self, request, tenant_id):
        """
        Creates a load balancer and adds it to the load balancer store.
        Returns the newly created load balancer with response code 202
        """
        try:
            content = json.loads(request.content.read())
        except ValueError:
            request.setResponseCode(400)
            return json.dumps(invalid_resource("Invalid JSON request body"))

        lb_id = randrange(99999)
        response_data = self.session(tenant_id).add_load_balancer(
            tenant_id, content['loadBalancer'], lb_id,
            self._session_store.clock.seconds()
        )
        request.setResponseCode(response_data[1])
        return json.dumps(response_data[0])

    @app.route('/v2/<string:tenant_id>/loadbalancers/<int:lb_id>', methods=['GET'])
    def get_load_balancers(self, request, tenant_id, lb_id):
        """
        Returns a list of all load balancers created using mimic with response code 200
        """
        response_data = self.session(tenant_id).get_load_balancers(
            lb_id,
            self._session_store.clock.seconds()
        )
        request.setResponseCode(response_data[1])
        return json.dumps(response_data[0])

    @app.route('/v2/<string:tenant_id>/loadbalancers', methods=['GET'])
    def list_load_balancers(self, request, tenant_id):
        """
        Returns a list of all load balancers created using mimic with response code 200
        """
        response_data = self.session(tenant_id).list_load_balancers(
            tenant_id,
            self._session_store.clock.seconds()
        )
        request.setResponseCode(response_data[1])
        return json.dumps(response_data[0])

    @app.route('/v2/<string:tenant_id>/loadbalancers/<int:lb_id>', methods=['DELETE'])
    def delete_load_balancer(self, request, tenant_id, lb_id):
        """
        Creates a load balancer and adds it to the load balancer store.
        Returns the newly created load balancer with response code 200
        """
        response_data = del_load_balancer(
            self.session(tenant_id),
            lb_id, self._session_store.clock.seconds()
        )
        request.setResponseCode(response_data[1])
        return json_dump(response_data[0])

    @app.route('/v2/<string:tenant_id>/loadbalancers/<int:lb_id>/nodes', methods=['POST'])
    def add_node_to_load_balancer(self, request, tenant_id, lb_id):
        """
        Return a successful add node response with code 200
        """
        try:
            content = json.loads(request.content.read())
        except ValueError:
            request.setResponseCode(400)
            return json.dumps(invalid_resource("Invalid JSON request body"))

        node_list = content['nodes']
        response_data = self.session(tenant_id).add_node(
            node_list, lb_id,
            self._session_store.clock.seconds()
        )
        request.setResponseCode(response_data[1])
        return json.dumps(response_data[0])

    @app.route('/v2/<string:tenant_id>/loadbalancers/<int:lb_id>/nodes/<int:node_id>',
               methods=['GET'])
    def get_nodes(self, request, tenant_id, lb_id, node_id):
        """
        Returns a 200 response code and list of nodes on the load balancer
        """
        response_data = self.session(tenant_id).get_nodes(
            lb_id, node_id,
            self._session_store.clock.seconds()
        )
        request.setResponseCode(response_data[1])
        return json.dumps(response_data[0])

    @app.route('/v2/<string:tenant_id>/loadbalancers/<int:lb_id>/nodes/<int:node_id>',
               methods=['DELETE'])
    def delete_node_from_load_balancer(self, request, tenant_id, lb_id, node_id):
        """
        Returns a 204 response code, for any load balancer created using the mocks
        """
        response_data = self.session(tenant_id).delete_node(
            lb_id, node_id,
            self._session_store.clock.seconds()
        )
        request.setResponseCode(response_data[1])
        return json.dumps(response_data[0])

    @app.route('/v2/<string:tenant_id>/loadbalancers/<int:lb_id>/nodes',
               methods=['DELETE'])
    def delete_nodes_from_load_balancer(self, request, tenant_id, lb_id):
        """
        Deletes multiple nodes from a LB.
        """
        node_ids = map(int, request.args.get('id', []))
        response_data = self.session(tenant_id).delete_nodes(
            lb_id, node_ids,
            self._session_store.clock.seconds())
        request.setResponseCode(response_data[1])
        return json_dump(response_data[0])

    @app.route('/v2/<string:tenant_id>/loadbalancers/<int:lb_id>/nodes',
               methods=['GET'])
    def list_nodes_for_load_balancer(self, request, tenant_id, lb_id):
        """
        Returns a 200 response code and list of nodes on the load balancer
        """
        response_data = self.session(tenant_id).list_nodes(
            lb_id,
            self._session_store.clock.seconds())
        request.setResponseCode(response_data[1])
        return json.dumps(response_data[0])
