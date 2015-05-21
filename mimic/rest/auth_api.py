# -*- test-case-name: mimic.test.test_auth -*-
"""
Defines get token, impersonation
"""
import json
import attr

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
    ImpersonationCredentials,
    PasswordCredentials,
    TokenCredentials)
from mimic.rest.mimicapp import MimicApp
from mimic.session import NonMatchingTenantError
from mimic.util.helper import invalid_resource

Request.defaultContentType = 'application/json'


from mimic.model.behaviors import (
    BehaviorRegistry, EventDescription, Criterion, regexp_predicate
)


authentication = EventDescription()
"""
Event refers to authenticating against Identity using a username/password,
username/api-key, token, or getting an impersonation token.
"""


# These Could be automated, but the docstrings are not all the same

@authentication.declare_criterion("tenant_id")
def tenant_id_criterion(value):
    """
    Return a Criterion which matches the given regular expression string
    against the ``"tenant_id"`` attribute.  Used for username/password,
    username/api_key, or token authentication requests.  This would match
    against authentication parameter ``"tenantName"`` or ``"tenantId"``, since
    both are conceptually the "tenant ID".
    """
    return Criterion(name='tenant_id', predicate=regexp_predicate(value))


@authentication.declare_criterion("username")
def username_criterion(value):
    """
    Return a Criterion which matches the given regular expression string
    against the ``"username"`` attribute.  Used for username/password,
    username/api_key, or impersonation authentication requests.
    """
    return Criterion(name='username', predicate=regexp_predicate(value))


@authentication.declare_criterion("password")
def password_criterion(value):
    """
    Return a Criterion which matches the given regular expression string
    against the ``"password"`` attribute.  Used for username/password
    authentication requests.
    """
    return Criterion(name='password', predicate=regexp_predicate(value))


@authentication.declare_criterion("api_key")
def api_key_criterion(value):
    """
    Return a Criterion which matches the given regular expression string
    against the ``"api_key"`` attribute.  Used for username/api_key
    authentication requests.
    """
    return Criterion(name='api_key', predicate=regexp_predicate(value))


@authentication.declare_criterion("token")
def token_criterion(value):
    """
    Return a Criterion which matches the given regular expression string
    against the ``"token"`` attribute.  Used for token or
    impersonation (in the form of the x-auth-token header) authentication
    requests.
    """
    return Criterion(name='token', predicate=regexp_predicate(value))


@authentication.declare_default_behavior
def default_authentication_behavior(core, http_request, credentials):
    """
    Default behavior in response to a server creation.

    :param core: An instance of :class:`mimic.core.MimicCore`
    :param http_request: A twisted http request/response object
    :param credentials: An `mimic.model.identity.ICredentials` provider
    """
    if type(credentials) in (
            APIKeyCredentials, PasswordCredentials, TokenCredentials):
        try:
            session = credentials.get_session(core.sessions)
        except NonMatchingTenantError as e:
            http_request.setResponseCode(401)
            if type(credentials) == TokenCredentials:
                message = ("Token doesn't belong to Tenant with Id/Name: "
                           "'{0}'".format(e.desired_tenant))
            else:
                message = ("Tenant with Name/Id: '{0}' is not valid for "
                           "User '{1}' (id: '{2}')".format(
                               e.desired_tenant,
                               e.session.username,
                               e.session.user_id))

            return json.dumps({
                "unauthorized": {
                    "code": 401,
                    "message": message
                }
            })
        else:
            http_request.setResponseCode(200)
            prefix_map = {
                # map of entry to URI prefix for that entry
            }

            def lookup(entry):
                return prefix_map[entry]
            result = get_token(
                session.tenant_id,
                entry_generator=lambda tenant_id:
                list(core.entries_for_tenant(
                     session.tenant_id, prefix_map,
                     base_uri_from_request(http_request))),
                prefix_for_endpoint=lookup,
                response_token=session.token,
                response_user_id=session.user_id,
                response_user_name=session.username,
            )
            return json.dumps(result)
    else:
        session = credentials.get_session(core.sessions)
        return json.dumps({"access": {
            "token": {"id": credentials.impersonated_token,
                      "expires": format_timestamp(session.expires)}
        }})


@attr.s(hash=False)
class AuthApi(object):
    """
    Rest endpoints for mocked Auth api.
    """
    core = attr.ib()
    auth_behavior_registry = attr.ib(default=attr.Factory(
        lambda: BehaviorRegistry(event=authentication)))

    app = MimicApp()

    @app.route('/v2.0/tokens', methods=['POST'])
    def get_token_and_service_catalog(self, request):
        """
        Return a service catalog consisting of all plugin endpoints and an api
        token.
        """
        try:
            content = json.loads(request.content.read())
        except ValueError:
            pass
        else:
            if "auth" in content and 0 < len(content['auth']) <= 2:
                for key, cred_type in (
                        ('passwordCredentials', PasswordCredentials),
                        ('RAX-KSKEY:apiKeyCredentials', APIKeyCredentials),
                        ("token", TokenCredentials)):
                    if key in content['auth']:
                        try:
                            creds = cred_type.from_json(content)
                        except Exception:
                            pass
                        else:
                            behavior = (self.auth_behavior_registry
                                        .behavior_for_attributes(
                                            attr.asdict(creds)))
                            return behavior(self.core, request, creds)

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
            creds = ImpersonationCredentials.from_json(
                content, request.getHeader("x-auth-token"))
        except Exception:
            pass
        else:
            behavior = self.auth_behavior_registry.behavior_for_attributes(
                attr.asdict(creds))
            return behavior(self.core, request, creds)

        request.setResponseCode(400)
        return json.dumps(
            invalid_resource("Invalid JSON request body"))

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
