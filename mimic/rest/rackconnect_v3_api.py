# -*- test-case-name: mimic.test.test_rackconnect_v3 -*-

"""
API mock for the Rackspace RackConnect v3 API, which is documented at:
http://docs.rcv3.apiary.io/
"""
from collections import defaultdict
import json
from uuid import uuid4, UUID

from characteristic import attributes, Attribute
from six import text_type

from twisted.plugin import IPlugin
from twisted.web.http import NOT_FOUND, NOT_IMPLEMENTED
from zope.interface import implementer

from mimic.catalog import Entry
from mimic.catalog import Endpoint
from mimic.imimic import IAPIMock
from mimic.rest.mimicapp import MimicApp
from mimic.util.helper import random_ipv4, seconds_to_timestamp


timestamp_format = '%Y-%m-%dT%H:%M:%SZ'


@implementer(IAPIMock, IPlugin)
class RackConnectV3(object):
    """
    API mock object for RackConnect V3.

    :ivar regions: The regions for which endpoints should be produced
    :type regions: ``iterable``

    :ivar int default_pools: The number of default load balancers to be
        created per tenant per region
    """

    def __init__(self, regions=("ORD",), default_pools=1):
        """
        Construct a :class:`RackConnectV3` object.
        """
        self.regions = regions
        self.default_pools = default_pools

    def catalog_entries(self, tenant_id):
        """
        Catalog entry for RackConnect V3 endpoints.
        """
        return [
            Entry(tenant_id, "rax:rackconnect", "rackconnect", [
                Endpoint(tenant_id, region, text_type(uuid4()), prefix="v3")
                for region in self.regions
            ])
        ]

    def resource_for_region(self, region, uri_prefix, session_store):
        """
        Return an IResource implementing a public RackConnect V3 region
        endpoint.
        """
        return RackConnectV3Region(
            iapi=self,
            uri_prefix=uri_prefix,
            session_store=session_store,
            region_name=region,
            default_pools=self.default_pools).app.resource()


@attributes(
    [Attribute("id", default_factory=lambda: text_type(uuid4()),
               instance_of=text_type),
     Attribute("name", default_value=u"default", instance_of=text_type),
     Attribute("port", default_value=80, instance_of=int),
     Attribute("status", default_value=u"ACTIVE", instance_of=text_type),
     Attribute("status_detail", default_value=None),
     Attribute("virtual_ip", default_factory=random_ipv4,
               instance_of=text_type),
     Attribute('nodes', default_factory=list, instance_of=list)],
    apply_with_cmp=False)
class LoadBalancerPool(object):
    """
    Represents a RackConnecvt v3 Load Balancer Pool.

    Load balancer pools cannot be created via the API, they have to just
    already exist on the account.

    :param text_type id: The ID of the load balancer pool - is randomly
        generated if not provided
    :param text_type name: The name of the load balancer pool - defaults to
        'default'
    :param int port: The incoming port of the load balancer - defaults to 80
    :param text_type status: The status of the load balancer - defaults to
        "ACTIVE"
    :param text_type status_detail: Any details about the status - defaults
        to None
    :param text_type virtual_ip: The IP of the load balancer pool
    :param list nodes: :class:`LoadBalancerPoolNode`s
    """
    def as_json(self):
        """
        Create a JSON-serializable representation of the contents of this
        object, which can be used in a REST response for a request for the
        details of this particular object
        """
        # no dictionary comprehensions in py2.6
        response = dict([
            (attr.name, getattr(self, attr.name))
            for attr in LoadBalancerPool.characteristic_attributes
            if attr.name != "nodes"])
        response['node_counts'] = {
            "cloud_servers": len(self.nodes),
            "external": 0,
            "total": len(self.nodes)
        }
        return response

    def node_by_cloud_server(self, cloud_server_id):
        """
        Find a node by its cloud server ID.

        :return: a :class:`LoadBalancerPoolNode` with a server id matching
            the given cloud server, or `None` if none are found
        """
        return next((node for node in self.nodes
                     if node.cloud_server == cloud_server_id),
                    None)

    def node_by_id(self, node_id):
        """
        Find a node by its node_id.

        :return: a :class:`LoadBalancerPoolNode` with the given node id,
            or `None` if none are found
        """
        return next((node for node in self.nodes if node.id == node_id), None)


