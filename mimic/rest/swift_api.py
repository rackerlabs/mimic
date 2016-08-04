# -*- test-case-name: mimic.test.test_swift -*-

"""
API mock for OpenStack Swift / Rackspace Cloud Files.
"""

from __future__ import absolute_import, division, unicode_literals

from uuid import uuid4, uuid5, NAMESPACE_URL
from six import text_type

import attr
from json import dumps

from mimic.imimic import IAPIMock
from twisted.plugin import IPlugin
from twisted.web.http import CREATED, ACCEPTED, OK

from mimic.catalog import Entry
from mimic.catalog import Endpoint
from mimic.rest.mimicapp import MimicApp
from twisted.web.http import CONFLICT
from twisted.web.resource import ErrorPage, NoResource
from zope.interface import implementer


class Conlict(ErrorPage):
    """
    HTTP 409 Conflict
    """

    def __init__(self, message="Sorry, Conflict prevents operation"):
        """
        Construct an object that will return an HTTP 409 Conflict message.
        """
        ErrorPage.__init__(self, CONFLICT, "Conflict", message)


def normal_tenant_id_to_crazy_mosso_id(normal_tenant_id):
    """
    Convert the tenant ID used by basically everything else (keystone, nova,
    loadbalancers, and so on) into the somewhat peculiar tenant ID used by
    Cloud Files, for maximum realism.

    :param unicode normal_tenant_id: the tenant ID from identity.

    :return: a new tenant ID that looks like a Cloud Files tenant ID
    :rtype: unicode
    """
    full_namespace = (u"https://github.com/rackerlabs/mimic/ns/tenant/"
                      + normal_tenant_id)
    if bytes is str:
        full_namespace = full_namespace.encode("ascii")
    uuid = uuid5(NAMESPACE_URL, full_namespace)
    return u"MossoCloudFS_" + text_type(uuid)


@implementer(IAPIMock, IPlugin)
class SwiftMock(object):
    """
    API mock for Swift.
    """

    def __init__(self, rackspace_flavor=True):
        """
        Construct a SwiftMock, either using Rackspace's tenant-ID translation
        idiom or not.
        """
        self._regions = ["ORD", "DFW", "IAD"]
        if rackspace_flavor:
            self.translate_tenant = normal_tenant_id_to_crazy_mosso_id
        else:
            self.translate_tenant = str

    def catalog_entries(self, tenant_id):
        """
        Catalog entry for Swift endpoints.
        """
        modified = self.translate_tenant(tenant_id)
        return [
            Entry(modified, "object-store", "cloudFiles", [
                Endpoint(modified, region, text_type(uuid4()), prefix="v1")
                for region in self._regions
            ])
        ]

    def resource_for_region(self, region, uri_prefix, session_store):
        """
        Return an IResource implementing a public Swift region endpoint.
        """
        return SwiftRegion(
            api=self,
            uri_prefix=uri_prefix,
            session_store=session_store).app.resource()


@attr.s
class SwiftRegion(object):
    """
    :obj:`SwiftRegion` is a set of klein routes and application representing a
    Swift endpoint.
    """
    api = attr.ib()
    uri_prefix = attr.ib()
    session_store = attr.ib()

    app = MimicApp()

    @app.route("/v1/<string:tenant_id>", branch=True)
    def get_one_tenant_resource(self, request, tenant_id):
        """
        Get a resource for a tenant in this region.
        """
        return (self.session_store.session_for_tenant_id(tenant_id)
                .data_for_api(self.api,
                              lambda:
                              SwiftTenantInRegion().app.resource()))


@attr.s
class Object(object):
    """
    A Python object (i.e. instance) representing a Swift object (i.e. bag of
    octets).
    """
    name = attr.ib()
    content_type = attr.ib()
    content_encoding = attr.ib()
    etag = attr.ib()
    object_manifest = attr.ib()
    object_meta_name = attr.ib()

    data = attr.ib()

    @property
    def length(self):
        """
        Return the length of the data
        """
        return len(self.data)

    def as_json(self):
        """
        Create a JSON-serializable representation of the contents of this
        object.
        """
        return {
            "name": self.name,
            "content_type": self.content_type,
            "bytes": self.length,
        }


