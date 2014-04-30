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

    @app.route('/v2.0/tokens', methods=['POST'])
    def get_service_catalog_and_token(self, request):
        """
        Return a service catalog consisting of nova and load balancer mocked
        endpoints and an api token.
        """
        content = json.loads(request.content.read())

	#need to the credential type like RAX-KSKEY:apiKeyCredentials or passwordCredentials
	#Then we can get the username so we can determine what response to send back.
	credential_key = content['auth'].keys()
        try:
            #tenant_id = content['auth']['tenantName']
	    auth_user_name = content['auth'][credential_key[0]]['username']
            tenant_id = '123456789'
        except KeyError:
            auth_user_name = 'user-admin'
            tenant_id = '123456789'
        request.setResponseCode(200)
	return json.dumps(get_token(tenant_id,auth_user_name))

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