@attributes(["created", "load_balancer_pool", "cloud_server",
             Attribute("id", default_factory=lambda: text_type(uuid4()),
                       instance_of=text_type),
             Attribute("updated", default_value=None),
             Attribute("status", default_value=text_type("ACTIVE"),
                       instance_of=text_type),
             Attribute("status_detail", default_value=None)])
class LoadBalancerPoolNode(object):
    """
    Represents a Load Balancer Pool Node.

    A load currently only corresponds to a particular cloud server.
    External nodes are not currently supported in RackConnectV3

    :param text_type id: The ID of the load balancer pool node - is randomly
        generated if not provided
    :param text_type created: The timestamp of when the load balancer node was
        created
    :param text_type updated: The timestamp of when the load balancer node was
        updated.  Can be None.
    :param load_balancer_pool: :class:`LoadBalancerPool` to which
        this node belongs
    :param text_type status: The status of the load balancer - defaults to
        "ACTIVE"
    :param text_type status_detail: Any details about the status - defaults
        to None
    :param text_type cloud_server: The ID of the cloud server corresponding to
        this node.  The cloud server's ID is not equivalent to the ``id``
        attribute on :class:`LoadBalancerPoolNode`, because a node
        in theory can also be some external (not a cloud server) resource,
        but that is not supported yet on the API.
    """
    def short_json(self):
        """
        Create a short JSON-serializable representation of the contents of
        this object (not detailed), which can be used in a REST response.

        Should match the JSON documented in the response for
        POST /v3/{tenant_id}/load_balancer_pools/{load_balancer_pool_id}/nodes
        (add load balancer pool node) or as part of the response for
        GET /v3/{tenant_id}/load_balancer_pools/{load_balancer_pool_id}/nodes
        (list load balancer pool nodes)
        """
        # no dictionary comprehensions in py2.6
        response = dict([
            (attr.name, getattr(self, attr.name))
            for attr in LoadBalancerPoolNode.characteristic_attributes
            if attr.name not in ('load_balancer_pool', 'cloud_server')])
        response['load_balancer_pool'] = {'id': self.load_balancer_pool.id}
        response['cloud_server'] = {'id': self.cloud_server}
        return response

    def update(self, now, status, status_detail=None):
        """
        Changes the status of the node.
        """
        self.updated = now
        self.status = status
        self.status_detail = status_detail


@attributes(["iapi", "uri_prefix", "session_store", "region_name",
             "default_pools"])
class RackConnectV3Region(object):
    """
    A set of ``klein`` routes representing a RackConnect V3 endpoint.
    """
    app = MimicApp()

    @app.route("/v3/<string:tenant_id>/load_balancer_pools", branch=True)
    def get_tenant_lb_pools(self, request, tenant_id):
        """
        Get a resource for a tenant's load balancer pools in this region.
        """
        tenant_store = self.session_store.session_for_tenant_id(tenant_id)
        per_tenant_lbs = tenant_store.data_for_api(
            self.iapi, lambda: defaultdict(list))
        per_tenant_per_region_lbs = per_tenant_lbs[self.region_name]

        if not per_tenant_per_region_lbs:
            per_tenant_per_region_lbs.extend([
                LoadBalancerPool() for _ in range(self.default_pools)])

        handler = LoadBalancerPoolsInRegion(lbpools=per_tenant_per_region_lbs,
                                            clock=self.session_store.clock)
        return handler.app.resource()


