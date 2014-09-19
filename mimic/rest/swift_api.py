# -*- test-case-name: mimic.test.test_swift -*-

"""
API mock for OpenStack Swift / Rackspace Cloud Files.
"""

from uuid import uuid4, uuid5, NAMESPACE_URL
from six import text_type

from characteristic import attributes
from json import dumps

from mimic.imimic import IAPIMock
from twisted.plugin import IPlugin
from twisted.web.http import CREATED, ACCEPTED, OK

from mimic.catalog import Entry
from mimic.catalog import Endpoint
from mimic.rest.mimicapp import MimicApp
from zope.interface import implementer


def normal_tenant_id_to_crazy_mosso_id(normal_tenant_id):
    """
    Convert the tenant ID used by basically everything else (keystone, nova,
    loadbalancers, and so on) into the somewhat peculiar tenant ID used by
    Cloud Files, for maximum realism.

    :return: a new tenant ID that looks like a Cloud Files tenant ID
    :rtype: str
    """
    return (
        "MossoCloudFS_" +
        str(uuid5(NAMESPACE_URL,
                  b"https://github.com/rackerlabs/mimic/ns/tenant/"
                  + normal_tenant_id.encode("utf-8")))
    )


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
        if tenant_id is not None:
            modified = self.translate_tenant(tenant_id)
        else:
            modified = None
        return [
            Entry(modified, "object-store", "cloudFiles", [
                Endpoint(modified, "ORD", text_type(uuid4()), prefix="v1"),
            ])
        ]

    def resource_for_region(self, region, uri_prefix, session_store):
        """
        Return an IResource implementing a public Swift region endpoint.
        """
        return SwiftRegion(uri_prefix=uri_prefix).app.resource()


@attributes("uri_prefix".split())
class SwiftRegion(object):
    """
    :obj:`SwiftRegion` is a set of klein routes and application representing a
    Swift endpoint.
    """

    app = MimicApp()

    # global for now, fix this with per-session state
    tenants_in_regions = {
        # map (uri_prefix, tenant_id) to SwiftTenantInRegion
    }

    @app.route("/v1/<string:tenant_id>", branch=True)
    def get_one_tenant_resource(self, request, tenant_id):
        """
        Get a resource for a tenant in this region.
        """
        key = (self.uri_prefix, tenant_id)
        if key not in self.tenants_in_regions:
            self.tenants_in_regions[tenant_id] = (
                SwiftTenantInRegion().app.resource())
        return self.tenants_in_regions[tenant_id]


@attributes("name".split())
class Container(object):
    """
    Create a container object.
    """


class SwiftTenantInRegion(object):
    """
    A :obj:`SwiftTenantInRegion` represents a single tenant and their
    associated storage resources within one region.
    """
    # TODO: The lifecycle of this object is wrong, we need to store it on a
    # session of some kind so that created containers will persist beyond the
    # individual HTTP request where they're created.

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
        request.setRawHeaders("content-type", ["application/json"])
        request.setResponseCode(OK)
        return dumps([])
