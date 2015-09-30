# -*- test-case-name: mimic.test.test_valkyrie -*-
"""
API Mock for Valkyrie.
"""

from mimic.rest.mimicapp import MimicApp


class ValkyrieApi(object):
    """
    Rest endpoints for the Valkyrie API.
    """

    app = MimicApp()

    def __init__(self, core):
        """
        :param MimicCore core: The core to which the Valkyrie Api will be
        communicating.
        """
        self.core = core

    @app.route('/login', methods=['POST'])
    def login(self, request):
        """
        Responds with response code 200 and returns an auth token
        See https://valkyrie.my.rackspace.com/#authentication
        """
        return self.core.valkyrie_store.create_token(request)

    @app.route('/login_user', methods=['POST'])
    def login_user(self, request):
        """
        Responds with response code 200 and returns an auth token
        See https://valkyrie.my.rackspace.com/#authentication
        """
        return self.core.valkyrie_store.create_token(request)

    effective_any_permissions_route = ('/account/<int:account_number>'
                                       '/permissions/contacts/any'
                                       '/by_contact/<int:contact_id>/effective')

    @app.route(effective_any_permissions_route, methods=['GET'])
    def effective_any_permissions(self, request, account_number, contact_id):
        """
        Responds with response code 200 and returns a list of all permissions
        for the given account and contact
        See https://valkyrie.my.rackspace.com/#managed-accounts
        """
        return self.core.valkyrie_store.get_permissions(request,
                                                        account_number, contact_id, None)

    effective_accounts_permissions_route = ('/account/<int:account_number>'
                                            '/permissions/contacts/accounts'
                                            '/by_contact/<int:contact_id>/effective')

    @app.route(effective_accounts_permissions_route, methods=['GET'])
    def effective_accounts_permissions(self, request, account_number, contact_id):
        """
        Responds with response code 200 and returns a list of account level permissions
        for the given account and contact
        See https://valkyrie.my.rackspace.com/#managed-accounts
        """
        return self.core.valkyrie_store.get_permissions(request,
                                                        account_number, contact_id, 1)

    effective_devices_permissions_route = ('/account/<int:account_number>'
                                           '/permissions/contacts/devices'
                                           '/by_contact/<int:contact_id>/effective')

    @app.route(effective_devices_permissions_route, methods=['GET'])
    def effective_devices_permissions(self, request, account_number, contact_id):
        """
        Responds with response code 200 and returns a list of device level permissions
        for the given account and contact
        See https://valkyrie.my.rackspace.com/#managed-accounts
        """
        return self.core.valkyrie_store.get_permissions(request,
                                                        account_number, contact_id, 2)
