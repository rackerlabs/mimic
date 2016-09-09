# -*- test-case-name: mimic.test.test_auth -*-
"""
Defines get token, impersonation
"""

from __future__ import absolute_import, division, unicode_literals

import binascii
import json
import os
import time
import uuid

import attr
from six import text_type

from twisted.python.urlpath import URLPath

from mimic.canned_responses.auth import (
    get_token,
    get_endpoints,
    format_timestamp,
    impersonator_user_role,
    get_version_v2)
from mimic.canned_responses.mimic_presets import get_presets
from mimic.core import (
    MimicCore,
    ServiceDoesNotExist,
    ServiceHasTemplates,
    ServiceNameExists
)
from mimic.model.behaviors import make_behavior_api
from mimic.model.identity import (
    APIKeyCredentials,
    ImpersonationCredentials,
    PasswordCredentials,
    TokenCredentials)
from mimic.model.identity_errors import (
    EndpointTemplateAlreadyExists,
    EndpointTemplateDisabledForTenant,
    EndpointTemplateDoesNotExist,
    InvalidEndpointTemplateId,
    InvalidEndpointTemplateMissingKey,
    InvalidEndpointTemplateServiceType
)
from mimic.model.identity_objects import (
    bad_request,
    conflict,
    EndpointTemplateStore,
    ExternalApiStore,
    not_found
)
from mimic.rest.decorators import require_auth_token
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
    :ivar apikey_length: the string length of any generated apikeys
    """
    core = attr.ib(validator=attr.validators.instance_of(MimicCore))
    registry_collection = attr.ib(
        validator=attr.validators.instance_of(BehaviorRegistryCollection))
    app = MimicApp()

    apikey_length = 32

    @classmethod
    def make_apikey(cls):
        """
        Generate an API key
        """
        # length of the final APIKey value
        generation_length = int(cls.apikey_length / 2)
        return text_type(
            binascii.hexlify(os.urandom(generation_length)).decode('utf-8')
        )

    @app.route('/v2.0', methods=['GET'])
    def get_version(self, request):
        """
        Returns keystone version.
        """
        base_uri = base_uri_from_request(request)
        return json.dumps(get_version_v2(base_uri))

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

    @app.route('/v2.0/users/<string:user_id>/OS-KSADM/credentials',
               methods=['GET'])
    def get_user_credentials_osksadm(self, request, user_id):
        """
        Support, such as it is, for the credentials call.

        `OpenStack Identity v2 Extension List Credentials
        <http://developer.openstack.org/api-ref-identity-v2-ext.html#listCredentials>`_
        """
        if user_id in self.core.sessions._userid_to_session:
            username = self.core.sessions._userid_to_session[user_id].username
            apikey = self.make_apikey()
            return json.dumps(
                {
                    'credentials': [
                        {
                            'RAX-KSKEY:apiKeyCredentials': {
                                'username': username,
                                'apiKey': apikey
                            }
                        }
                    ],
                    "credentials_links": []
                }
            )
        else:
            request.setResponseCode(404)
            return json.dumps({'itemNotFound':
                              {'code': 404, 'message': 'User ' + user_id + ' not found'}})

    @app.route('/v2.0/users/<string:user_id>/OS-KSADM/credentials/RAX-KSKEY:apiKeyCredentials',
               methods=['GET'])
    def rax_kskey_apikeycredentials(self, request, user_id):
        """
        Support, such as it is, for the apiKeysCredentials call.

        reference: https://developer.rackspace.com/docs/cloud-identity/v2/api-reference/users-operations/#get-user-credentials  # noqa
        """
        if user_id in self.core.sessions._userid_to_session:
            username = self.core.sessions._userid_to_session[user_id].username
            apikey = self.make_apikey()
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
        `OpenStack Identity v2 Admin Validate Token
        <http://developer.openstack.org/api-ref-identity-admin-v2.html#admin-validateToken>`_
        """
        request.setResponseCode(200)
        session = None

        # Attempt to get the session based on tenant_id+token if the optional
        # tenant_id is provided; if tenant_id is not provided, then just look
        # it up based on the token.
        tenant_id = request.args.get(b'belongsTo')
        if tenant_id is not None:
            tenant_id = tenant_id[0].decode("utf-8")
            session = self.core.sessions.session_for_tenant_id(
                tenant_id, token_id)

        else:
            session = self.core.sessions.session_for_token(
                token_id
            )

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
            # This is returning a 401 Unauthorized message but in a 404 not_found
            # JSON data format. Is there a reason for this? An old OpenStack bug?
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

        `OpenStack Identity v2 Admin Endpoints for Token
        <http://developer.openstack.org/api-ref/identity/v2-admin/#list-endoints-for-token>`_
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

    @app.route('/v2.0/services', methods=['GET'])
    @require_auth_token
    def list_external_api_services(self, request):
        """
        List the available external services that endpoint templates
        may be added to.

        .. note:: Does not implement the limits or markers.
        `OpenStack Identity v2 OS-KSADM List Services
        <http://developer.openstack.org/api-ref/identity/v2-ext/index.html#list-services-admin-extension>`_
        """
        request.setResponseCode(200)
        return json.dumps({
            "OS-KSADM:services": [
                {
                    "name": api.name_key,
                    "type": api.type_key,
                    "id": api.uuid_key,
                    "description": api.description
                }
                for api in [
                    self.core.get_external_api(api_id)
                    for api_id in self.core.get_external_apis()]]})

    @app.route('/v2.0/services', methods=['POST'])
    @require_auth_token
    def create_external_api_service(self, request):
        """
        Create a new external api service that endpoint templates
        may be added to.

        .. note:: Only requires 'name' and 'type' fields in the JSON. If the 'id'
            or 'description' fields are present, then they will be used;
            otherwise a UUID4 will be assigned to the 'id' field and the
            'description' will be given a generic value.
        `OpenStack Identity v2 OS-KSADM Create Service
        <http://developer.openstack.org/api-ref/identity/v2-ext/index.html#create-service-admin-extension>`_
        """
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

        try:
            service_description = content['description']
        except KeyError:
            service_description = u"External API referenced by Mimic"

        if service_id in self.core.get_external_apis():
            return json.dumps(
                conflict(
                    "Conflict: Service with the same uuid already exists.",
                    request))

        try:
            self.core.add_api(ExternalApiStore(
                service_id,
                service_name,
                service_type,
                description=service_description))
        except ServiceNameExists:
            return json.dumps(
                conflict(
                    "Conflict: Service with the same name already exists.",
                    request))
        else:
            request.setResponseCode(201)
            return b''

    @app.route('/v2.0/services/<string:service_id>', methods=['DELETE'])
    @require_auth_token
    def delete_external_api_service(self, request, service_id):
        """
        Delete/Remove an existing  external service api. It must not have
        any endpoint templates assigned to it for success.

        `OpenStack Identity v2 OS-KSADM Delete Service
        <http://developer.openstack.org/api-ref/identity/v2-ext/index.html#delete-service-admin-extension>`_
        """
        try:
            self.core.remove_external_api(
                service_id
            )
        except ServiceDoesNotExist:
            return json.dumps(
                not_found(
                    "Service not found. Unable to remove.",
                    request))
        except ServiceHasTemplates:
            return json.dumps(
                conflict(
                    "Service still has endpoint templates.",
                    request))
        else:
            request.setResponseCode(204)
            return b''

    @app.route('/v2.0/OS-KSCATALOG/endpointTemplates', methods=['GET'])
    @require_auth_token
    def list_endpoint_templates(self, request):
        """
        List the available endpoint templates.

        .. note:: Marker/Limit capability not implemented here.

        `OpenStack Identity v2 OS-KSCATALOG List Endpoint Templates
        <http://developer.openstack.org/api-ref-identity-v2-ext.html>`_
        """
        # caller may provide a specific API to list by setting the
        # serviceid header
        external_apis_to_list = []
        service_id = request.getHeader(b'serviceid')
        if service_id is not None:
            external_apis_to_list = [service_id.decode('utf-8')]
        else:
            external_apis_to_list = [
                api_id
                for api_id in self.core.get_external_apis()
            ]

        try:
            data = []
            request.setResponseCode(200)
            for api_id in external_apis_to_list:
                api = self.core.get_external_api(api_id)
                for endpoint_template in api.list_templates():
                    data.append(endpoint_template.serialize())

            return json.dumps(
                {
                    "OS-KSCATALOG": data,
                    "OS-KSCATALOG:endpointsTemplates_links": []
                }
            )
        except ServiceDoesNotExist:
            request.setResponseCode(404)
            return json.dumps(not_found(
                "Unable to find the requested API",
                request))

    @app.route('/v2.0/OS-KSCATALOG/endpointTemplates', methods=['POST'])
    @require_auth_token
    def add_endpoint_templates(self, request):
        """
        Add an API endpoint template to the system. By default the API
        described by the template will disabled for all users.

        .. note:: Either the service-id must be specified in the header or
            a Service Name by the same name must already exist. Otherwise
            a Not Found (404) will be returned.

        .. note:: A template has certain required parametes. For Mimic the
            id, name, type, and region parameters are required. See
            EndpointTemplateStore.required_mapping for details. Other
            implementations may have different requirements.

        `OpenStack Identity v2 OS-KSCATALOG Create Endpoint Template
        <http://developer.openstack.org/api-ref-identity-v2-ext.html>`_
        """
        try:
            content = json_from_request(request)
        except ValueError:
            return json.dumps(
                bad_request("Invalid JSON request body", request)
            )

        try:
            endpoint_template_instance = EndpointTemplateStore.deserialize(
                content
            )
        except InvalidEndpointTemplateMissingKey as ex:
            return json.dumps(
                bad_request(
                    "JSON body does not contain the required parameters: "
                    + text_type(ex),
                    request
                )
            )

        # Access the Service ID that tells which External API
        # is to support this template.
        service_id = request.getHeader(b'serviceid')
        if service_id is not None:
            service_id = service_id.decode('utf-8')

        # Check all existing External APIs for the API ID
        # to ensure that none of them contain it already. The
        # value must be unique.
        for api_id in self.core.get_external_apis():
            api = self.core.get_external_api(api_id)
            if api.has_template(endpoint_template_instance.id_key):
                return json.dumps(
                    conflict(
                        "ID value is already assigned to an existing template",
                        request
                    )
                )

            # While we're at it, if we need to look up the service ID
            # and find the External API that will ultimately provide it
            # then grab that too instead of repeating the search.
            elif api.name_key == endpoint_template_instance.name_key:
                if service_id is None:
                    service_id = api.uuid_key

        try:
            service = self.core.get_external_api(service_id)
        except ServiceDoesNotExist:
            return json.dumps(
                not_found(
                    "Service API for endoint template not found",
                    request
                )
            )

        try:
            service.add_template(endpoint_template_instance)
        except (EndpointTemplateAlreadyExists,
                InvalidEndpointTemplateServiceType):
            return json.dumps(
                conflict(
                    "Endpoint already exists or service type does not match.",
                    request
                )
            )
        else:
            request.setResponseCode(201)
            return b''

    @app.route('/v2.0/OS-KSCATALOG/endpointTemplates/<string:template_id>',
               methods=['PUT'])
    @require_auth_token
    def update_endpoint_templates(self, request, template_id):
        """
        Update an API endpoint template already in the system.

        .. note:: A template by the same id must already exist in the system.

        .. note:: Either the service-id must be specified in the header or
            a Service Name by the same name must already exist. Otherwise
            a Not Found (404) will be returned.

        `OpenStack Identity v2 OS-KSCATALOG Update Endpoint Template
        <http://developer.openstack.org/api-ref-identity-v2-ext.html>`_
        """
        try:
            content = json_from_request(request)
        except ValueError:
            return json.dumps(
                bad_request("Invalid JSON request body", request)
            )

        try:
            if content['id'] != template_id:
                return json.dumps(
                    conflict(
                        "Template ID in URL does not match that of the JSON body",
                        request
                    )
                )

            endpoint_template_instance = EndpointTemplateStore.deserialize(
                content
            )
        except (InvalidEndpointTemplateMissingKey, KeyError) as ex:
            # KeyError is for the content['id'] line
            return json.dumps(
                bad_request(
                    "JSON body does not contain the required parameters: "
                    + text_type(ex),
                    request
                )
            )

        service_id = request.getHeader(b'serviceid')
        if service_id is None:
            for api_id in self.core.get_external_apis():
                api = self.core.get_external_api(api_id)
                if api.has_template(template_id):
                    service_id = api.uuid_key
        else:
            service_id = service_id.decode('utf-8')

        try:
            service = self.core.get_external_api(service_id)
        except ServiceDoesNotExist:
            return json.dumps(
                not_found(
                    "Service API for endoint template not found",
                    request
                )
            )

        try:
            service.update_template(endpoint_template_instance)
        except (InvalidEndpointTemplateServiceType,
                InvalidEndpointTemplateId):
            return json.dumps(
                conflict(
                    "Endpoint already exists and service id or service type "
                    "does not match.",
                    request
                )
            )
        except EndpointTemplateDoesNotExist:
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

    @app.route('/v2.0/OS-KSCATALOG/endpointTemplates/<string:template_id>',
               methods=['DELETE'])
    @require_auth_token
    def delete_endpoint_templates(self, request, template_id):
        """
        Delete an endpoint API template from the system.

        .. note:: Either the service-id must be specified in the header or
            a Service Name by the same name must already exist. Otherwise
            a Not Found (404) will be returned.

        `OpenStack Identity v2 OS-KSCATALOG Delete Endpoint Template
        <http://developer.openstack.org/api-ref-identity-v2-ext.html>`_
        """
        service_id = request.getHeader(b'serviceid')
        if service_id is not None:
            api = self.core.get_external_api(service_id.decode('utf-8'))
            if api.has_template(template_id):
                api.remove_template(template_id)
                request.setResponseCode(204)
                return b''
        else:
            for api_id in self.core.get_external_apis():
                api = self.core.get_external_api(api_id)
                if api.has_template(template_id):
                    api.remove_template(template_id)
                    request.setResponseCode(204)
                    return b''

        return json.dumps(
            not_found(
                "Unable to locate an External API with the given Template ID.",
                request
            )
        )

    @app.route('/v2.0/tenants/<string:tenant_id>/OS-KSCATALOG/endpoints',
               methods=['GET'])
    @require_auth_token
    def list_endpoints_for_tenant(self, request, tenant_id):
        """
        List the available endpoints for a given tenant-id.

        .. note:: Marker/Limit capability not implemented here.

        `OpenStack Identity v2 OS-KSCATALOG List Endpoints for Tenant
        <http://developer.openstack.org/api-ref-identity-v2-ext.html>`_
        """
        # caller may provide a specific API to list by setting the
        # serviceid header
        external_apis_to_list = []
        service_id = request.getHeader(b'serviceid')
        if service_id is not None:
            external_apis_to_list = [service_id.decode('utf-8')]
        else:
            external_apis_to_list = [
                api_id
                for api_id in self.core.get_external_apis()
            ]

        try:
            data = []
            request.setResponseCode(200)
            for api_id in external_apis_to_list:
                api = self.core.get_external_api(api_id)
                for endpoint_template in api.list_tenant_templates(tenant_id):
                    data.append(
                        endpoint_template.serialize(
                            tenant_id
                        )
                    )

            return json.dumps(
                {
                    "endpoints": data,
                    "endpoints_links": []
                }
            )
        except ServiceDoesNotExist:
            request.setResponseCode(404)
            return json.dumps(not_found(
                "Unable to find the requested API",
                request))

    @app.route('/v2.0/tenants/<string:tenant_id>/OS-KSCATALOG/endpoints',
               methods=['POST'])
    @require_auth_token
    def create_endpoint_for_tenant(self, request, tenant_id):
        """
        Enable a given endpoint template for a given tenantid.

        `OpenStack Identity v2 OS-KSCATALOG Create Endpoint for Tenant
        <http://developer.openstack.org/api-ref-identity-v2-ext.html>`_
        """
        try:
            content = json_from_request(request)
        except ValueError:
            return json.dumps(
                bad_request("Invalid JSON request body", request)
            )

        try:
            template_id = content['OS-KSCATALOG:endpointTemplate']['id']
        except KeyError:
            return json.dumps(
                bad_request(
                    "Invalid Content. OS-KSCATALOG:endpointTemplate:id is "
                    "required.",
                    request))

        for api_id in self.core.get_external_apis():
            api = self.core.get_external_api(api_id)
            if api.has_template(template_id):
                api.enable_endpoint_for_tenant(
                    tenant_id,
                    template_id
                )
                request.setResponseCode(201)
                return b''

        return json.dumps(
            not_found(
                "Unable to locate an External API with the given Template ID.",
                request
            )
        )

    @app.route('/v2.0/tenants/<string:tenant_id>/OS-KSCATALOG/endpoints/'
               '<string:template_id>', methods=['DELETE'])
    @require_auth_token
    def remove_endpoint_for_tenant(self, request, tenant_id, template_id):
        """
        Disable a given endpoint template for a given tenantid if it's been
        enabled. This does not affect an endpoint template that has been
        globally enabled.

        `OpenStack Identity v2 OS-KSCATALOG Delete Endpoint for Tenant
        <http://developer.openstack.org/api-ref-identity-v2-ext.html>`_
        """
        for api_id in self.core.get_external_apis():
            api = self.core.get_external_api(api_id)
            if api.has_template(template_id):
                try:
                    api.disable_endpoint_for_tenant(
                        tenant_id,
                        template_id
                    )
                except EndpointTemplateDisabledForTenant:
                    return json.dumps(
                        not_found(
                            "Template not enabled for tenant",
                            request
                        )
                    )
                else:
                    request.setResponseCode(204)
                    return b''

        return json.dumps(
            not_found(
                "Unable to locate an External API with the given Template ID.",
                request
            )
        )


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
