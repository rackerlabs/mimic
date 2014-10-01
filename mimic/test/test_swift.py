
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

    def createSwiftService(self, rackspace_flavor=True):
        """
        Set up to create the requests
        """
        self.core = MimicCore(Clock(), [SwiftMock(rackspace_flavor)])
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
        self.createSwiftService()
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

    def create_one_container(self, expected_code):
        """
        Create one container and assert its code is the given expected status.
        """
        uri = (self.json_body['access']['serviceCatalog'][0]['endpoints'][0]
               ['publicURL'] + '/testcontainer')
        create_container = request(self, self.root, "PUT", uri)
        create_container_response = self.successResultOf(create_container)
        self.assertEqual(create_container_response.code, expected_code)
        self.assertEqual(
            self.successResultOf(treq.content(create_container_response)),
            b"",
        )

    def test_create_container(self):
        """
        Test to verify create container using :obj:`SwiftMock`
        """
        self.createSwiftService()
        self.create_one_container(201)

    def test_create_twice(self):
        """
        Creating a container twice results in an ACCEPTED status code.
        """
        self.createSwiftService()
        self.create_one_container(201)
        self.create_one_container(202)
        self.create_one_container(202)

    def test_get_container(self):
        """
        Creating a container and immediately retrieving it yields an empty list
        (since there are no objects) and several headers indicating that no
        objects are in the container and they consume no space.
        """
        self.createSwiftService()
        # create a container
        uri = (self.json_body['access']['serviceCatalog'][0]['endpoints'][0]
               ['publicURL'] + '/testcontainer')
        create_container = request(self, self.root, "PUT", uri)
        self.successResultOf(create_container)
        container_response = self.successResultOf(
            request(self, self.root, "GET", uri)
        )
        self.assertEqual(container_response.code, 200)
        container_contents = self.successResultOf(
            treq.json_content(container_response)
        )
        self.assertEqual(container_contents, [])
        self.assertEqual(
            container_response.headers.getRawHeaders(
                "X-Container-Object-Count")[0], "0"
        )
        self.assertEqual(
            container_response.headers.getRawHeaders(
                "X-Container-Bytes-Used")[0], "0"
        )

    def test_get_no_container(self):
        """
        GETing a container that has not been created results in a 404.
        """
        self.createSwiftService()
        # create a container
        uri = (self.json_body['access']['serviceCatalog'][0]['endpoints'][0]
               ['publicURL'] + '/testcontainer')
        container_response = self.successResultOf(
            request(self, self.root, "GET", uri)
        )
        self.assertEqual(container_response.code, 404)
        self.assertEqual(
            container_response.headers.getRawHeaders(
                "X-Container-Object-Count"), None
        )
        self.assertEqual(
            container_response.headers.getRawHeaders(
                "X-Container-Bytes-Used"), None
        )

    def test_put_object(self):
        """
        PUTting an object into a container causes the container to list that
        object.
        """
        self.createSwiftService()
        # create a container
        uri = (self.json_body['access']['serviceCatalog'][0]['endpoints'][0]
               ['publicURL'] + '/testcontainer')
        create_container = request(self, self.root, "PUT", uri)
        self.successResultOf(create_container)
        BODY = b'some bytes'
        object_uri = uri + "/" + "testobject"
        object_response = request(self, self.root,
                                  "PUT", object_uri,
                                  headers={"content-type": ["text/plain"]},
                                  body=BODY)
        self.assertEqual(self.successResultOf(object_response).code,
                         201)
        container_response = self.successResultOf(
            request(self, self.root, "GET", uri)
        )
        self.assertEqual(container_response.code, 200)
        container_contents = self.successResultOf(
            treq.json_content(container_response)
        )
        self.assertEqual(len(container_contents), 1)
        self.assertEqual(container_contents[0]['name'], "testobject")
        self.assertEqual(container_contents[0]['content_type'], "text/plain")
        self.assertEqual(container_contents[0]['bytes'], len(BODY))
        object_response = self.successResultOf(
            request(self, self.root, "GET", object_uri)
        )
        self.assertEqual(object_response.code, 200)
        object_body = self.successResultOf(treq.content(object_response))
        self.assertEquals(object_body, BODY)

    def test_openstack_ids(self):
        """
        Non-Rackspace implementations of Swift just use the same tenant ID as
        other services in the catalog.

        (Note that this is not exposed by configuration yet, see
        U{https://github.com/rackerlabs/mimic/issues/85})
        """
        self.createSwiftService(False)
        url = (self.json_body['access']['serviceCatalog'][0]
               ['endpoints'][0]['publicURL'])
        self.assertIn("/fun_tenant", url)
        self.assertNotIn("/MossoCloudFS_", url)
