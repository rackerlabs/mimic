
from json import dumps

from twisted.trial.unittest import SynchronousTestCase
from twisted.internet.task import Clock

import treq

from mimic.rest.swift_api import SwiftMock
from mimic.resource import MimicRoot
from mimic.core import MimicCore
from mimic.rest.swift_api import normal_tenant_id_to_crazy_mosso_id
from mimic.test.helpers import request


class SwiftTests(SynchronousTestCase):
    """
    tests for swift API
    """

    def setUp(self):
        """
        Set up to create the requests
        """
        self.core = MimicCore(Clock(), [SwiftMock()])
        self.root = MimicRoot(self.core).app.resource()
        self.response = request(
            self, self.root, "POST", "/identity/v2.0/tokens",
            dumps({
                "auth": {
                    "passwordCredentials": {
                        "username": "test1",
                        "password": "test1password",
                    },
                    # TODO: should this really be 'tenantId'?
                    "tenantName": "fun_tenant",
                }
            })
        )
        self.auth_response = self.successResultOf(self.response)
        self.json_body = self.successResultOf(
            treq.json_content(self.auth_response))

    def test_service_catalog(self):
        """
        When provided with a :obj:`SwiftMock`, :obj:`MimicCore` yields a
        service catalog containing a swift endpoint.
        """
        self.assertEqual(self.auth_response.code, 200)
        self.assertTrue(self.json_body)
        sample_entry = self.json_body['access']['serviceCatalog'][0]
        self.assertEqual(sample_entry['type'], u'object-store')
        sample_endpoint = sample_entry['endpoints'][0]
        self.assertEqual(
            sample_endpoint['tenantId'],
            normal_tenant_id_to_crazy_mosso_id("fun_tenant")
        )
        self.assertEqual(sample_endpoint['region'], 'ORD')
        self.assertEqual(len(self.json_body['access']['serviceCatalog']), 1)

    def test_create_container(self):
        """
        Test to verify create container using :obj:`SwiftMock`
        """
        uri = (self.json_body['access']['serviceCatalog'][0]['endpoints'][0]
               ['publicURL'] + '/testcontainer')
        create_container = request(self, self.root, "PUT", uri)
        create_container_response = self.successResultOf(create_container)
        self.assertEqual(create_container_response.code, 201)
        self.assertEqual(
            self.successResultOf(treq.content(create_container_response)),
            b"",
        )
