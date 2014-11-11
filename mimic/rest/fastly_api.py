# -*- test-case-name: mimic.test.test_auth -*-
"""
Defines get current customer
"""

import json

from twisted.web.server import Request
from mimic.rest.mimicapp import MimicApp
from mimic.canned_responses import fastly

Request.defaultContentType = 'application/json'


class FastlyApi(object):
    """
    Rest endpoints for mocked Fastly api.
    """

    app = MimicApp()

    def __init__(self, core):
        """
        :param MimicCore core: The core to which this AuthApi will be
            authenticating.
        """
        self.core = core

    @app.route('/current_customer', methods=['GET'])
    def get_current_customer(self):
        """
        Returns response with random usernames.
        """
        response = fastly.get_current_customer()
        return json.dumps(response)
