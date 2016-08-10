from __future__ import absolute_import, division, unicode_literals

from json import loads, dumps

import ddt

from twisted.trial.unittest import SynchronousTestCase
from twisted.internet.task import Clock

import treq

from mimic.rest.swift_api import SwiftMock
from mimic.resource import MimicRoot
from mimic.core import MimicCore
from mimic.rest.swift_api import normal_tenant_id_to_crazy_mosso_id
from mimic.test.helpers import request


class SwiftTestBase(SynchronousTestCase):
    """
    Common functionality for testing the Swift API.
    """

    def createSwiftService(self, rackspace_flavor=True):
        """
        Set up to create the requests
        """
        self.swift_mock = SwiftMock(rackspace_flavor)
        self.core = MimicCore(Clock(), [self.swift_mock])
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

    def setUp(self):
        """
        Setup common functionality
        """
        super(SwiftTestBase, self).setUp()
        self.createSwiftService()

        self.tenant_id = self.json_body['access']['token']['tenant']['id']
        self.token = self.json_body['access']['token']['id']
        self.swift_endpoint = (
            self.json_body['access']['serviceCatalog'][0]['endpoints'][0])
        self.swift_uri = self.swift_endpoint['publicURL']

        # container information
        self.container_name = u"/testcontainer"
        self.uri = (self.swift_uri + self.container_name).encode('ascii')

        # object information
        self.object_path = b"testobject"
        self.object_uri = self.uri + b"/" + self.object_path
        self.object_data = b'some bytes'
        self.object_size = len(self.object_data)

    def head_account(self, expected_result=204, with_body=True):
        """
        HEAD a container - retrieve the meta-data on the container
        """
        container_response = self.successResultOf(
            request(self, self.root, b"HEAD", self.swift_uri)
        )
        self.assertEqual(container_response.code, expected_result)

        container_contents = None
        if with_body:
            container_contents = self.successResultOf(
                treq.content(container_response)
            )

        return (container_response, container_contents)

    def post_account(self, expected_result=204, with_body=True, headers=None):
        """
        POST an account - create metadata on an account
        """
        container_response = self.successResultOf(
            request(self, self.root, b"POST", self.swift_uri, headers=headers)
        )
        self.assertEqual(container_response.code, expected_result)

        container_contents = None
        if with_body:
            container_contents = self.successResultOf(
                treq.content(container_response)
            )

        return (container_response, container_contents)

    def put_container(self, container_path=None, expected_result=201):
        """
        PUT a container - create a container
        """
        container_uri = (
            container_path if container_path is not None else self.uri)
        create_container = request(self, self.root, b"PUT", container_uri)
        create_container_response = self.successResultOf(create_container)
        self.assertEqual(create_container_response.code, expected_result)
        self.assertEqual(
            self.successResultOf(treq.content(create_container_response)),
            b"",
        )

    def head_container(self, container_path=None, expected_result=204,
                       with_body=True):
        """
        HEAD a container - retrieve the meta-data on the container
        """
        container_uri = (
            container_path if container_path is not None else self.uri)
        container_response = self.successResultOf(
            request(self, self.root, b"HEAD", container_uri)
        )
        self.assertEqual(container_response.code, expected_result)

        container_contents = None
        if with_body:
            container_contents = self.successResultOf(
                treq.content(container_response)
            )

        return (container_response, container_contents)

    def get_container(self, container_path=None, expected_result=200,
                      with_body=True):
        """
        GET a container - retrieve the listing of objects in the container
        """
        container_uri = (
            container_path if container_path is not None else self.uri)
        container_response = self.successResultOf(
            request(self, self.root, b"GET", container_uri)
        )
        self.assertEqual(container_response.code, expected_result)

        container_contents = None
        if with_body:
            container_contents = self.successResultOf(
                treq.json_content(container_response)
            )

        return (container_response, container_contents)

    def delete_container(self, container_path=None, expected_result=204):
        """
        DELETE a container.
        """
        container_uri = (
            container_path if container_path is not None else self.uri)
        container_response = self.successResultOf(
            request(self, self.root, b"DELETE", container_uri)
        )
        self.assertEqual(container_response.code, expected_result)
        return container_response

    def put_object(self, object_path=None, expected_result=201, body=None,
                   headers=None):
        """
        PUT an object into the container

        :param object_path: optional object path for where to put the object.
                            if None, then the default self.object_uri is used.
        :param body: optional object data to upload, if None then the default
                     self.object_data is used
        :param headers: optional header data to pass as part of the request
        :param expected_result: expected HTTP Status Code
        """
        object_uri = object_path if object_path is not None else self.object_uri
        object_data = body if body is not None else self.object_data
        object_response = request(self, self.root,
                                  b"PUT", object_uri,
                                  headers=headers,
                                  body=object_data)
        self.assertEqual(self.successResultOf(object_response).code,
                         expected_result)

        return object_response

    def head_object(self, object_path=None, expected_result=200, with_body=True):
        """
        HEAD an object in the container.

        :param object_path: optional object path for where to put the object.
                            if None, then the default self.object_uri is used.
        :param expected_result: expected HTTP Status Code
        :param with_body: boolean value for whether or not to retrieve the
            content of the message, useful for accessing the headers
        """
        head_response = self.successResultOf(
            request(self, self.root, b"HEAD", self.object_uri)
        )
        self.assertEqual(head_response.code,
                         expected_result)
        head_contents = None
        if with_body:
            head_contents = self.successResultOf(
                treq.content(head_response)
            )
        return (head_response, head_contents)

    def get_object(self, object_path=None, expected_result=200, with_body=True):
        """
        GET an object from the container.

        :param object_path: optional object path for where to put the object.
                            if None, then the default self.object_uri is used.
        :param expected_result: expected HTTP Status Code
        :param with_body: boolean value for whether or not to retrieve the
            content of the message, useful for accessing the headers
        """
        object_uri = object_path if object_path is not None else self.object_uri
        object_response = self.successResultOf(
            request(self, self.root, b"GET", object_uri)
        )
        self.assertEqual(object_response.code, expected_result)
        object_body = None
        if with_body:
            object_body = self.successResultOf(treq.content(object_response))

        return (object_response, object_body)

    def delete_object(self, object_path=None, expected_result=204):
        """
        DELETE an object in the container.

        :param object_path: optional object path for where to put the object.
                            if None, then the default self.object_uri is used.
        :param expected_result: expected HTTP Status Code
        """
        object_uri = object_path if object_path is not None else self.object_uri
        del_object = self.successResultOf(
            request(self, self.root, b"DELETE", object_uri)
        )
        self.assertEqual(del_object.code, expected_result)
        return del_object


