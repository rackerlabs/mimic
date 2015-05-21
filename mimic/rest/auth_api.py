# -*- test-case-name: mimic.test.test_auth -*-
"""
Defines get token, impersonation
"""
import json
from six import text_type
from uuid import uuid4

from twisted.web.server import Request
from twisted.python.urlpath import URLPath
from mimic.canned_responses.auth import (
    get_token,
    get_endpoints,
    format_timestamp,
    impersonator_user_role)
from mimic.canned_responses.mimic_presets import get_presets
from mimic.model.identity import (
    APIKeyCredentials,
    PasswordCredentials,
    TokenCredentials)
from mimic.rest.mimicapp import MimicApp
from mimic.session import NonMatchingTenantError
from mimic.util.helper import invalid_resource

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

        def format_response(cred, nonmatching_tenant_message_generator):
            try:
                session = cred.get_session(self.core.sessions)
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
                         session.tenant_id,
                         prefix_map, base_uri_from_request(request))),
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

        cred_mappings = {
            'passwordCredentials':
                (PasswordCredentials, username_generator),
            'RAX-KSKEY:apiKeyCredentials':
                (APIKeyCredentials, username_generator),
            'token':
                (TokenCredentials,
                 lambda e: (
                     "Token doesn't belong to Tenant with Id/Name: "
                     "'{0}'".format(e.desired_tenant)))
        }

        relevant_cred_keys = set(cred_mappings).intersection(
            set(content['auth']))

        if relevant_cred_keys:
            cred_type, error_handler = cred_mappings[relevant_cred_keys.pop()]
            try:
                cred = cred_type.from_json(content)
            except Exception:
                pass
            else:
                return format_response(cred, error_handler)

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
        impersonator_token = request.getHeader("x-auth-token")
        expires_in = content['RAX-AUTH:impersonation']['expire-in-seconds']
        username = content['RAX-AUTH:impersonation']['user']['username']
        impersonated_token = 'impersonated_token_' + text_type(uuid4())
        session = self.core.sessions.session_for_impersonation(username,
                                                               expires_in,
                                                               impersonator_token,
                                                               impersonated_token)

        return json.dumps({"access": {
            "token": {"id": impersonated_token,
                      "expires": format_timestamp(session.expires)}
        }})

    @app.route('/v2.0/tokens/<string:token_id>', methods=['GET'])
    def validate_token(self, request, token_id):
        """
        Creates a new session for the given tenant_id and token_id
        and always returns response code 200.
        Docs: http://developer.openstack.org/api-ref-identity-v2.html#admin-tokens
        """
        request.setResponseCode(200)
        tenant_id = request.args.get('belongsTo')
        if tenant_id is not None:
            tenant_id = tenant_id[0]
        session = self.core.sessions.session_for_tenant_id(tenant_id, token_id)
        response = get_token(
            session.tenant_id,
            response_token=session.token,
            response_user_id=session.user_id,
            response_user_name=session.username,
        )
        if session.impersonator_session_for_token(token_id) is not None:
            impersonator_session = session.impersonator_session_for_token(token_id)
            response["access"]["RAX-AUTH:impersonator"] = impersonator_user_role(
                impersonator_session.user_id,
                impersonator_session.username)

        if token_id in get_presets["identity"]["token_fail_to_auth"]:
            request.setResponseCode(401)
            return json.dumps({'itemNotFound':
                              {'code': 401, 'message': 'Invalid auth token'}})

        imp_token = get_presets["identity"]["maas_admin_roles"]
        racker_token = get_presets["identity"]["racker_token"]
        if token_id in imp_token:
            response["access"]["RAX-AUTH:impersonator"] = {
                "id": response["access"]["user"]["id"],
                "name": response["access"]["user"]["name"],
                "roles": [{"id": "123",
                           "name": "monitoring:service-admin"},
                          {"id": "234",
                           "name": "object-store:admin"}]}
        if token_id in racker_token:
            response["access"]["RAX-AUTH:impersonator"] = {
                "id": response["access"]["user"]["id"],
                "name": response["access"]["user"]["name"],
                "roles": [{"id": "9",
                           "name": "Racker"}]}
        if tenant_id in get_presets["identity"]["observer_role"]:
            response["access"]["user"]["roles"] = [
                {"id": "observer",
                 "description": "Global Observer Role.",
                 "name": "observer"}]
        if tenant_id in get_presets["identity"]["creator_role"]:
            response["access"]["user"]["roles"] = [
                {"id": "creator",
                 "description": "Global Creator Role.",
                 "name": "creator"}]
        if tenant_id in get_presets["identity"]["admin_role"]:
            response["access"]["user"]["roles"] = [
                {"id": "admin",
                 "description": "Global Admin Role.",
                 "name": "admin"},
                {"id": "observer",
                 "description": "Global Observer Role.",
                 "name": "observer"}]
        return json.dumps(response)

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
