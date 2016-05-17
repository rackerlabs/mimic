# -*- test-case-name: mimic.test.test_auth -*-
"""
Defines get token, impersonation
"""

from __future__ import absolute_import, division, unicode_literals

import json
import time
import uuid

import attr
from six import text_type

from twisted.python.urlpath import URLPath

from mimic.canned_responses.auth import (
    get_token,
    get_endpoints,
    format_timestamp,
    impersonator_user_role)
from mimic.canned_responses.mimic_presets import get_presets
from mimic.core import MimicCore
from mimic.model.behaviors import make_behavior_api
from mimic.model.identity import (
    APIKeyCredentials,
    ImpersonationCredentials,
    PasswordCredentials,
    TokenCredentials)
from mimic.model.identity_objects import (
    bad_request,
    conflict,
    not_found,
    unauthorized,
    ExternalApiStore,
    EndpointTemplateStore
)
from mimic.rest.mimicapp import MimicApp
from mimic.session import NonMatchingTenantError
from mimic.util.helper import (
    invalid_resource,
    seconds_to_timestamp,
    json_from_request,
)

from mimic.model.behaviors import (
    BehaviorRegistryCollection,
    Criterion,
    EventDescription,
    regexp_predicate
)

authentication = EventDescription()
"""
Event refers to authenticating against Identity using a username/password,
username/api-key, token, or getting an impersonation token.
"""


@authentication.declare_criterion("username")
def username_criterion(value):
    """
    Return a Criterion which matches the given regular expression string
    against the ``"username"`` attribute.
    """
    return Criterion(name='username', predicate=regexp_predicate(value))


@authentication.declare_criterion("tenant_id")
def tenant_id_criterion(value):
    """
    Return a Criterion which matches the given regular expression string
    against the ``"tenant_Id"`` attribute.
    """
    return Criterion(name='tenant_id', predicate=regexp_predicate(value))


@authentication.declare_default_behavior
def default_authentication_behavior(core, http_request, credentials):
    """
    Default behavior in response to a server creation.  This will create
    a session for the tenant if one does not already exist, and return
    the auth token for that session.  In the case of
    :class:`PasswordCredentials`, :class:`ApiKeyCredentials`, or
    :class:`TokenCredentials`, also returns the service catalog.

    :param core: An instance of :class:`mimic.core.MimicCore`
    :param http_request: A twisted http request/response object
    :param credentials: An `mimic.model.identity.ICredentials` provider

    Handles setting the response code and also
    :return: The response body for a default authentication request.
    """
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
        if type(credentials) == ImpersonationCredentials:
            return json.dumps({"access": {
                "token": {"id": credentials.impersonated_token,
                          "expires": format_timestamp(session.expires)}
            }})

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


@authentication.declare_behavior_creator("fail")
def authenticate_failure_behavior(parameters):
    """
    Create a failing behavior for authentication.

    Takes three parameters:

    ``"code"``, an integer describing the HTTP response code, and
    ``"message"``, a string describing a textual message.
    ``"type"``, a string representing what type of error message it is

    If ``type`` is "string", the message is just returned as the string body.
    Otherwise, the following JSON body will be synthesized (as per the
    canonical Nova error format):

    ```
    {
        <type>: {
            "message": <message>,
            "code": <code>
        }
    }

    The default type is unauthorized, the default code is 401, and the
    default message is
    "Unable to authenticate user with credentials provided."
    """
    def _fail(core, http_request, credentials):
        status_code = parameters.get("code", 401)
        http_request.setResponseCode(status_code)

        failure_type = parameters.get("type", "unauthorized")
        failure_message = parameters.get(
            "message",
            "Unable to authenticate user with credentials provided.")

        if failure_type == "string":
            return failure_message
        else:
            return json.dumps({
                failure_type: {
                    "message": failure_message,
                    "code": status_code
                }
            })

    return _fail


