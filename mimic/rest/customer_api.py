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

        Until the contacts are set by the `POST` call, this returns the default
        contacts for a tenant.
        """
        response = self.core.contacts_store.list_contacts_for_tenant(tenant_id)
        return json.dumps(response)

    @app.route('/<string:tenant_id>/contacts', methods=['POST'])
    def add_customer_contacts_for_tenant(self, request, tenant_id):
        """
        Adds new contacts to a tenant and responds with a 200.

        Note: If there is a GET on the tenant before this `POST` call, the default
        contacts would have been listed. This POST will overwrite the existing contacts
        and only set the contacts provided.
        """
        content = json.loads(request.content.read())
        contact_list = [(each_contact["email"], each_contact["role"]) for each_contact in content]
        self.core.contacts_store.add_to_contacts_store(tenant_id, contact_list)
        return b''