# exclude all the attributes from comparison so that equality has to be
# determined by identity, since lbpools is mutable and we don't want to
# compare clocks
@attributes(["lbpools", "clock"], apply_with_cmp=False)
class LoadBalancerPoolsInRegion(object):
    """
    A set of ``klein`` routes handling RackConnect V3 Load Balancer Pools
    collections.
    """
    app = MimicApp()

    def _pool_by_id(self, id):
        """
        Get a pool by the ID of the pool.
        """
        return next((pool for pool in self.lbpools if pool.id == id), None)

    @app.route("/", methods=["GET"])
    def list_all_load_balancer_pools(self, request):
        """
        API call to list all load balancer pools for the tenant and region
        correspoding to this handler.  Returns 200 always.

        http://docs.rcv3.apiary.io/#get-%2Fv3%2F%7Btenant_id%7D%2Fload_balancer_pools
        """
        return json.dumps([pool.as_json() for pool in self.lbpools])

    @app.route("/nodes", methods=["POST"])
    def bulk_add_nodes_to_load_balancer_pools(self, request):
        """
        Add multiple nodes to multiple load balancer pools.

        Returns a 400 if the lb pool_id is not a uuid.
        Returns a 409 if the lb pool_id does not exist or the cloud server already exists
        on the lb pool.

        http://docs.rcv3.apiary.io/#post-%2Fv3%2F%7Btenant_id%7D%2Fload_balancer_pools%2Fnodes

        TODO: blow up with a 500 and verify if the given server exists in nova.
        """
        body = json.loads(request.content.read())
        added_nodes = []
        error_response = {"errors": []}

        for each in body:
            pool_id = each['load_balancer_pool']['id']
            try:
                UUID(pool_id, version=4)
            except (ValueError, AttributeError):
                request.setResponseCode(400)
                return json.dumps('The input was not in the correct format. Please reference '
                                  'the documentation at http://docs.rcv3.apiary.io for '
                                  'further assistance.')
            pool = self._pool_by_id(pool_id)
            if pool is None:
                response_code = 409
                error_response["errors"].append("Load Balancer Pool {0} does "
                                                "not exist".format(pool_id))
            elif pool.node_by_cloud_server(each['cloud_server']['id']):
                response_code = 409
                error_response["errors"].append("Cloud Server {0} is already a "
                                                "member of Load Balancer Pool "
                                                "{1}".format(each['cloud_server']['id'],
                                                             pool_id))
        if not error_response['errors']:
            for add in body:
                node = LoadBalancerPoolNode(
                    created=seconds_to_timestamp(self.clock.seconds(),
                                                 timestamp_format),
                    load_balancer_pool=pool,
                    cloud_server=add['cloud_server']['id'])

                pool.nodes.append(node)
                added_nodes.append(node)
                response_code = 201

        request.setResponseCode(response_code)
        if response_code == 201:
            return json.dumps([n.short_json() for n in added_nodes])
        else:
            return json.dumps(error_response)

    @app.route("/nodes", methods=["DELETE"])
    def bulk_delete_nodes_to_load_balancer_pools(self, request):
        """
        Delete multiple nodes from multiple load balancer pools.

        Returns a 400 if the lb pool_id is not a uuid.
        Returns a 409 if the lb pool_id does not exist or the cloud server does not exist
        on the lb pool.

        http://docs.rcv3.apiary.io/#delete-%2Fv3%2F%7Btenant_id%7D%2Fload_balancer_pools%2Fnodes

        TODO: For now, blow up with a 500 and verify if the given server exists in nova.
        """
        body = json.loads(request.content.read())
        error_response = {"errors": []}

        for each in body:
            pool_id = each['load_balancer_pool']['id']
            try:
                UUID(pool_id, version=4)
            except (ValueError, AttributeError):
                request.setResponseCode(400)
                return json.dumps('The input was not in the correct format. Please reference '
                                  'the documentation at http://docs.rcv3.apiary.io for '
                                  'further assistance.')
            pool = self._pool_by_id(pool_id)

            if pool is None:
                response_code = 409
                error_response["errors"].append("Load Balancer Pool {0} does "
                                                "not exist".format(pool_id))
            elif pool.node_by_cloud_server(each['cloud_server']['id']) is None:
                response_code = 409
                error_response["errors"].append(("Cloud Server {0} is not a "
                                                 "member of Load Balancer Pool "
                                                 "{1}").format(each['cloud_server']['id'],
                                                               pool_id))
        if not error_response['errors']:
            for add in body:
                pool = self._pool_by_id(add['load_balancer_pool']['id'])
                node = pool.node_by_cloud_server(add['cloud_server']['id'])
                pool.nodes.remove(node)
                response_code = 204

        request.setResponseCode(response_code)
        if response_code == 204:
            return b""
        else:
            return json.dumps(error_response)

    @app.route("/<string:id>", branch=True)
    def delegate_to_one_pool_handler(self, request, id):
        """
        If the load balancer pool of the given ID exists, delgate to the
        :class:`OneLoadBalancerPool` handler for further requests.

        Returns 400 is the pool_id is not a uuid
        Returns 404 if no pool with the ID exists.
        """
        try:
            UUID(id, version=4)
        except (ValueError, AttributeError):
            request.setResponseCode(400)
            return ('The input was not in the correct format. Please reference '
                    'the documentation at http://docs.rcv3.apiary.io for further assistance.')
        pool = self._pool_by_id(id)
        if pool is not None:
            handler = OneLoadBalancerPool(pool=pool)
            app = handler.app
            resource = app.resource()
            return resource

        # TODO: what is the error message if any?  It is undocumented.
        # guess based on Remove Load Balancer Pool Node documentation
        request.setResponseCode(NOT_FOUND)
        return "Load Balancer Pool {0} does not exist".format(id)


