"""
Defines get token, impersonation
"""

import json
from twisted.web.server import Request
from mimic.canned_responses.auth import (get_token, get_user,
                                         get_user_token, get_endpoints)
from mimic.rest.mimicapp import MimicApp
from twisted.python import log

Request.defaultContentType = 'application/json'


class AuthApi(object):
    """
    Rest endpoints for mocked Auth api.
    """

    app = MimicApp()

    def __init__(self, core):
        """
        :param MimicCore core: The core to which this AuthApi will be
            authenticating.
        """
        print("AuthApi created...")
        self.core = core

    @app.route('/v2.0/tokens', methods=['POST'])
    def get_service_catalog_and_token(self, request):
        """
        Return a service catalog consisting of nova and load balancer mocked
        endpoints and an api token.
        """
        print("Getting service catalog...")
        content = json.loads(request.content.read())
        print("Loaded content...")
        try:
            tenant_id = content['auth']['tenantName']
        except KeyError:
            tenant_id = 'test'
        request.setResponseCode(200)
        prefix_map = {
            # map of entry to URI prefix for that entry
        }
        return json.dumps(
            get_token(
                tenant_id,
                entry_generator=lambda tenant_id:
                self.core.entries_for_tenant(tenant_id, prefix_map,
                                             "http://localhost:8900/service/"),
                prefix_for_entry=prefix_map.get,
            )
        )

    @app.route('/v1.1/mosso/<string:tenant_id>', methods=['GET'])
    def get_username(self, request, tenant_id):
        """
        Returns response with random usernames.
        """
        request.setResponseCode(301)
        return json.dumps(get_user(tenant_id))

    @app.route('/v2.0/RAX-AUTH/impersonation-tokens', methods=['POST'])
    def get_user_token(self, request):
        """
        Return a token id with expiration.
        """
        request.setResponseCode(200)
        content = json.loads(request.content.read())
        log.msg(content)
        expires_in = content['RAX-AUTH:impersonation']['expire-in-seconds']
        username = content['RAX-AUTH:impersonation']['user']['username']
        return json.dumps(get_user_token(expires_in, username))

    @app.route('/v2.0/tokens/<string:token_id>/endpoints', methods=['GET'])
    def get_service_catalog(self, request, token_id):
        """
        Return a service catalog consisting of nova and load balancer mocked
        endpoints.
        """
        request.setResponseCode(200)
        return json.dumps(get_endpoints(token_id))
