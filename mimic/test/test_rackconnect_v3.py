"""
Unit tests for the Rackspace RackConnect V3 API.
"""

import json
import treq

from twisted.trial.unittest import SynchronousTestCase
from mimic.test.fixtures import APIMockHelper
from mimic.rest.rackconnect_v3_api import (
    LoadBalancerPool, LoadBalancerPoolNode)
from mimic.test.helpers import request


class LoadBalancerObjectTests(SynchronousTestCase):
    """
    Tests for :class:`LoadBalancerPool` and :class:`LoadBalancerPoolNode`
    """
    def setUp(self):
        self.pool = LoadBalancerPool(id="pool_id", virtual_ip="10.0.0.1")
        for i in range(10):
            self.pool.nodes.append(
                LoadBalancerPoolNode(id="node_{0}".format(i),
                                     created="2000-01-01T00:00:00Z",
                                     load_balancer_pool=self.pool,
                                     updated=None,
                                     cloud_server="server_{0}".format(i)))

    def test_LBPoolNode_short_json(self):
        """
        Valid JSON response (as would be displayed when listing nodes) is
        produced by :func:`LoadBalancerPoolNode.short_json`
        """
        self.assertEqual(
            {
                "id": "node_0",
                "created": "2000-01-01T00:00:00Z",
                "updated": None,
                "load_balancer_pool": {
                    "id": "pool_id"
                },
                "cloud_server": {
                    "id": "server_0"
                },
                "status": "ACTIVE",
                "status_detail": None
            },
            self.pool.nodes[0].short_json())

    def test_LBPool_short_json(self):
        """
        Valid JSON response (as would be displayed when listing pools or
        getting pool details) is produced by :func:`LoadBalancerPool.as_json`.
        """
        self.assertEqual(
            {
                "id": "pool_id",
                "name": "default",
                "node_counts": {
                    "cloud_servers": 10,
                    "external": 0,
                    "total": 10
                },
                "port": 80,
                "virtual_ip": "10.0.0.1",
                "status": "ACTIVE",
                "status_detail": None
            },
            self.pool.as_json())

    def test_LBPool_find_nodes_by_id(self):
        """
        A node can be retrieved by its ID.
        """
        self.assertIs(self.pool.nodes[5], self.pool.node_by_id("node_5"))

    def test_LBPool_find_nodes_by_server_id(self):
        """
        A node can be retrieved by its cloud server ID.
        """
        self.assertIs(self.pool.nodes[3],
                      self.pool.node_by_cloud_server("server_3"))