class SwiftGenericTests(SwiftTestBase):
    """
    Generic Tests for Swift that do not necessarily have to do with Swift itself
    such as the Service Catalog.
    """

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


@ddt.ddt
class SwiftAccountTests(SwiftTestBase):
    """
    Swift Account Tests.
    """

    @ddt.data(
        (0, 0),
        (1, 0),
        (2, 5),
    )
    @ddt.unpack
    def test_head_account(self, container_count, object_count):
        """
        HEAD an account reports the container count, object count,
        and number of bytes used.

        :param container_count: number of containers under the
            account.
        :param object_count: number of objects in each container.

        .. note:: the test will add the specified the number of
            containers with the specified of objects. These
            values are directly used. However, the objects are
            a constant size set by SwiftTestBase.setUp() which is
            indirectly used for the total bytes calculation.
        """
        # Add containers and objects per parameters
        for container_index in range(container_count):
            container_uri = (
                self.swift_uri +
                "/container{0}".format(container_index))
            self.put_container(container_path=container_uri)

            for object_index in range(object_count):
                object_uri = (
                    container_uri +
                    "/object{0}".format(object_index))
                self.put_object(object_path=object_uri)

        # now try to head the account
        head_response, head_content = self.head_account()

        total_objects = object_count * container_count
        total_bytes = total_objects * self.object_size

        # validate the headers
        self.assertEqual(
            head_response.headers.getRawHeaders(
                b"X-Account-Container-Count")[0],
            "{0}".format(container_count).encode("utf-8"))
        self.assertEqual(
            head_response.headers.getRawHeaders(
                b"X-Account-Object-Count")[0],
            "{0}".format(total_objects).encode("utf-8"))
        self.assertEqual(
            head_response.headers.getRawHeaders(
                b"X-Account-Bytes-Used")[0],
            "{0}".format(total_bytes).encode("utf-8"))

    @ddt.data(
        True,
        False
    )
    def test_post_account_metadata(self, post_metadata):
        """
        POST an account saves metadata to the account.

        :param bool post_metadata: whether or not to include metadata
            in the POST request.

        .. note:: uses HEAD to verify the data was saved.
        """
        headers = None
        if post_metadata:
            # Add customer headers that should be returne in the HEAD
            # operation.
            headers = {
                b"X-Account-Meta-MockTest": [b"HelloWorld"],
                b"x-account-meta-field": [b"WorldWide"]
            }

        post_response, post_content = self.post_account(headers=headers)

        # validate via a HEAD operation
        head_response, head_content = self.head_account()

        if headers is not None:
            # Verify each header that was posted to the account was
            # returned in the HEAD request.
            for k, v in headers.items():
                self.assertEqual(
                    head_response.headers.getRawHeaders(k),
                    v)
        else:
            # Verify that there are no headers present that start with
            # the magic prefix of X-Account-Meta-
            for k, _ in head_response.headers.getAllRawHeaders():
                key = k.decode("utf-8").lower()
                self.assertFalse(key.startswith("x-account-meta-"))