@attr.s(hash=False)
class IdentityApi(object):
    """
    Rest endpoints for mocked Auth api.

    :ivar core: an instance of :class:`mimic.core.MimicCore`
    :ivar registry_collection: an instance of
        :class:`mimic.model.behaviors.BehaviorRegistryCollection`
    """
    core = attr.ib(validator=attr.validators.instance_of(MimicCore))
    registry_collection = attr.ib(
        validator=attr.validators.instance_of(BehaviorRegistryCollection))
    app = MimicApp()

    @app.route('/v2.0/tokens', methods=['POST'])
    def get_token_and_service_catalog(self, request):
        """
        Return a service catalog consisting of all plugin endpoints and an api
        token.
        """
        try:
            content = json_from_request(request)
        except ValueError:
            pass
        else:
            for cred_type in (PasswordCredentials, APIKeyCredentials,
                              TokenCredentials):
                if cred_type.type_key in content['auth']:
                    try:
                        cred = cred_type.from_json(content)
                    except (KeyError, TypeError):
                        pass
                    else:
                        registry = self.registry_collection.registry_by_event(
                            authentication)
                        behavior = registry.behavior_for_attributes(
                            attr.asdict(cred))
                        return behavior(self.core, request, cred)

        request.setResponseCode(400)
        return json.dumps(invalid_resource("Invalid JSON request body"))

    @app.route('/v1.1/mosso/<string:tenant_id>', methods=['GET'])
    def get_username(self, request, tenant_id):
        """
        Returns response with random usernames.
        """
        request.setResponseCode(301)
        session = self.core.sessions.session_for_tenant_id(tenant_id)
        return json.dumps(dict(user=dict(id=session.username)))

    @app.route('/v2.0/users', methods=['GET'])
    def get_users_details(self, request):
        """
        Returns response with  detailed account information about each user
        including email, name, user ID, account configuration and status
        information.
        """
        username = request.args.get(b"name")[0].decode("utf-8")
        session = self.core.sessions.session_for_username_password(
            username, "test")
        return json.dumps(dict(user={
            "RAX-AUTH:domainId": session.tenant_id,
            "id": session.user_id,
            "enabled": True,
            "username": session.username,
            "email": "thisisrandom@email.com",
            "RAX-AUTH:defaultRegion": "ORD",
            "created": seconds_to_timestamp(time.time()),
            "updated": seconds_to_timestamp(time.time())
        }))

    @app.route('/v2.0/users/<string:user_id>/OS-KSADM/credentials/RAX-KSKEY:apiKeyCredentials',
               methods=['GET'])
    def rax_kskey_apikeycredentials(self, request, user_id):
        """
        Support, such as it is, for the apiKeysCredentials call.
        """
        if user_id in self.core.sessions._userid_to_session:
            username = self.core.sessions._userid_to_session[user_id].username
            apikey = '7fc56270e7a70fa81a5935b72eacbe29'  # echo -n A | md5sum
            return json.dumps({'RAX-KSKEY:apiKeyCredentials': {'username': username,
                                                               'apiKey': apikey}})
        else:
            return json.dumps(not_found(
                              'User ' + user_id + ' not found',
                              request))

    @app.route('/v2.0/RAX-AUTH/impersonation-tokens', methods=['POST'])
    def get_impersonation_token(self, request):
        """
        Return a token id with expiration.
        """
        request.setResponseCode(200)
        try:
            content = json_from_request(request)
        except ValueError:
            request.setResponseCode(400)
            return json.dumps(invalid_resource("Invalid JSON request body"))

        x_auth_token = request.getHeader(b"x-auth-token")
        if x_auth_token is not None:
            x_auth_token = x_auth_token.decode("utf-8")
        cred = ImpersonationCredentials.from_json(content, x_auth_token)
        registry = self.registry_collection.registry_by_event(authentication)
        behavior = registry.behavior_for_attributes({
            "token": cred.impersonator_token,
            "username": cred.impersonated_username
        })
        return behavior(self.core, request, cred)

    @app.route('/v2.0/tokens/<string:token_id>', methods=['GET'])
    def validate_token(self, request, token_id):
        """
        Creates a new session for the given tenant_id and token_id
        and always returns response code 200.
        Docs: http://developer.openstack.org/api-ref-identity-v2.html#admin-tokens
        """
        request.setResponseCode(200)
        tenant_id = request.args.get(b'belongsTo')
        if tenant_id is not None:
            tenant_id = tenant_id[0].decode("utf-8")
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
            # weird mix between an unauthorized (401) and not_found (404)
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

        # Canned responses to be removed ...

        if token_id in get_presets["identity"]["non_dedicated_observer"]:
                response["access"]["token"]["tenant"] = {
                    "id": "135790",
                    "name": "135790",
                }
                response["access"]["user"] = {
                    "id": "12",
                    "name": "OneTwo",
                    "roles": [{"id": "1",
                               "name": "monitoring:observer",
                               "description": "Monitoring Observer"}]
                }

        if token_id in get_presets["identity"]["non_dedicated_admin"]:
                response["access"]["token"]["tenant"] = {
                    "id": "135790",
                    "name": "135790",
                }
                response["access"]["user"] = {
                    "id": "34",
                    "name": "ThreeFour",
                    "roles": [{"id": "1",
                               "name": "monitoring:admin",
                               "description": "Monitoring Admin"},
                              {"id": "2",
                               "name": "admin",
                               "description": "Admin"}]
                }

        if token_id in get_presets["identity"]["non_dedicated_impersonator"]:
                response["access"]["token"]["tenant"] = {
                    "id": "135790",
                    "name": "135790",
                }
                response["access"]["user"] = {
                    "id": "34",
                    "name": "ThreeFour",
                    "roles": [{"id": "1",
                               "name": "identity:nobody",
                               "description": "Nobody"}]
                }
                response["access"]["RAX-AUTH:impersonator"] = {
                    "id": response["access"]["user"]["id"],
                    "name": response["access"]["user"]["name"],
                    "roles": [{"id": "1",
                               "name": "monitoring:service-admin"},
                              {"id": "2",
                               "name": "object-store:admin"}]
                }

        if token_id in get_presets["identity"]["non_dedicated_racker"]:
                response["access"]["token"]["tenant"] = {
                    "id": "135790",
                    "name": "135790",
                }
                response["access"]["user"] = {
                    "id": "34",
                    "name": "ThreeFour",
                    "roles": [{"id": "1",
                               "name": "identity:nobody",
                               "description": "Nobody"}]
                }
                response["access"]["RAX-AUTH:impersonator"] = {
                    "id": response["access"]["user"]["id"],
                    "name": response["access"]["user"]["name"],
                    "roles": [{"id": "1",
                               "name": "Racker"}]
                }

        if token_id in get_presets["identity"]["dedicated_full_device_permission_holder"]:
                response["access"]["token"]["tenant"] = {
                    "id": "hybrid:123456",
                    "name": "hybrid:123456",
                }
                response["access"]["user"] = {
                    "id": "12",
                    "name": "HybridOneTwo",
                    "roles": [{"id": "1",
                               "name": "monitoring:observer",
                               "tenantId": "hybrid:123456"}],
                    "RAX-AUTH:contactId": "12"
                }

        if token_id in get_presets["identity"]["dedicated_account_permission_holder"]:
                response["access"]["token"]["tenant"] = {
                    "id": "hybrid:123456",
                    "name": "hybrid:123456",
                }
                response["access"]["user"] = {
                    "id": "34",
                    "name": "HybridThreeFour",
                    "roles": [{"id": "1",
                               "name": "monitoring:creator",
                               "description": "Monitoring Creator"},
                              {"id": "2",
                               "name": "creator",
                               "description": "Creator"}],
                    "RAX-AUTH:contactId": "34"
                }

        if token_id in get_presets["identity"]["dedicated_limited_device_permission_holder"]:
                response["access"]["token"]["tenant"] = {
                    "id": "hybrid:123456",
                    "name": "hybrid:123456",
                }
                response["access"]["user"] = {
                    "id": "56",
                    "name": "HybridFiveSix",
                    "roles": [{"id": "1",
                               "name": "monitoring:observer",
                               "description": "Monitoring Observer"},
                              {"id": "2",
                               "name": "observer",
                               "description": "Observer"}],
                    "RAX-AUTH:contactId": "56"
                }

        if token_id in get_presets["identity"]["dedicated_racker"]:
                response["access"]["token"]["tenant"] = {
                    "id": "hybrid:123456",
                    "name": "hybrid:123456",
                }
                response["access"]["user"] = {
                    "id": "12",
                    "name": "HybridOneTwo",
                    "roles": [{"id": "1",
                               "name": "identity:nobody",
                               "description": "Nobody"}],
                    "RAX-AUTH:contactId": "12"
                }
                response["access"]["RAX-AUTH:impersonator"] = {
                    "id": response["access"]["user"]["id"],
                    "name": response["access"]["user"]["name"],
                    "roles": [{"id": "1",
                               "name": "Racker"}]
                }

        if token_id in get_presets["identity"]["dedicated_impersonator"]:
                response["access"]["token"]["tenant"] = {
                    "id": "hybrid:123456",
                    "name": "hybrid:123456",
                }
                response["access"]["user"] = {
                    "id": "34",
                    "name": "HybridThreeFour",
                    "roles": [{"id": "1",
                               "name": "identity:nobody",
                               "description": "Nobody"}],
                    "RAX-AUTH:contactId": "34"
                }
                response["access"]["RAX-AUTH:impersonator"] = {
                    "id": response["access"]["user"]["id"],
                    "name": response["access"]["user"]["name"],
                    "roles": [{"id": "1",
                               "name": "monitoring:service-admin"}]
                }

        if token_id in get_presets["identity"]["dedicated_non_permission_holder"]:
                response["access"]["token"]["tenant"] = {
                    "id": "hybrid:123456",
                    "name": "hybrid:123456",
                }
                response["access"]["user"] = {
                    "id": "78",
                    "name": "HybridSevenEight",
                    "roles": [{"id": "1",
                               "name": "identity:user-admin",
                               "description": "User admin"}],
                    "RAX-AUTH:contactId": "78"
                }

        if token_id in get_presets["identity"]["dedicated_quasi_user_impersonator"]:
                response["access"]["token"]["tenant"] = {
                    "id": "hybrid:123456",
                    "name": "hybrid:123456",
                }
                response["access"]["user"] = {
                    "id": "90",
                    "name": "HybridNineZero",
                    "roles": [{"id": "1",
                               "name": "identity:user-admin",
                               "description": "Admin"},
                              {"id": "3",
                               "name": "hybridRole",
                               "description": "Hybrid Admin",
                               "tenantId": "hybrid:123456"}]
                }
                response["access"]["RAX-AUTH:impersonator"] = {
                    "id": response["access"]["user"]["id"],
                    "name": response["access"]["user"]["name"],
                    "roles": [{"id": "1",
                               "name": "monitoring:service-admin"}]
                }

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

    @app.route('/v2.0/tenants', methods=['GET'])
    def list_tenants(self, request):
        """
        List all tenants for the specified auth token.

        The token for this call is specified in the X-Auth-Token header,
        like using the services in the service catalog. Mimic supports
        only one tenant per session, so the number of listed tenants is
        always 1 if the call succeeds.

        For more information about this call, refer to the `Rackspace Cloud
        Identity Developer Guide
        <https://developer.rackspace.com/docs/cloud-identity/v2/developer-guide/#list-tenants>`_
        """
        try:
            sess = self.core.sessions.existing_session_for_token(
                request.getHeader(b'x-auth-token').decode('utf-8'))
            return json.dumps({'tenants': [{'id': sess.tenant_id,
                                            'name': sess.tenant_id,
                                            'enabled': True}]})
        except KeyError:
            request.setResponseCode(401)
            return json.dumps({'unauthorized': {
                'code': 401,
                'message': ("No valid token provided. Please use the 'X-Auth-Token'"
                            " header with a valid token.")}})

    @app.route('/v2.0/MIMIC-OSKSCATALOG/services', methods=['GET'])
    def list_external_api_services(self, request):
        """
        List the available external services that endpoint templates
        may be added to.

        Note: MIMIC-OSKSCATALOG is a Mimic specific administrative extension
            for managing services in the Service Catalog that are not
            hosted by Mimic internally. These services are manageable
            via the Keystone OS-KSCATALOG administrative extension.
        """
        x_auth_token = request.getHeader(b"x-auth-token")
        if x_auth_token is None:
            return json.dumps(unauthorized("Authentication required", request))

        request.setResponseCode(200)
        return json.dumps({
            "MIMIC-OS-KSCATALOG": [
                {
                    "name": api.name_key,
                    "type": api.type_key,
                    "id": api.uuid_key
                }
                for api in [
                    self.core.get_external_api(api_name)
                    for api_name in self.core.get_external_apis()]]})

    @app.route('/v2.0/MIMIC-OSKSCATALOG/services', methods=['POST'])
    def create_external_api_service(self, request):
        """
        Create a new external api service that endpoint templates
        may be added to.

        Note: MIMIC-OSKSCATALOG is a Mimic specific administrative extension
            for managing services in the Service Catalog that are not
            hosted by Mimic internally. These services are manageable
            via the Keystone OS-KSCATALOG administrative extension.

        Note: Only requires 'name' and 'type' fields in the JSON. If the 'id'
            field is present, it will use it; otherwise a UUID4 will be
            assigned.
        """
        x_auth_token = request.getHeader(b"x-auth-token")
        if x_auth_token is None:
            return json.dumps(unauthorized("Authentication required", request))

        try:
            content = json_from_request(request)
        except ValueError:
            return json.dumps(bad_request("Invalid JSON request body", request))

        try:
            service_name = content['name']
            service_type = content['type']
        except KeyError:
            return json.dumps(
                bad_request(
                    "Invalid Content. 'name' and 'type' fields are required.",
                    request))

        try:
            service_id = content['id']
        except KeyError:
            service_id = text_type(uuid.uuid4())

        if service_name in self.core.get_external_apis():
            return json.dumps(
                conflict(
                    "Conflict: Service with the same name already exists.",
                    request))

        self.core.add_api(ExternalApiStore(
            service_id,
            service_name,
            service_type))
        request.setResponseCode(201)
        return b''

    @app.route('/v2.0/MIMIC-OSKSCATALOG/services', methods=['DELETE'])
    def delete_external_api_service(self, request):
        """
        Delete/Remove an existing  external service api. It must not have
        any endpoint templates assigned to it for success.

        Note: MIMIC-OSKSCATALOG is a Mimic specific administrative extension
            for managing services in the Service Catalog that are not
            hosted by Mimic internally. These services are manageable
            via the Keystone OS-KSCATALOG administrative extension.

        Note: Requires 'name', 'id', and 'type' fields in the JSON.
        """
        x_auth_token = request.getHeader(b"x-auth-token")
        if x_auth_token is None:
            return json.dumps(unauthorized("Authentication required", request))

        try:
            content = json_from_request(request)
        except ValueError:
            return json.dumps(bad_request("Invalid JSON request body", request))

        try:
            service_name = content['name']
            service_type = content['type']
            service_id = content['id']
        except KeyError:
            return json.dumps(
                bad_request(
                    "Invalid Content. 'id', 'name', and 'type' fields are required.",
                    request))

        try:
            self.core.remove_external_api(
                service_id,
                service_type,
                service_name
            )
        except IndexError:
            return json.dumps(
                not_found(
                    "Service not found. Unable to remove.",
                    request))
        except ValueError:
            return json.dumps(
                conflict(
                    "Service still has endpoint templates.",
                    request))
        else:
            request.setResponseCode(204)
            return b''

    @app.route('/v2.0/OS-KSCATALOG/endpointTemplates', methods=['GET'])
    def list_endpoint_templates(self, request):
        """
        List the available endpoint templates.

        Reference: http://developer.openstack.org/api-ref-identity-v2-ext.html

        Note: Marker/Limit capability not implemented here.
        """
        x_auth_token = request.getHeader(b"x-auth-token")
        if x_auth_token is None:
            return json.dumps(unauthorized("Authentication required", request))

        # caller may provide a specific API to list by setting the
        # serviceid header
        external_apis_to_list = []
        service_id = request.getHeader(b'serviceid')
        if service_id is not None:
            external_apis_to_list = [service_id.decode('utf-8')]
        else:
            external_apis_to_list = [
                api_name
                for api_name in self.core.get_external_apis()
            ]

        try:
            data = []
            request.setResponseCode(200)
            for api_name in external_apis_to_list:
                api = self.core.get_external_api(api_name)
                for endpoint_template in api.list_templates():
                    data.append(endpoint_template.serialize())
            request.setHeader('X-Service-Count', len(data))
            request.setHeader('X-API-Count', len(external_apis_to_list))
            request.setHeader('X-Core-API-Count',
                              len(self.core._uuid_to_api_external))
            return json.dumps(
                {
                    "OS-KSCATALOG": data
                }
            )
        except IndexError:
            request.setResponseCode(404)
            return json.dumps(not_found(
                "Unable to find the requested API",
                request))

    @app.route('/v2.0/OS-KSCATALOG/endpointTemplates', methods=['POST'])
    def add_endpoint_templates(self, request):
        """
        Add an API endpoint template to the system. By default the API
        described by the template will disabled for all users.

        Reference: http://developer.openstack.org/api-ref-identity-v2-ext.html

        Note: Either the service-id must be specified in the header or
            a Service Name by the same name must already exist. Otherwise
            a Not Found (404) will be returned.

        Note: A template has certain required parametes. For Mimic the
            id, name, type, and region parameters are required. See
            EndpointTemplateStore.required_mapping for details. Other
            implementations may have different requirements.
        """
        x_auth_token = request.getHeader(b"x-auth-token")
        if x_auth_token is None:
            return json.dumps(unauthorized("Authentication required", request))

        try:
            content = json_from_request(request)
        except ValueError:
            return json.dumps(
                bad_request("Invalid JSON request body", request)
            )

        try:
            endpoint_template_instance = EndpointTemplateStore(
                template_dict=content
            )
        except KeyError:
            return json.dumps(
                bad_request(
                    "JSON body does not contain the required parameters: "
                    + text_type(
                        [key
                         for key, _ in EndpointTemplateStore.required_mapping]
                    ),
                    request
                )
            )

        service_name = endpoint_template_instance.name_key

        try:
            service = self.core.get_external_api(service_name)
        except IndexError:
            return json.dumps(
                not_found(
                    "Service API for endoint template not found",
                    request
                )
            )

        try:
            service.add_template(endpoint_template_instance)
        except ValueError:
            return json.dumps(
                conflict(
                    "Endpoint already exists or service type does not match.",
                    request
                )
            )
        else:
            request.setResponseCode(201)
            return b''

    @app.route('/v2.0/OS-KSCATALOG/endpointTemplates', methods=['PUT'])
    def update_endpoint_templates(self, request):
        """
        Update an API endpoint template already in the system.

        Reference: http://developer.openstack.org/api-ref-identity-v2-ext.html

        Note: A template by the same id must already exist in the system.

        Note: Either the service-id must be specified in the header or
            a Service Name by the same name must already exist. Otherwise
            a Not Found (404) will be returned.
        """
        x_auth_token = request.getHeader(b"x-auth-token")
        if x_auth_token is None:
            return json.dumps(unauthorized("Authentication required", request))

        try:
            content = json_from_request(request)
        except ValueError:
            return json.dumps(
                bad_request("Invalid JSON request body", request)
            )

        try:
            endpoint_template_instance = EndpointTemplateStore(
                template_dict=content
            )
        except KeyError:
            return json.dumps(
                bad_request(
                    "JSON body does not contain the required parameters: "
                    + text_type(
                        [key
                         for key, _ in EndpointTemplateStore.required_mapping]
                    ),
                    request
                )
            )

        service_name = endpoint_template_instance.name_key

        try:
            service = self.core.get_external_api(service_name)
        except IndexError:
            return json.dumps(
                not_found(
                    "Service API for endoint template not found",
                    request
                )
            )

        try:
            service.update_template(endpoint_template_instance)
        except ValueError:
            return json.dumps(
                conflict(
                    "Endpoint already exists and service id or service type "
                    "does not match.",
                    request
                )
            )
        except IndexError:
            return json.dumps(
                not_found(
                    "Unable to update non-existent template. Template must "
                    "first be added before it can be updated.",
                    request
                )
            )
        else:
            request.setResponseCode(201)
            return b''

    @app.route('/v2.0/OS-KSCATALOG/endpointTemplates', methods=['DELETE'])
    def delete_endpoint_templates(self, request):
        """
        Delete an endpoint API template from the system.

        Reference: http://developer.openstack.org/api-ref-identity-v2-ext.html

        Note: Either the service-id must be specified in the header or
            a Service Name by the same name must already exist. Otherwise
            a Not Found (404) will be returned.
        """
        x_auth_token = request.getHeader(b"x-auth-token")
        if x_auth_token is None:
            return json.dumps(unauthorized("Authentication required", request))


def base_uri_from_request(request):
    """
    Given a request, return the base URI of the request

    :param request: a twisted HTTP request
    :type request: :class:`twisted.web.http.Request`

    :return: the base uri the request was trying to access
    :rtype: ``str``
    """
    return str(URLPath.fromRequest(request).click(b'/'))


AuthControlApiBehaviors = make_behavior_api({'auth': authentication})
"""
Handlers for CRUD operations on authentication behaviors.

:ivar registry_collection: an instance of
    :class:`mimic.model.behaviors.BehaviorRegistryCollection`
"""
