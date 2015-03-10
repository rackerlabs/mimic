# -*- test-case-name: mimic.test.test_auth -*-
"""
Defines get token, impersonation
"""

import json

from twisted.web.server import Request
from twisted.python.urlpath import URLPath
from mimic.canned_responses.auth import get_token, get_endpoints
from mimic.rest.mimicapp import MimicApp
from mimic.canned_responses.auth import format_timestamp
from mimic.util.helper import invalid_resource
from mimic.session import NonMatchingTenantError

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
    def get_token_and_service_catalog(self, request):
        """
        Return a service catalog consisting of all plugin endpoints and an api
        token.
        """
        try:
            content = json.loads(request.content.read())
        except ValueError:
            request.setResponseCode(400)
            return json.dumps(invalid_resource("Invalid JSON request body"))

        tenant_id = (content['auth'].get('tenantName', None) or
                     content['auth'].get('tenantId', None))

        def format_response(callable_returning_session,
                            nonmatching_tenant_message_generator):
            try:
                session = callable_returning_session()
            except NonMatchingTenantError as e:
                request.setResponseCode(401)
                return json.dumps({
                    "unauthorized": {
                        "code": 401,
                        "message": nonmatching_tenant_message_generator(e)
                    }
                })
            else:
                request.setResponseCode(200)
                prefix_map = {
                    # map of entry to URI prefix for that entry
                }

                def lookup(entry):
                    return prefix_map[entry]
                result = get_token(
                    session.tenant_id,
                    entry_generator=lambda tenant_id:
                    list(self.core.entries_for_tenant(
                         tenant_id, prefix_map, base_uri_from_request(request))),
                    prefix_for_endpoint=lookup,
                    response_token=session.token,
                    response_user_id=session.user_id,
                    response_user_name=session.username,
                )
                return json.dumps(result)

        username_generator = (
            lambda exception: "Tenant with Name/Id: '{0}' is not valid for "
                              "User '{1}' (id: '{2}')".format(
                                  exception.desired_tenant,
                                  exception.session.username,
                                  exception.session.user_id))

        if content['auth'].get('passwordCredentials'):
            username = content['auth']['passwordCredentials']['username']
            password = content['auth']['passwordCredentials']['password']
            return format_response(
                lambda: self.core.sessions.session_for_username_password(
                    username, password, tenant_id),
                username_generator)

        elif content['auth'].get('RAX-KSKEY:apiKeyCredentials'):
            username = content['auth']['RAX-KSKEY:apiKeyCredentials'][
                'username']
            api_key = content['auth']['RAX-KSKEY:apiKeyCredentials'][
                'apiKey']
            return format_response(
                lambda: self.core.sessions.session_for_api_key(
                    username, api_key, tenant_id),
                username_generator)

        elif content['auth'].get('token') and tenant_id:
            token = content['auth']['token']['id']
            return format_response(
                lambda: self.core.sessions.session_for_token(token,
                                                             tenant_id),
                lambda e: "Token doesn't belong to Tenant with Id/Name: "
                          "'{0}'".format(e.desired_tenant))
        else:
            request.setResponseCode(400)
            return json.dumps(
                invalid_resource("Invalid JSON request body"))

    @app.route('/v1.1/mosso/<string:tenant_id>', methods=['GET'])
    def get_username(self, request, tenant_id):
        """
        Returns response with random usernames.
        """
        request.setResponseCode(301)
        session = self.core.sessions.session_for_tenant_id(tenant_id)
        return json.dumps(dict(user=dict(id=session.username)))

    @app.route('/v2.0/users/<string:user_id>/OS-KSADM/credentials/RAX-KSKEY:apiKeyCredentials',
               methods=['GET'])
    def rax_kskey_apikeycredentials(self, request, user_id):
        """
        Support, such as it is, for the apiKeysCredentials call.
        """
        if user_id in self.core.sessions._userid_to_session:
            username = self.core.sessions._userid_to_session[user_id].username.decode('ascii')
            apikey = '7fc56270e7a70fa81a5935b72eacbe29'  # echo -n A | md5sum
            return json.dumps({'RAX-KSKEY:apiKeyCredentials': {'username': username,
                               'apiKey': apikey}})
        else:
            request.setResponseCode(404)
            return json.dumps({'itemNotFound':
                              {'code': 404, 'message': 'User ' + user_id + ' not found'}})

    @app.route('/v2.0/RAX-AUTH/impersonation-tokens', methods=['POST'])
    def get_impersonation_token(self, request):
        """
        Return a token id with expiration.
        """
        request.setResponseCode(200)
        try:
            content = json.loads(request.content.read())
        except ValueError:
            request.setResponseCode(400)
            return json.dumps(invalid_resource("Invalid JSON request body"))

        expires_in = content['RAX-AUTH:impersonation']['expire-in-seconds']
        username = content['RAX-AUTH:impersonation']['user']['username']

        session = self.core.sessions.session_for_impersonation(username,
                                                               expires_in)
        return json.dumps({"access": {
            "token": {"id": session.token,
                      "expires": format_timestamp(session.expires)}
        }})

    @app.route('/v2.0/tokens/<string:token_id>/endpoints', methods=['GET'])
    def get_endpoints_for_token(self, request, token_id):
        """
        Return a service catalog consisting of nova and load balancer mocked
        endpoints.
        """
        # FIXME: TEST
        request.setResponseCode(200)
        prefix_map = {}
        session = self.core.sessions.session_for_token(token_id)
        return json.dumps(get_endpoints(
            session.tenant_id,
            entry_generator=lambda tenant_id: list(
                self.core.entries_for_tenant(tenant_id, prefix_map,
                                             base_uri_from_request(request))),
            prefix_for_endpoint=prefix_map.get)
        )


def base_uri_from_request(request):
    """
    Given a request, return the base URI of the request

    :param request: a twisted HTTP request
    :type request: :class:`twisted.web.http.Request`

    :return: the base uri the request was trying to access
    :rtype: ``str``
    """
    return str(URLPath.fromRequest(request).click('/'))