class SwiftContainerTests(SwiftTestBase):
    """
    Swift Container Tests.
    """

    def test_create_container(self):
        """
        PUT container creates a container.
        """
        self.put_container(expected_result=201)

    def test_create_twice(self):
        """
        Creating a container twice results in an ACCEPTED status code.
        """
        self.put_container(expected_result=201)
        self.put_container(expected_result=202)
        self.put_container(expected_result=202)

    def test_delete_container(self):
        """
        DELETEing a container.
        """
        # create a container
        self.put_container()

        # delete the container
        self.delete_container()

    def test_delete_container_non_existent(self):
        """
        DELETE a non-existent container.
        """
        self.delete_container(expected_result=404)

    def test_delete_container_non_empty(self):
        """
        DELETE a non-empty container returns 409 Conflict.
        """
        # create a container
        self.put_container()

        # put the object
        self.put_object(headers={b"content-type": [b"text/plain"]})

        # delete the container
        self.delete_container(expected_result=409)

    def test_get_container(self):
        """
        Creating a container and immediately retrieving it yields an empty list
        (since there are no objects) and several headers indicating that no
        objects are in the container and they consume no space.
        """
        # create a container
        self.put_container()

        # get the container
        container_response, container_contents = self.get_container()

        # validate the response
        self.assertEqual(container_contents, [])
        self.assertEqual(
            container_response.headers.getRawHeaders(
                b"X-Container-Object-Count")[0], b"0"
        )
        self.assertEqual(
            container_response.headers.getRawHeaders(
                b"X-Container-Bytes-Used")[0], b"0"
        )

    def test_get_container_non_existent(self):
        """
        GET a container that has not been created results in a 404.
        """
        # create a container
        container_response, _ = self.get_container(
            expected_result=404, with_body=False)

        # Validate the response
        self.assertIsNone(
            container_response.headers.getRawHeaders(
                "X-Container-Object-Count")
        )
        self.assertIsNone(
            container_response.headers.getRawHeaders(
                "X-Container-Bytes-Used")
        )

    def test_get_container_non_empty(self):
        """
        GET a non-empty container.
        """
        # create a container
        self.put_container()

        # put the object
        self.put_object(headers={b"content-type": [b"text/plain"]})

        # get the container
        container_response, container_contents = self.get_container()

        # validate the response
        self.assertNotEqual(container_contents, [])
        self.assertEqual(len(container_contents), 1)
        self.assertEqual(container_contents[0]['name'],
                         self.object_path.decode('utf-8'))
        self.assertEqual(container_contents[0]['content_type'], "text/plain")
        self.assertEqual(container_contents[0]['bytes'], self.object_size)
        self.assertEqual(
            container_response.headers.getRawHeaders(
                b"X-Container-Object-Count")[0], b"1"
        )
        self.assertEqual(
            container_response.headers.getRawHeaders(
                b"X-Container-Bytes-Used")[0],
            "{0}".format(self.object_size).encode("utf-8")
        )

    def test_head_container(self):
        """
        HEAD a container.
        """
        # create a container
        self.put_container()

        # the container should have some information in it
        # the names of the object's don't matter, but having some
        # dynamic content will help prove it's all working correctly
        # so generate a series of objects names to use
        object_paths = [
            self.object_path,
        ]
        object_path_prefix = b""
        for i in range(10):
            object_path_prefix = (
                object_path_prefix + "_{0}_".format(i).encode('utf-8'))
            new_object_path = object_path_prefix + object_paths[0]
            object_paths.append(new_object_path)

        # loop through and add each object then validate that the container
        # meta-data changed appropriately
        object_count = 0
        for object_path in object_paths:
            # calculate what the container should look like after the object
            # has been uploaded
            object_count += 1
            container_counter = "{0}".format(object_count).encode("utf-8")
            container_size = "{0}".format(
                self.object_size * object_count).encode("utf-8")

            # upload the object into the container
            object_uri = self.uri + b"/" + object_path
            self.put_object(
                object_path=object_uri,
                headers={b"content-type": [b"text/plain"]})

            # head the container
            container_response, container_contents = self.head_container()

            # Validate container meta-data
            self.assertEqual(
                container_response.headers.getRawHeaders(
                    b"X-Container-Object-Count")[0], container_counter
            )
            self.assertEqual(
                container_response.headers.getRawHeaders(
                    b"X-Container-Bytes-Used")[0], container_size
            )

            # head operation should not have a body
            self.assertEqual(
                container_contents, b""
            )

    def test_head_container_non_existent(self):
        """
        HEAD a container that has not been created results in a 404.
        """
        # head a container
        container_response, _ = self.head_container(
            expected_result=404, with_body=False)

        # validate the response
        self.assertIsNone(
            container_response.headers.getRawHeaders(
                "X-Container-Object-Count")
        )
        self.assertIsNone(
            container_response.headers.getRawHeaders(
                "X-Container-Bytes-Used")
        )

    def test_head_container_non_empty(self):
        """
        HEAD a non-empty container
        """
        # create a container
        self.put_container()

        # put the object
        self.put_object(headers={b"content-type": [b"text/plain"]})

        # head the container
        container_response, container_contents = self.head_container()

        # validate the response
        self.assertEqual(container_contents, b"")
        self.assertEqual(
            container_response.headers.getRawHeaders(
                b"X-Container-Object-Count")[0], b"1"
        )
        self.assertEqual(
            container_response.headers.getRawHeaders(
                b"X-Container-Bytes-Used")[0],
            "{0}".format(self.object_size).encode("utf-8")
        )