@attr.s
class Container(object):
    """
    A Swift container (collection of :obj:`Object`.)
    """
    name = attr.ib()
    objects = attr.ib(default=attr.Factory(dict))

    @property
    def object_count(self):
        """
        Return the number of objects in the container
        """
        return len(self.objects)

    @property
    def byte_count(self):
        """
        Return the sum of data of all the objects in the container
        """
        byte_count = 0
        for obj in self.objects.values():
            byte_count += obj.length
        return byte_count


class SwiftTenantInRegion(object):
    """
    A :obj:`SwiftTenantInRegion` represents a single tenant and their
    associated storage resources within one region.
    """

    app = MimicApp()

    def __init__(self):
        """
        Initialize a tenant with some containers.
        """
        self.containers = {}
        self.metadata = {}

    @app.route("/", methods=["POST"])
    def create_account_metadata(self, request):
        """
        Save the meta-data
        """
        for k, v in request.requestHeaders.getAllRawHeaders():
            key = k.decode("utf-8")
            key_compare = key.lower()
            if key_compare.startswith("x-account-meta-"):
                metakey_name = key[len("x-account-meta-"):]
                self.metadata[metakey_name] = v
        request.setResponseCode(204)
        return b""

    @app.route("/", methods=["HEAD"])
    def head_account(self, request):
        """
        Api call to get the meta-data regarding all containers for a tenant
        """
        total_containers = len(self.containers)
        total_objects = 0
        total_bytes = 0
        for container in self.containers.values():
            total_objects += container.object_count
            total_bytes += container.byte_count
        container_count = "{0}".format(total_containers).encode("utf-8")
        object_count = "{0}".format(total_objects).encode("utf-8")
        byte_count = "{0}".format(total_bytes).encode("utf-8")
        request.responseHeaders.setRawHeaders(b"content-type",
                                              [b"application/json"])
        request.responseHeaders.setRawHeaders(b"x-account-container-count",
                                              [container_count])
        request.responseHeaders.setRawHeaders(b"x-account-object-count",
                                              [object_count])
        request.responseHeaders.setRawHeaders(b"x-account-bytes-used",
                                              [byte_count])
        for k, v in self.metadata.items():
            request.responseHeaders.setRawHeaders(
                "X-Account-Meta-{0}".format(k).encode("utf-8"),
                v)

        request.setResponseCode(204)
        return b""

    @app.route("/<string:container_name>", methods=["PUT"])
    def create_container(self, request, container_name):
        """
        Api call to create and save container.  HTTP status code of 201 if
        created, else returns 202.
        """
        if container_name not in self.containers:
            self.containers[container_name] = Container(name=container_name)
            request.setResponseCode(CREATED)
        else:
            request.setResponseCode(ACCEPTED)
        return b""

    @app.route("/<string:container_name>", methods=["HEAD"])
    def head_container(self, request, container_name):
        """
        Api call to get the meta-data regarding a container
        """
        if container_name in self.containers:
            container = self.containers[container_name]
            object_count = "{0}".format(container.object_count).encode("utf-8")
            byte_count = "{0}".format(container.byte_count).encode("utf-8")
            request.responseHeaders.setRawHeaders(b"content-type",
                                                  [b"application/json"])
            request.responseHeaders.setRawHeaders(b"x-container-object-count",
                                                  [object_count])
            request.responseHeaders.setRawHeaders(b"x-container-bytes-used",
                                                  [byte_count])
            request.setResponseCode(204)
            return b""

        else:
            return NoResource("No such container")

    @app.route("/<string:container_name>", methods=["GET"])
    def get_container(self, request, container_name):
        """
        Api call to get a container, given the name of the container.  HTTP
        status code of 200 when such a container exists, 404 if not.
        """
        if container_name in self.containers:
            container = self.containers[container_name]
            object_count = "{0}".format(container.object_count).encode("utf-8")
            byte_count = "{0}".format(container.byte_count).encode("utf-8")
            request.responseHeaders.setRawHeaders(b"content-type",
                                                  [b"application/json"])
            request.responseHeaders.setRawHeaders(b"x-container-object-count",
                                                  [object_count])
            request.responseHeaders.setRawHeaders(b"x-container-bytes-used",
                                                  [byte_count])
            request.setResponseCode(OK)
            return dumps([
                obj.as_json() for obj in
                self.containers[container_name].objects.values()
            ])
        else:
            return NoResource("No such container")

    @app.route("/<string:container_name>", methods=["DELETE"])
    def delete_container(self, request, container_name):
        """
        Api call to remove a container
        """
        if container_name in self.containers:
            if len(self.containers[container_name].objects) == 0:
                del self.containers[container_name]

                request.setResponseCode(204)
                return b""

            else:
                return Conlict("Container not empty")

        else:
            return NoResource("No such container")

    @app.route("/<string:container_name>/<path:object_name>",
               methods=["HEAD"])
    def head_object(self, request, container_name, object_name):
        """
        Get an object from a container.
        """
        if container_name in self.containers:
            container = self.containers[container_name]
            if object_name in container.objects:
                obj = container.objects[object_name]

                def set_header_if_not_none(header_key, obj_value):
                    if obj_value is not None:
                        request.responseHeaders.setRawHeaders(
                            header_key, [obj_value.encode("ascii")])

                set_header_if_not_none(
                    b"content-type",
                    obj.content_type if obj.content_type is not None else
                    u"application/octet-stream")
                set_header_if_not_none(b"content-encoding", obj.content_encoding)
                set_header_if_not_none(b"etag", obj.etag)
                set_header_if_not_none(b"x-object-manifest", obj.object_manifest)
                set_header_if_not_none(b"x-object-meta-name", obj.object_meta_name)

                # return 200 since it actually "touches" the object
                # while non-standard, this is how the Swift API works :(
                request.setResponseCode(200)
                return b""
            else:
                return NoResource("No such object in container")
        else:
            return NoResource("No such container")

    @app.route("/<string:container_name>/<path:object_name>",
               methods=["GET"])
    def get_object(self, request, container_name, object_name):
        """
        Get an object from a container.
        """
        if container_name in self.containers:
            container = self.containers[container_name]
            if object_name in container.objects:
                obj = container.objects[object_name]

                def set_header_if_not_none(header_key, obj_value):
                    if obj_value is not None:
                        request.responseHeaders.setRawHeaders(
                            header_key, [obj_value.encode("ascii")])

                set_header_if_not_none(
                    b"content-type",
                    obj.content_type if obj.content_type is not None else
                    u"application/octet-stream")
                set_header_if_not_none(b"content-encoding", obj.content_encoding)
                set_header_if_not_none(b"etag", obj.etag)
                set_header_if_not_none(b"x-object-manifest", obj.object_manifest)
                set_header_if_not_none(b"x-object-meta-name", obj.object_meta_name)

                request.setResponseCode(200)
                return container.objects[object_name].data
            else:
                return NoResource("No such object in container")
        else:
            return NoResource("No such container")

    @app.route("/<string:container_name>/<path:object_name>",
               methods=["PUT"])
    def put_object(self, request, container_name, object_name):
        """
        Create or update an object in a container.
        """
        if container_name in self.containers:
            container = self.containers[container_name]

            def get_header_value(header_key):
                value = request.requestHeaders.getRawHeaders(header_key)
                if value is not None:
                    return value[0].decode("ascii")
                else:
                    return None

            content_type = get_header_value(b"content-type")
            content_encoding = get_header_value(b"content-encoding")
            etag = get_header_value(b"etag")
            object_manifest = get_header_value(b"x-object-manifest")
            object_meta_name = get_header_value(b"x-object-meta-name")

            container.objects[object_name] = Object(
                name=object_name,
                content_encoding=content_encoding,
                content_type=content_type,
                etag=etag,
                object_manifest=object_manifest,
                object_meta_name=object_meta_name,
                data=request.content.read()
            )
            request.setResponseCode(201)
            return b""
        else:
            return NoResource("No such container")

    @app.route("/<string:container_name>/<path:object_name>",
               methods=["DELETE"])
    def delete_object(self, request, container_name, object_name):
        """
        Delete an object in a container.
        """
        if container_name in self.containers:
            container = self.containers[container_name]
            if object_name in container.objects:
                del container.objects[object_name]
                request.setResponseCode(204)
                return b""
            else:
                return NoResource("No such object in container")
        else:
            return NoResource("No such container")
