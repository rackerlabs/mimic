# -*- test-case-name: mimic.test.test_customer -*-
"""
API Mock for the Customer API.
"""

import json

from mimic.rest.mimicapp import MimicApp


class CustomerApi(object):
    """
    Rest endpoints for mocked Customer api.
    """

    app = MimicApp()

    def __init__(self, core):
        """
        :param MimicCore core: The core to which this Customer Api will be
        communicating.
        """
        self.core = core

    @app.route('/<string:tenant_id>/contacts', methods=['GET'])
    def get_customer_contacts_for_tenant(self, request, tenant_id):
        """
        Responds with code 200 and returns a list of contacts for the given tenant.

        Note: The control plane for the customer api allows one to set specific
        conatact details for a tenant that will be returned by this `GET` call.
        """
        return json.dumps({"tenant_id": tenant_id})
