# -*- test-case-name: mimic.test.test_rackconnect_v3 -*-

"""
API mock for the Rackspace RackConnect v3 API, which is documented at:
http://http://docs.rcv3.apiary.io/
"""

from json import dumps
from uuid import uuid4, uuid5, NAMESPACE_URL

from characteristic import attributes, Attribute
from six import text_type

from twisted.plugin import IPlugin
from twisted.web.http import CREATED, ACCEPTED, OK
from twisted.web.resource import NoResource
from zope.interface import implementer

from mimic.catalog import Entry
from mimic.catalog import Endpoint
from mimic.imimic import IAPIMock
from mimic.rest.mimicapp import MimicApp
from mimic.util.helper import attribute_names, random_ipv4


lb_pool_attrs = [
    Attribute("id", default_factory=lambda: text_type(uuid4()),
              instance_of=str),
    Attribute("name", default_value="default", instance_of=str),
    Attribute("port", default_value=80, instance_of=int),
    Attribute("status", default_value="ACTIVE", instance_of=str),
    Attribute("status_detail", default_value=None),
    Attribute("virtual_ip", default_factory=random_ipv4, instance_of=str),
    Attribute('nodes', default_factory=list, instance_of=list)]


@attributes(lb_pool_attrs)
class LoadBalancerPool(object):
    """
    Represents a Load Balancer Pool, which cannot be created via the API.

    :param str id: The ID of the load balancer pool - is randomly generated
        if not provided
    :param str name: The name of the load balancer pool - defaults to
        'default'
    :param int port: The incoming port of the load balancer - defaults to 80
    :param str status: The status of the load balancer - defaults to "ACTIVE"
    :param str status_detail: Any details about the status - defaults to None
    :param list nodes: :class:`LoadBalancerPoolNode`s
    """
    def as_json(self):
        """
        Create a JSON-serializable representation of the contents of this
        object, which can be used in a REST response for a request for the
        details of this particular object
        """
        response = {attr: getattr(self, attr) for attr in
                    attribute_names(lb_pool_attrs) if attr != "nodes"}
        response['node_counts'] = {
            "cloud_servers": len(self.nodes),
            "external": 0,
            "total": len(self.nodes)
        }
        return response

    def node_by_cloud_server(self, cloud_server_id):
        """
        Find a node by it's cloud server ID.
        """
        return next((node for node in self.nodes
                     if node.cloud_server == cloud_server_id),
                    None)

    def node_by_id(self, node_id):
        """
        Find a node by it's node_id.
        """
        return next((node for node in self.nodes if node.id == node_id), None)



# XXX: External nodes are not currently supported in RackConnectV3
lb_node_attrs = [
    "created", "load_balancer_pool", "cloud_server",
    Attribute("id", default_factory=lambda: text_type(uuid4()),
              instance_of=str),
    Attribute("updated", default_value=None),
    Attribute("status", default_value="ACTIVE", instance_of=str),
    Attribute("status_detail", default_value=None)]


@attributes(lb_node_attrs)
class LoadBalancerPoolNode(object):
    """
    Represents a Load Balancer Pool Node.

    :param str id: The ID of the load balancer pool node - is randomly
        generated if not provided
    :param str created: The timestamp of when the load balancer node was
        created
    :param str updated: The timestamp of when the load balancer node was
        updated.  Can be None.
    :param load_balancer_pool: :class:`LoadBalancerPool` to which
        this node belongs
    :param str status: The status of the load balancer - defaults to "ACTIVE"
    :param str status_detail: Any details about the status - defaults to None
    :param str cloud_server: The ID of the cloud server corresponding to
        this node (not the same as the instance's ``id``).  Note - a node
        in theory can also be some external resource (not a cloud server),
        but that is not supported yet.
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
        response = {attr: getattr(self, attr) for attr in
                    attribute_names(lb_node_attrs)
                    if attr not in ('load_balancer_pool', 'cloud_server')}
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
