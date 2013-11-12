"""
Defines get token, impersonation
"""

import json
from twisted.web.server import Request
from mimic.canned_responses.auth import (get_token, get_user,
                                         get_user_token, get_endpoints)
from mimic.rest.mimicapp import MimicApp

Request.defaultContentType = 'application/json'


class AuthApi(object):

    """
    Rest endpoints for mocked Auth api.
    """
    app = MimicApp()

    @app.route('/v2.0/tokens', methods=['POST'])
    def get_service_catalog_and_token(self, request):
        """
        Return a service catalog consisting of nova and load balancer mocked
        endpoints and an api token.
        """
        request.setResponseCode(200)
        return json.dumps(get_token)

    @app.route('/v1.1/mosso/<string:tenant_id>', methods=['GET'])
    def get_username(self, request, tenant_id):
        """
        Returns response with username 'autoscaleprod.
        """
        request.setResponseCode(301)
        return json.dumps(get_user())

    @app.route('/v2.0/RAX-AUTH/impersonation-tokens', methods=['POST'])
    def get_user_token(self, request):
        """
        Return a token id with expiration.
        """
        request.setResponseCode(200)
        content = json.loads(request.content.read())
        expires_in = content['RAX-AUTH:impersonation']['expire-in-seconds']
        return json.dumps(get_user_token(expires_in))

    @app.route('/v2.0/tokens/<string:token_id>/endpoints', methods=['GET'])
    def get_service_catalog(self, request, token_id):
        """
        Return a service catalog consisting of nova and load balancer mocked
        endpoints.
        """
        request.setResponseCode(200)
        return json.dumps(get_endpoints())
