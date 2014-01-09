"""
Defines the GET api call to the mimic api to fetch the presets
TO DO: SHould alos be able to chnage the presets using a PUT request
"""

import json
from twisted.web.server import Request
from mimic.canned_responses.mimic_presets import get_presets
from mimic.rest.mimicapp import MimicApp


Request.defaultContentType = 'application/json'


class MimicPresetApi(object):

    """
    Rest endpoints for mocked Load balancer api.
    """
    app = MimicApp()

    @app.route('/v1.0/mimic/presets', methods=['GET'])
    def get_mimic_presets(self, request):
        """
        Return the preset values for mimic
        """
        request.setResponseCode(200)
        return json.dumps(get_presets)
