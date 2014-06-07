# -*- test-case-name: mimic.test.test_auth -*-
"""
Defines get token, impersonation
"""

import json
from twisted.web.server import Request
from mimic.canned_responses.auth import get_token, get_endpoints
from mimic.rest.mimicapp import MimicApp
from mimic.canned_responses.auth import format_timestamp

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
        self.core = core

    @app.route('/v2.0/tokens', methods=['POST'])
    def get_service_catalog_and_token(self, request):
        """
        Return a service catalog consisting of nova and load balancer mocked
        endpoints and an api token.
        """
        content = json.loads(request.content.read())
        # tenant_id = content['auth'].get('tenantName', None)
        credentials = content['auth']['passwordCredentials']
        session = self.core.session_for_username_password(
            credentials['username'], credentials['password'],
            content['auth'].get('tenantName', None),
        )
        request.setResponseCode(200)
        prefix_map = {
            # map of entry to URI prefix for that entry
        }
        def lookup(entry):
            return prefix_map[entry]
        return json.dumps(
            get_token(
                session.tenant_id,
                entry_generator=lambda tenant_id:
                list(self.core.entries_for_tenant(tenant_id, prefix_map)),
                prefix_for_entry=lookup,
                response_token=session.token,
                response_user_id=session.user_id,
                response_user_name=session.username,
            )
        )

    @app.route('/v1.1/mosso/<string:tenant_id>', methods=['GET'])
    def get_username(self, request, tenant_id):
        """
        Returns response with random usernames.
        """
        # FIXME: TEST
        request.setResponseCode(301)
        session = self.core.session_for_tenant_id(tenant_id)
        return json.dumps(dict(user=dict(id=session.username)))

    @app.route('/v2.0/RAX-AUTH/impersonation-tokens', methods=['POST'])
    def get_impersonation_token(self, request):
        """
        Return a token id with expiration.
        """
        # FIXME: TEST
        request.setResponseCode(200)
        content = json.loads(request.content.read())
        expires_in = content['RAX-AUTH:impersonation']['expire-in-seconds']
        username = content['RAX-AUTH:impersonation']['user']['username']

        session = self.core.session_for_impersonation(username, expires_in)
        return json.dumps({"access": {
            "token": {"id": session.token,
                      "expires": format_timestamp(session.expires)}
        }})

    @app.route('/v2.0/tokens/<string:token_id>/endpoints', methods=['GET'])
    def get_service_catalog(self, request, token_id):
        """
        Return a service catalog consisting of nova and load balancer mocked
        endpoints.
        """
        # FIXME: TEST
        request.setResponseCode(200)
        prefix_map = {}
        return json.dumps(get_endpoints(
            token_id,
            entry_generator=lambda tenant_id: list(
                self.core.entries_for_tenant(tenant_id, prefix_map)),
            prefix_for_entry=prefix_map.get)
        )