@attributes(["pool"])
class OneLoadBalancerPool(object):
    """
    A set of ``klein`` routes handling the RackConnect V3 API for a single
    load balancer pool
    """
    app = MimicApp()

    @app.route("/", methods=["GET"])
    def get_pool_information(self, request):
        """
        API call to get the details of the single load balancer pool
        corresponding to this handler.

        Returns a 200 because the pool definitely exists by the time this
        handler is invoked.

        http://docs.rcv3.apiary.io/#get-%2Fv3%2F%7Btenant_id%7D%2Fload_balancer_pools%2F%7Bid%7D
        """
        return json.dumps(self.pool.as_json())

    @app.route("/nodes", methods=["GET"])
    def get_node_collection_information(self, request):
        """
        List all the nodes for the load balancer pool.

        Returns a 200 always.

        http://docs.rcv3.apiary.io/#get-%2Fv3%2F%7Btenant_id%7D%2Fload_balancer_pools%2F%7Bload_balancer_pool_id%7D%2Fnodes
        """
        return json.dumps([node.short_json() for node in self.pool.nodes])

    @app.route("/nodes/details", methods=["GET"])
    def get_node_collection_details_information(self, request):
        """
        Get detailed information about all the nodes, including the cloud
        server network information.  This is unimplemented as it might
        need to be hooked up to the nova api.

        http://docs.rcv3.apiary.io/#get-%2Fv3%2F%7Btenant_id%7D%2Fload_balancer_pools%2F%7Bload_balancer_pool_id%7D%2Fnodes%2Fdetails
        """
        request.setResponseCode(NOT_IMPLEMENTED)

    @app.route("/nodes", methods=["POST"])
    def add_single_pool_node(self, request):
        """
        Add a single pool node to the load balancer pool is not implemented
        yet.

        http://docs.rcv3.apiary.io/#post-%2Fv3%2F%7Btenant_id%7D%2Fload_balancer_pools%2F%7Bload_balancer_pool_id%7D%2Fnodes
        """
        request.setResponseCode(NOT_IMPLEMENTED)

    @app.route("/nodes/<string:node_id>", branch=True)
    def handle_single_node_requests(self, request, node_id):
        """
        Catchall to specify that single node operations (GET, DELETE,
        GET details) are not implemented yet
        """
        request.setResponseCode(NOT_IMPLEMENTED)
