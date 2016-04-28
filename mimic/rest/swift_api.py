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
from twisted.web.resource import NoResource
from zope.interface import implementer


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
                Endpoint(modified, "ORD", text_type(uuid4()), prefix="v1"),
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
    data = attr.ib()

    def as_json(self):
        """
        Create a JSON-serializable representation of the contents of this
        object.
        """
        return {
            "name": self.name,
            "content_type": self.content_type,
            "bytes": len(self.data),
        }


@attr.s
class Container(object):
    """
    A Swift container (collection of :obj:`Object`.)
    """
    name = attr.ib()
    objects = attr.ib(default=attr.Factory(dict))


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

    @app.route("/<string:container_name>", methods=["GET"])
    def get_container(self, request, container_name):
        """
        Api call to get a container, given the name of the container.  HTTP
        status code of 200 when such a container exists, 404 if not.
        """
        if container_name in self.containers:
            request.responseHeaders.setRawHeaders(b"content-type",
                                                  [b"application/json"])
            request.responseHeaders.setRawHeaders(b"x-container-object-count",
                                                  [b"0"])
            request.responseHeaders.setRawHeaders(b"x-container-bytes-used",
                                                  [b"0"])
            request.setResponseCode(OK)
            return dumps([
                obj.as_json() for obj in
                self.containers[container_name].objects.values()
            ])
        else:
            return NoResource()

    @app.route("/<string:container_name>/<string:object_name>",
               methods=["GET"])
    def get_object(self, request, container_name, object_name):
        """
        Get an object from a container.
        """
        return self.containers[container_name].objects[object_name].data

    @app.route("/<string:container_name>/<string:object_name>",
               methods=["PUT"])
    def put_object(self, request, container_name, object_name):
        """
        Create or update an object in a container.
        """
        request.setResponseCode(201)
        container = self.containers[container_name]
        content_type = (request.requestHeaders
                        .getRawHeaders(b'content-type')[0].decode("ascii"))
        container.objects[object_name] = Object(
            name=object_name, data=request.content.read(),
            content_type=content_type
        )
        return b''
