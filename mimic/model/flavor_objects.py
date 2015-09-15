"""
Model objects for the flavors.
"""

from characteristic import attributes, Attribute
from json import dumps
from mimic.model.flavors import (
    RackspaceStandardFlavor, RackspaceComputeFlavor, RackspaceMemoryFlavor,
    RackspaceOnMetalFlavor, RackspaceIOFlavor, RackspaceGeneralFlavor,
    RackspacePerformance1Flavor, RackspacePerformance2Flavor)

from twisted.web.http import NOT_FOUND


@attributes(['nova_message'])
class BadRequestError(Exception):
    """
    Error to be raised when bad input has been received to Nova.
    """


def _nova_error_message(msg_type, message, status_code, request):
    """
    Set the response code on the request, and return a JSON blob representing
    a Nova error body, in the format Nova returns error messages.

    :param str msg_type: What type of error this is - something like
        "badRequest" or "itemNotFound" for Nova.
    :param str message: The message to include in the body.
    :param int status_code: The status code to set
    :param request: the request to set the status code on

    :return: dictionary representing the error body
    """
    request.setResponseCode(status_code)
    return {
        msg_type: {
            "message": message,
            "code": status_code
        }
    }


def not_found(message, request):
    """
    Return a 404 error body associated with a Nova not found error.
    Also sets the response code on the request.

    :param str message: The message to include in the bad request body.
    :param request: The request on which to set the response code.

    :return: dictionary representing the error body.
    """
    return _nova_error_message("itemNotFound", message, NOT_FOUND, request)


@attributes(
    ["tenant_id", "region_name", "clock",
     Attribute("flavors_store", default_factory=list)]
)
class RegionalFlavorCollection(object):
    """
    A collection of flavors, in a given region, for a given tenant.
    """
    def flavor_by_id(self, flavor_id):
        """
        Retrieve a :obj:`Flavor` object by its ID.
        """
        for flavor in self.flavors_store:
            if flavor.flavor_id == flavor_id:
                return flavor

    def create_flavors_list(self, flavor_classes):
        """
        Generates the data for each flavor in each flavor class
        """
        if len(self.flavors_store) < 1:
            for flavor_class in flavor_classes:
                for flavor, flavor_spec in flavor_class.flavors.iteritems():
                    if not self.flavor_by_id(flavor_spec['id']):
                        flavor_name = flavor
                        flavor_id = flavor_spec['id']
                        ram = flavor_spec['ram']
                        vcpus = flavor_spec['vcpus']
                        network = flavor_spec['rxtx_factor']
                        disk = flavor_spec['disk']
                        tenant_id = self.tenant_id
                        flavor = flavor_class(flavor_id=flavor_id, tenant_id=tenant_id,
                                              name=flavor_name, ram=ram, vcpus=vcpus,
                                              rxtx=network, disk=disk)
                        self.flavors_store.append(flavor)

    def list_flavors(self, include_details, absolutize_url):
        """
        Return a list of flavors with details.
        """
        flavors = [RackspaceStandardFlavor, RackspaceComputeFlavor, RackspacePerformance1Flavor,
                   RackspaceOnMetalFlavor, RackspacePerformance2Flavor, RackspaceMemoryFlavor,
                   RackspaceIOFlavor, RackspaceGeneralFlavor]
        self.create_flavors_list(flavors)
        flavors = []
        for flavor in self.flavors_store:
            if self.region_name != "IAD" and isinstance(flavor, RackspaceOnMetalFlavor):
                continue
            if include_details:
                flavors.append(flavor.detailed_json(absolutize_url))
            else:
                flavors.append(flavor.brief_json(absolutize_url))
        result = {"flavors": flavors}

        return dumps(result)

    def get_flavor(self, http_get_request, flavor_id, absolutize_url):
        """
        Return a flavor object if one exists from the list `/flavors` api,
        else creates and adds the flavor to the :obj: `flavors_store`.
        If the `flavor_id` is listed in `mimic.canned_responses.mimic_presets`,
        then will return 404.
        """
        flavor = self.flavor_by_id(flavor_id)
        if flavor is None:
            return dumps(not_found("The resource could not be found.",
                                   http_get_request))
        return dumps({"flavor": flavor.detailed_json(absolutize_url)})


@attributes(["tenant_id", "clock",
             Attribute("regional_collections", default_factory=dict)])
class GlobalFlavorCollections(object):
    """
    A :obj:`GlobalFlavorCollections` is a set of all the
    :obj:`RegionalFlavorCollection` objects owned by a given tenant.  In other
    words, all the flavor objects that a single tenant owns globally.
    """

    def collection_for_region(self, region_name):
        """
        Get a :obj:`RegionalFlavorCollection` for the region identified by the
        given name.
        """
        if region_name not in self.regional_collections:
            self.regional_collections[region_name] = (
                RegionalFlavorCollection(tenant_id=self.tenant_id, region_name=region_name,
                                         clock=self.clock))
        return self.regional_collections[region_name]
