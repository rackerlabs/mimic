from __future__ import absolute_import, division, unicode_literals

from json import loads, dumps

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
            self, self.root, b"POST", b"/identity/v2.0/tokens",
            dumps({
                "auth": {
                    "passwordCredentials": {
                        "username": "test1",
                        "password": "test1password",
                    },
                    # TODO: should this really be 'tenantId'?
                    "tenantName": "fun_tenant",
                }
            }).encode("utf-8")
        )
        self.auth_response = self.successResultOf(self.response)
        text_body = self.successResultOf(treq.content(self.auth_response)).decode("utf-8")
        self.json_body = loads(text_body)

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
               ['publicURL'] + '/testcontainer').encode("ascii")
        create_container = request(self, self.root, b"PUT", uri)
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
               ['publicURL'] + '/testcontainer').encode("ascii")
        create_container = request(self, self.root, b"PUT", uri)
        self.successResultOf(create_container)
        container_response = self.successResultOf(
            request(self, self.root, b"GET", uri)
        )
        self.assertEqual(container_response.code, 200)
        container_contents = self.successResultOf(
            treq.json_content(container_response)
        )
        self.assertEqual(container_contents, [])
        self.assertEqual(
            container_response.headers.getRawHeaders(
                b"X-Container-Object-Count")[0], b"0"
        )
        self.assertEqual(
            container_response.headers.getRawHeaders(
                b"X-Container-Bytes-Used")[0], b"0"
        )

    def test_get_no_container(self):
        """
        GETing a container that has not been created results in a 404.
        """
        self.createSwiftService()
        # create a container
        uri = (self.json_body['access']['serviceCatalog'][0]['endpoints'][0]
               ['publicURL'] + '/testcontainer').encode("ascii")
        container_response = self.successResultOf(
            request(self, self.root, b"GET", uri)
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

    def test_head_container(self):
        """
        Validate the HEAD operation on a container.
        """
        self.createSwiftService()
        # create a container
        uri = (self.json_body['access']['serviceCatalog'][0]['endpoints'][0]
               ['publicURL'] + u'/testcontainer').encode('ascii')
        create_container = request(self, self.root, b"PUT", uri)
        self.successResultOf(create_container)

        # generate some paths with depth, swift's object name field is greedy
        # and consumes everything, including slashes, after the container name
        object_paths = [
            b"testobject",
        ]
        object_path_prefix = b""
        for i in range(10):
            object_path_prefix = (
                object_path_prefix + "{0}".format(i).encode('utf-8') + b"/")
            new_object_path = object_path_prefix + object_paths[0]
            object_paths.append(new_object_path)

        BODY = b'some bytes'
        object_size = len(BODY)
        object_count = 0
        for object_path in object_paths:
            object_count += 1
            container_counter = "{0}".format(object_count).encode("utf-8")
            container_size = "{0}".format(object_size * object_count).encode("utf-8")

            object_uri = uri + b"/" + object_path
            object_response = request(self, self.root,
                                      b"PUT", object_uri,
                                      headers={b"content-type": [b"text/plain"]},
                                      body=BODY)
            self.assertEqual(self.successResultOf(object_response).code,
                             201)
            container_response = self.successResultOf(
                request(self, self.root, b"HEAD", uri)
            )
            self.assertEqual(container_response.code, 204)
            container_contents = self.successResultOf(
                treq.content(container_response)
            )
            # Validate container meta-data
            self.assertEqual(
                container_response.headers.getRawHeaders(
                    b"X-Container-Object-Count")[0], container_counter
            )
            self.assertEqual(
                container_response.headers.getRawHeaders(
                    b"X-Container-Bytes-Used")[0], container_size
            )
            self.assertEqual(
                container_contents, b""
            )

    def test_head_no_container(self):
        """
        HEADing a container that has not been created results in a 404.
        """
        self.createSwiftService()
        # create a container
        uri = (self.json_body['access']['serviceCatalog'][0]['endpoints'][0]
               ['publicURL'] + '/testcontainer').encode("ascii")
        container_response = self.successResultOf(
            request(self, self.root, b"HEAD", uri)
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
               ['publicURL'] + u'/testcontainer').encode('ascii')
        create_container = request(self, self.root, b"PUT", uri)
        self.successResultOf(create_container)

        # generate some paths with depth, swift's object name field is greedy
        # and consumes everything, including slashes, after the container name
        object_paths = [
            b"testobject",
        ]
        object_path_prefix = b""
        for i in range(10):
            object_path_prefix = (
                object_path_prefix + "{0}".format(i).encode('utf-8') + b"/")
            new_object_path = object_path_prefix + object_paths[0]
            object_paths.append(new_object_path)

        BODY = b'some bytes'
        object_size = len(BODY)
        container_size = "{0}".format(object_size).encode("utf-8")
        for object_path in object_paths:

            object_uri = uri + b"/" + object_path
            object_response = request(self, self.root,
                                      b"PUT", object_uri,
                                      headers={b"content-type": [b"text/plain"]},
                                      body=BODY)
            self.assertEqual(self.successResultOf(object_response).code,
                             201)
            container_response = self.successResultOf(
                request(self, self.root, b"GET", uri)
            )
            self.assertEqual(container_response.code, 200)
            container_contents = self.successResultOf(
                treq.json_content(container_response)
            )
            # Validate container meta-data
            self.assertEqual(
                container_response.headers.getRawHeaders(
                    b"X-Container-Object-Count")[0], b"1"
            )
            self.assertEqual(
                container_response.headers.getRawHeaders(
                    b"X-Container-Bytes-Used")[0], container_size
            )
            # Validate container response
            self.assertEqual(len(container_contents), 1)
            self.assertEqual(container_contents[0]['name'],
                             object_path.decode('utf-8'))
            self.assertEqual(container_contents[0]['content_type'], "text/plain")
            self.assertEqual(container_contents[0]['bytes'], object_size)

            object_response = self.successResultOf(
                request(self, self.root, b"GET", object_uri)
            )
            self.assertEqual(object_response.code, 200)
            object_body = self.successResultOf(treq.content(object_response))
            self.assertEquals(object_body, BODY)

            del_object = self.successResultOf(
                request(self, self.root, b"DELETE", object_uri)
            )
            self.assertEqual(del_object.code, 204)

    def test_head_no_object_no_container(self):
        """
        HEADing a non-existing object in a non-existent container.
        """
        self.createSwiftService()
        # create a container
        uri = (self.json_body['access']['serviceCatalog'][0]['endpoints'][0]
               ['publicURL'] + u'/testcontainer').encode('ascii')

        # generate some paths with depth, swift's object name field is greedy
        # and consumes everything, including slashes, after the container name
        object_path = b"testobject"

        # head the object
        object_uri = uri + b"/" + object_path
        object_response = request(self, self.root,
                                  b"HEAD", object_uri)
        self.assertEqual(self.successResultOf(object_response).code,
                         404)

    def test_head_no_object(self):
        """
        HEADing a non-existing object in a container.
        """
        self.createSwiftService()
        # create a container
        uri = (self.json_body['access']['serviceCatalog'][0]['endpoints'][0]
               ['publicURL'] + u'/testcontainer').encode('ascii')
        create_container = request(self, self.root, b"PUT", uri)
        self.successResultOf(create_container)

        # generate some paths with depth, swift's object name field is greedy
        # and consumes everything, including slashes, after the container name
        object_path = b"testobject"

        # head the object
        object_uri = uri + b"/" + object_path
        object_response = request(self, self.root,
                                  b"HEAD", object_uri)
        self.assertEqual(self.successResultOf(object_response).code,
                         404)

    def test_head_object_no_extra_properties(self):
        """
        HEADing a object in a container but without the extra properties being
        assigned during the PUT operation.
        """
        self.createSwiftService()
        # create a container
        uri = (self.json_body['access']['serviceCatalog'][0]['endpoints'][0]
               ['publicURL'] + u'/testcontainer').encode('ascii')
        create_container = request(self, self.root, b"PUT", uri)
        self.successResultOf(create_container)

        # generate some paths with depth, swift's object name field is greedy
        # and consumes everything, including slashes, after the container name
        object_path = b"testobject"
        BODY = b'some bytes'

        # put the object
        object_uri = uri + b"/" + object_path
        object_response = request(self, self.root,
                                  b"PUT", object_uri,
                                  body=BODY)
        self.assertEqual(self.successResultOf(object_response).code,
                         201)

        # head the object
        head_response = self.successResultOf(
            request(self, self.root, b"HEAD", object_uri)
        )
        self.assertEqual(head_response.code,
                         200)
        head_contents = self.successResultOf(
            treq.content(head_response)
        )
        self.assertEqual(
            head_response.headers.getRawHeaders(b"content-type"),
            [b"application/octet-stream"])
        non_existent_headers = (
            b"content-encoding",
            b"etag",
            b"x-object-manifest",
            b"x-object-meta-name"
        )
        for header_key in non_existent_headers:
            self.assertIsNone(head_response.headers.getRawHeaders(header_key))

        self.assertEqual(head_contents, b'')

    def test_head_object_with_extra_properties(self):
        """
        HEADing a object in a container but without the extra properties being
        assigned during the PUT operation.
        """
        self.createSwiftService()
        # create a container
        uri = (self.json_body['access']['serviceCatalog'][0]['endpoints'][0]
               ['publicURL'] + u'/testcontainer').encode('ascii')
        create_container = request(self, self.root, b"PUT", uri)
        self.successResultOf(create_container)

        # generate some paths with depth, swift's object name field is greedy
        # and consumes everything, including slashes, after the container name
        object_path = b"testobject"
        BODY = b'some bytes'

        property_values = {
            b"content-type": [b"application/test-value"],
            b"content-encoding": [b"ascii"],
            b"etag": [b"etag_in_123456"],
            b"x-object-manifest": [b"{object/1}"],
            b"x-object-meta-name": [b"2bd4"]
        }

        # put the object
        object_uri = uri + b"/" + object_path
        object_response = request(self, self.root,
                                  b"PUT", object_uri,
                                  headers=property_values,
                                  body=BODY)
        self.assertEqual(self.successResultOf(object_response).code,
                         201)

        # head the object
        head_response = self.successResultOf(
            request(self, self.root, b"HEAD", object_uri)
        )
        self.assertEqual(head_response.code,
                         200)
        head_contents = self.successResultOf(
            treq.content(head_response)
        )
        header_keys = (
            b"content-type",
            b"content-encoding",
            b"etag",
            b"x-object-manifest",
            b"x-object-meta-name"
        )
        for header_key in header_keys:
            self.assertEqual(
                head_response.headers.getRawHeaders(header_key),
                property_values[header_key])

        self.assertEqual(head_contents, b'')

    def test_delete_object(self):
        """
        Deleting an object from a container.
        """
        self.createSwiftService()
        # create a container
        uri = (self.json_body['access']['serviceCatalog'][0]['endpoints'][0]
               ['publicURL'] + u'/testcontainer').encode('ascii')
        create_container = request(self, self.root, b"PUT", uri)
        self.successResultOf(create_container)

        # generate some paths with depth, swift's object name field is greedy
        # and consumes everything, including slashes, after the container name
        object_path = b"testobject"
        BODY = b'some bytes'

        # put the object
        object_uri = uri + b"/" + object_path
        object_response = request(self, self.root,
                                  b"PUT", object_uri,
                                  headers={b"content-type": [b"text/plain"]},
                                  body=BODY)
        self.assertEqual(self.successResultOf(object_response).code,
                         201)

        # then delete it
        delete_response = request(self, self.root,
                                  b"DELETE", object_uri)
        self.assertEqual(self.successResultOf(delete_response).code,
                         204)

        # ensure it's no longer listed
        container_response = self.successResultOf(
            request(self, self.root, b"GET", uri)
        )
        self.assertEqual(container_response.code, 200)
        container_contents = self.successResultOf(
            treq.json_content(container_response)
        )
        self.assertEqual(len(container_contents), 0)

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
