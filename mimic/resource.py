"""
Resources for Mimic's core.
"""

import json
from mimic.canned_responses.mimic_presets import get_presets
from mimic.rest.mimicapp import MimicApp
from mimic.rest.auth_api import AuthApi

class MimicRoot(object):

    app = MimicApp()

    def __init__(self, core):
        """
        :param core: ???
        """
        self.core = core


    @app.route("/identity", branch=True)
    def get_auth_api(self, request):
        """
        Get the identity ...
        """
        return AuthApi(self.core).app.resource()


    @app.route('/mimic/v1.0/presets', methods=['GET'])
    def get_mimic_presets(self, request):
        """
        Return the preset values for mimic
        """
        request.setResponseCode(200)
        return json.dumps(get_presets)


    @app.route("/<region_name>/<service_id>", branch=True)
    def get_service_resource(self, request, region_name, service_id):
        """
        Based on the URL prefix of a region and a service, where the region is
        an identifier (like ORD, DFW, etc) and service is a
        dynamically-generated UUID for a particular plugin, retrieve the
        resource associated with that service.
        """
        serviceObject = self.core.service_with_region(region_name, service_id)
        return serviceObject
