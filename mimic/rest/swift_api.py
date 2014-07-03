"""
API mock for OpenStack Swift / Rackspace Cloud Files™.
"""

from uuid import uuid4, uuid5
from six import text_type

from characteristic import attributes

from mimic.imimic import IAPIMock
from twisted.plugin import IPlugin
from twisted.web.http import CREATED, ACCEPTED, NO_CONTENT, OK

from mimic.catalog import Entry
from mimic.catalog import Endpoint
from mimic.rest.mimicapp import MimicApp
from zope.interface import implementer

def normal_tenant_id_to_crazy_mosso_id(normal_tenant_id):
    """
    Convert the tenant ID used by basically everything else (keystone, nova,
    loadbalancers, and so on) into the somewhat peculiar tenant ID used by
    Cloud Files, for maximum realism.
    """
    return (
        "MossoCloudFS_" +
        str(uuid5("urn:whatever:openstack:swift:tenant", normal_tenant_id))
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
        Catalog entry for
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

    def resource_for_region(self, uri_prefix):
        """
        Return an IResource implementing a public Swift region endpoint.
        """
        return SwiftRegion(uri_prefix).app.resource()


@attributes("uri_prefix")
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
                SwiftTenantInRegion(tenant_id).app.resource())
        return self.tenants_in_regions[tenant_id]


class SwiftTenantInRegion(object):
    """
    
    """

    app = MimicApp()

    def __init__(self, ):
        """
        
        """
        self.containers = {}


    @app.route("/<string:container_name>", methods=["PUT"])
    def create_container(self, request, container_name):
        """
        
        """
        if container_name not in self.containers:
            self.containers[container_name] = Container()
            request.setResponseCode(CREATED)
        else:
            request.setResponseCode(ACCEPTED)
        return b""


    @app.route("/<string:container_name>", methods=["GET"])
    def get_container(self, request, container_name):
        """
        
        """
        request.setRawHeaders("content-type", ["application/json"])
        request.setResponseCode(OK)
        return dumps([])