class SwiftObjectTests(SwiftTestBase):
    """
    Swift Object Tests
    """

    def setUp(self):
        """
        Configure for the test
        """
        super(SwiftObjectTests, self).setUp()

        # in most of the tests we want to have an existing
        # container. Those that do not need it can remove it.
        self.put_container()

    def test_get_object(self):
        """
        GET object - basic test.
        """
        # put an object
        self.put_object(headers={b"content-type": [b"text/plain"]})

        # get the object
        object_response, object_content = self.get_object()

        # validate the response
        self.assertEquals(object_content, self.object_data)

    def test_get_object_path_based_name(self):
        """
        GET object - object name is a path instead of a simple string.
        """
        # generate some paths with depth, swift's object name field is greedy
        # and consumes everything, including slashes, after the container name
        object_paths = [
            self.object_path,
        ]
        object_path_prefix = b""
        for i in range(10):
            object_path_prefix = (
                object_path_prefix + "{0}".format(i).encode('utf-8') + b"/")
            new_object_path = object_path_prefix + object_paths[0]
            object_paths.append(new_object_path)

        for object_path in object_paths:
            # put the object
            object_uri = self.uri + b"/" + object_path
            self.put_object(
                object_path=object_uri,
                headers={b"content-type": [b"text/plain"]},
            )

            # Get the object
            object_response, object_body = self.get_object(
                object_path=object_uri)
            self.assertEquals(object_body, self.object_data)

    def test_get_object_non_existent_container_non_existent_object(self):
        """
        GET object - container doesn't exist, object doesn't exist.
        """
        # setUp() auto-creates a container, so delete it first
        self.delete_container()

        # now try to get the object
        self.get_object(expected_result=404)

    def test_get_object_non_existent_object(self):
        """
        GET object - get a non-existent object from the existing container.
        """
        # now try to get the object
        self.get_object(expected_result=404)

    def test_get_object_with_properties(self):
        """
        GET object - get an object with additional properties set.
        """
        property_values = {
            b"content-type": [b"application/test-value"],
            b"content-encoding": [b"ascii"],
            b"etag": [b"etag_in_123456"],
            b"x-object-manifest": [b"{object/1}"],
            b"x-object-meta-name": [b"2bd4"]
        }
        # put the object
        self.put_object(headers=property_values)

        # now try to get the object
        object_response, object_content = self.get_object()

        # Validate the headers
        header_keys = (
            b"content-type",
            b"content-encoding",
            b"etag",
            b"x-object-manifest",
            b"x-object-meta-name"
        )
        for header_key in header_keys:
            self.assertEqual(
                object_response.headers.getRawHeaders(header_key),
                property_values[header_key])

        self.assertEqual(object_content, self.object_data)

    def test_get_object_without_properties(self):
        """
        GET object - get an object without any additional properties set.
        """
        # put the object
        self.put_object()

        # now try to get the object
        object_response, object_content = self.get_object()

        # Validate the headers
        self.assertEqual(
            object_response.headers.getRawHeaders(b"content-type"),
            [b"application/octet-stream"])

        header_keys = (
            b"content-encoding",
            b"etag",
            b"x-object-manifest",
            b"x-object-meta-name"
        )
        for header_key in header_keys:
            self.assertIsNone(
                object_response.headers.getRawHeaders(header_key))

        self.assertEqual(object_content, self.object_data)

    def test_put_object(self):
        """
        PUT an object into a container causes the container to list that
        object.
        """
        # put the object
        self.put_object(headers={b"content-type": [b"text/plain"]})

        # get the container listing
        container_response, container_contents = self.get_container()

        # Validate container meta-data
        self.assertEqual(
            container_response.headers.getRawHeaders(
                b"X-Container-Object-Count")[0], b"1"
        )
        self.assertEqual(
            container_response.headers.getRawHeaders(
                b"X-Container-Bytes-Used")[0],
            "{0}".format(self.object_size).encode("ascii")
        )
        # Validate container response
        self.assertEqual(len(container_contents), 1)
        self.assertEqual(container_contents[0]['name'],
                         self.object_path.decode('utf-8'))
        self.assertEqual(container_contents[0]['content_type'], "text/plain")
        self.assertEqual(container_contents[0]['bytes'], self.object_size)

        # Get the object
        object_response, object_body = self.get_object(
            object_path=self.object_uri)
        self.assertEquals(object_body, self.object_data)

    def test_put_object_path_based_name(self):
        """
        PUT object - object name is a path instead of a simple string.
        """
        # generate some paths with depth, swift's object name field is greedy
        # and consumes everything, including slashes, after the container name
        object_paths = [
            self.object_path,
        ]
        object_path_prefix = b""
        for i in range(10):
            object_path_prefix = (
                object_path_prefix + "{0}".format(i).encode('utf-8') + b"/")
            new_object_path = object_path_prefix + object_paths[0]
            object_paths.append(new_object_path)

        container_size = "{0}".format(self.object_size).encode("utf-8")
        for object_path in object_paths:

            object_uri = self.uri + b"/" + object_path
            self.put_object(
                object_path=object_uri,
                headers={b"content-type": [b"text/plain"]},
            )

            container_response, container_contents = self.get_container()

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
            self.assertEqual(container_contents[0]['bytes'], self.object_size)

            # Get the object
            object_response, object_body = self.get_object(
                object_path=object_uri)
            self.assertEquals(object_body, self.object_data)

            # clean up the object
            self.delete_object(object_path=object_uri)

    def test_put_object_updates_object(self):
        """
        PUT object - put objects can update the container while leaving other
        data alone if the object already existed.
        """
        self.put_object()

        new_data = b"new object"
        self.put_object(body=new_data)

        # Get the object
        object_response, object_body = self.get_object()
        self.assertEquals(object_body, new_data)

    def test_put_object_non_existent_container(self):
        """
        PUT object - attempt to put an object to a non-existent container.
        """
        # setUp() auto-creates a container, so delete it first
        self.delete_container()

        # put an object
        self.put_object(expected_result=404)

    def test_put_object_with_properties(self):
        """
        PUT object - add an object with extraneous properties.
        """
        property_values = {
            b"content-type": [b"application/test-value"],
            b"content-encoding": [b"ascii"],
            b"etag": [b"etag_in_123456"],
            b"x-object-manifest": [b"{object/1}"],
            b"x-object-meta-name": [b"2bd4"]
        }
        # put the object
        self.put_object(headers=property_values)

        # now try to head the object - could also use  get_object()
        object_response, object_content = self.head_object()

        # Validate the headers
        header_keys = (
            b"content-type",
            b"content-encoding",
            b"etag",
            b"x-object-manifest",
            b"x-object-meta-name"
        )
        for header_key in header_keys:
            self.assertEqual(
                object_response.headers.getRawHeaders(header_key),
                property_values[header_key])

    def test_put_object_without_properties(self):
        """
        PUT object - add an object without any extraneous properties.
        """
        # put the object
        self.put_object()

        # now try to head the object - could also use get_object()
        object_response, object_content = self.head_object()

        # Validate the headers
        self.assertEqual(
            object_response.headers.getRawHeaders(b"content-type"),
            [b"application/octet-stream"])

        header_keys = (
            b"content-encoding",
            b"etag",
            b"x-object-manifest",
            b"x-object-meta-name"
        )
        for header_key in header_keys:
            self.assertIsNone(
                object_response.headers.getRawHeaders(header_key))

    def test_head_object(self):
        """
        HEAD object - HEAD an object in storage.
        """
        # put the object
        self.put_object()

        # head the object
        object_response, object_content = self.head_object(with_body=True)
        self.assertEqual(object_content, b"")

    def test_head_object_path_based_name(self):
        """
        HEAD object - object name is a path instead of a simple string.
        """
        object_paths = [
            self.object_path,
        ]
        object_path_prefix = b""
        for i in range(10):
            object_path_prefix = (
                object_path_prefix + "{0}".format(i).encode('utf-8') + b"/")
            new_object_path = object_path_prefix + object_paths[0]
            object_paths.append(new_object_path)

        for object_path in object_paths:
            # put the object
            object_uri = self.uri + b"/" + object_path
            self.put_object(
                object_path=object_uri,
                headers={b"content-type": [b"text/plain"]},
            )

            # HEAD the object
            object_response, object_body = self.head_object(
                object_path=object_uri, with_body=True)
            self.assertEquals(object_body, b"")

    def test_head_object_non_existent_container_non_existent_object(self):
        """
        HEAD a non-existing object in a non-existent container.
        """
        # setUp() auto-creates a container, so delete it first
        self.delete_container()
        # head the object
        self.head_object(expected_result=404, with_body=False)

    def test_head_object_non_existent_object(self):
        """
        HEAD a non-existing object in a container.
        """
        # head the object
        self.head_object(expected_result=404, with_body=False)

    def test_head_object_with_properties(self):
        """
        HEAD a object in a container but without the extra properties being
        assigned during the PUT operation.
        """
        property_values = {
            b"content-type": [b"application/test-value"],
            b"content-encoding": [b"ascii"],
            b"etag": [b"etag_in_123456"],
            b"x-object-manifest": [b"{object/1}"],
            b"x-object-meta-name": [b"2bd4"]
        }
        # put the object
        self.put_object(headers=property_values)

        # head the object
        head_response, head_contents = self.head_object()

        # Validate the headers
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

    def test_head_object_without_properties(self):
        """
        HEAD a object in a container but without the extra properties being
        assigned during the PUT operation.
        """
        # put the object
        self.put_object()

        # head the object
        head_response, head_contents = self.head_object()

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

    def test_delete_object(self):
        """
        DELETE an object from a container.
        """
        # put the object
        self.put_object(headers={b"content-type": [b"text/plain"]})

        # ensure it's listed
        container_response, container_contents = self.get_container()
        self.assertEqual(len(container_contents), 1)

        # then delete it
        self.delete_object()

        # ensure it's no longer listed
        container_response, container_contents = self.get_container()
        self.assertEqual(len(container_contents), 0)

    def test_delete_object_path_based_name(self):
        """
        DELETE object - object name is a path instead of a simple string.
        """
        object_paths = [
            self.object_path,
        ]
        object_path_prefix = b""
        for i in range(10):
            object_path_prefix = (
                object_path_prefix + "{0}".format(i).encode('utf-8') + b"/")
            new_object_path = object_path_prefix + object_paths[0]
            object_paths.append(new_object_path)

        for object_path in object_paths:
            # put the object
            object_uri = self.uri + b"/" + object_path
            self.put_object(
                object_path=object_uri,
                headers={b"content-type": [b"text/plain"]},
            )

            self.delete_object(object_path=object_uri)

    def test_delete_object_non_existent_container_non_existent_object(self):
        """
        DELETE object - remove non-existent object from non-existent container.
        """
        # setUp() auto-creates a container, so delete it first
        self.delete_container()

        # remove the object
        self.delete_object(expected_result=404)

    def test_delete_object_non_existent_object(self):
        """
        DELETE object - non-existent object in existing container.
        """
        # remove the object
        self.delete_object(expected_result=404)
