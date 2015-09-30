"""
Tests for mimic identity (:mod:`mimic.model.identity` and
:mod:`mimic.rest.auth_api`)
"""
import json

from twisted.trial.unittest import SynchronousTestCase
from twisted.internet.task import Clock

from mimic.canned_responses.auth import (
    get_token, HARD_CODED_TOKEN, HARD_CODED_USER_ID,
    HARD_CODED_USER_NAME, HARD_CODED_ROLES,
    get_endpoints
)
from mimic.canned_responses.mimic_presets import get_presets
from mimic.catalog import Entry, Endpoint
from mimic.core import MimicCore
from mimic.resource import MimicRoot
from mimic.test.behavior_tests import (
    behavior_tests_helper_class,
    register_behavior
)
from mimic.test.dummy import ExampleAPI
from mimic.test.helpers import json_request, request, request_with_content


def core_and_root(api_list):
    """
    Given a list of APIs to load, return core and root.
    """
    core = MimicCore(Clock(), api_list)
    root = MimicRoot(core).app.resource()
    return core, root


class ExampleCatalogEndpoint(object):

    def __init__(self, tenant, num, endpoint_id):
        self._tenant = tenant
        self._num = num
        self.endpoint_id = endpoint_id

    @property
    def region(self):
        return "EXAMPLE_{num}".format(num=self._num)

    @property
    def tenant_id(self):
        return "{tenant}_{num}".format(tenant=self._tenant,
                                       num=self._num)

    def url_with_prefix(self, prefix):
        return "http://ok_{num}".format(num=self._num)


class ExampleCatalogEntry(object):

    """
    Example of a thing that a plugin produces at some phase of its lifecycle;
    maybe you have to pass it a tenant ID to get one of these.  (Services which
    don't want to show up in the catalog won't produce these.)
    """

    def __init__(self, tenant_id, name, endpoint_count=2, idgen=lambda: 1):
        # some services transform their tenant ID
        self.name = name
        self.type = "compute"
        self.path_prefix = "/v2/"
        self.endpoints = [ExampleCatalogEndpoint(tenant_id, n + 1, idgen())
                          for n in range(endpoint_count)]


def example_endpoints(counter):
    """
    Create some example catalog entries from a given tenant ID, like the plugin
    loader would.
    """
    def endpoints(tenant_id):
        yield ExampleCatalogEntry(tenant_id, "something", idgen=counter)
        yield ExampleCatalogEntry(tenant_id, "something_else", idgen=counter)
    return endpoints


class CatalogGenerationTests(SynchronousTestCase):

    """
    Tests for generating a service catalog in various formats from a common
    data source.
    """

    # Service catalogs are pretty large, so set the testing option to a value
    # where we can see as much as possible of the difference in the case of a
    # failure.
    maxDiff = None

    def test_tokens_response(self):
        """
        :func:`get_token` returns JSON-serializable data in the format
        presented by a ``POST /v2.0/tokens`` API request; i.e. the normal
        user-facing service catalog generation.
        """
        tenant_id = 'abcdefg'
        self.assertEqual(
            get_token(
                tenant_id=tenant_id, timestamp=lambda dt: "<<<timestamp>>>",
                entry_generator=example_endpoints(lambda: 1),
                prefix_for_endpoint=lambda e: 'prefix'
            ),
            {
                "access": {
                    "token": {
                        "id": HARD_CODED_TOKEN,
                        "expires": "<<<timestamp>>>",
                        "tenant": {
                            "id": tenant_id,
                            "name": tenant_id,  # TODO: parameterize later
                        },
                        "RAX-AUTH:authenticatedBy": [
                            "PASSWORD",
                        ]
                    },
                    "serviceCatalog": [
                        {
                            "name": "something",
                            "type": "compute",
                            "endpoints": [
                                {
                                    "region": "EXAMPLE_1",
                                    "tenantId": "abcdefg_1",
                                    "publicURL": "http://ok_1"
                                },
                                {
                                    "region": "EXAMPLE_2",
                                    "tenantId": "abcdefg_2",
                                    "publicURL": "http://ok_2"
                                }
                            ]
                        },
                        {
                            "name": "something_else",
                            "type": "compute",
                            "endpoints": [
                                {
                                    "region": "EXAMPLE_1",
                                    "tenantId": "abcdefg_1",
                                    "publicURL": "http://ok_1"
                                },
                                {
                                    "region": "EXAMPLE_2",
                                    "tenantId": "abcdefg_2",
                                    "publicURL": "http://ok_2"
                                }
                            ]
                        }
                    ],
                    "user": {
                        "id": HARD_CODED_USER_ID,
                        "name": HARD_CODED_USER_NAME,
                        "roles": HARD_CODED_ROLES,
                    }
                }
            }
        )

    def test_endpoints_response(self):
        """
        :func:`get_endpoints` returns JSON-serializable data in the format
        presented by a ``GET /v2.0/tokens/<token>/endpoints``; i.e. the
        administrative list of tokens.
        """
        tenant_id = 'abcdefg'
        from itertools import count
        accum = count(1)

        def counter():
            return next(accum)
        # Possible TODO for cloudServersOpenStack:

        # "versionInfo": "http://localhost:8902/v2",
        # "versionList": "http://localhost:8902/",
        # "versionId": "2",

        self.assertEqual(
            get_endpoints(
                tenant_id=tenant_id,
                entry_generator=example_endpoints(counter),
                prefix_for_endpoint=lambda e: 'prefix'
            ),
            {
                "endpoints": [
                    {
                        "region": "EXAMPLE_1",
                        "tenantId": "abcdefg_1",
                        "publicURL": "http://ok_1",
                        "name": "something",
                        "type": "compute",
                        "id": 1,
                    },
                    {
                        "region": "EXAMPLE_2",
                        "tenantId": "abcdefg_2",
                        "publicURL": "http://ok_2",
                        "name": "something",
                        "type": "compute",
                        "id": 2,
                    },
                    {
                        "region": "EXAMPLE_1",
                        "tenantId": "abcdefg_1",
                        "publicURL": "http://ok_1",
                        "name": "something_else",
                        "type": "compute",
                        "id": 3,
                    },
                    {
                        "region": "EXAMPLE_2",
                        "tenantId": "abcdefg_2",
                        "publicURL": "http://ok_2",
                        "name": "something_else",
                        "type": "compute",
                        "id": 4
                    }
                ]
            },
        )

    def test_unversioned_entry(self):
        """
        An L{Endpoint} created without a 'prefix' returns a URI without a
        version.
        """
        self.assertEqual(
            get_endpoints(
                tenant_id="1234",
                entry_generator=lambda t_id: [Entry(
                    tenant_id=t_id, type="compute",
                    name="compute_name", endpoints=[
                        Endpoint(tenant_id=t_id,
                                 region="None",
                                 endpoint_id="eid")
                    ]
                )],
                prefix_for_endpoint=lambda ep: "http://prefix/"
            ),
            {
                "endpoints": [
                    {
                        "id": "eid",
                        "name": "compute_name",
                        "type": "compute",
                        "region": "None",
                        "tenantId": "1234",
                        "publicURL": "http://prefix/1234"
                    }
                ]
            }
        )


def authenticate_with_username_password(test_case, root,
                                        uri='/identity/v2.0/tokens',
                                        username=None, password=None,
                                        tenant_name=None, tenant_id=None,
                                        request_func=json_request):
    """
    Returns a tuple of the response code and json body after authentication
    with username and password.
    """
    creds = {
        "auth": {
            "passwordCredentials": {
                "username": username or "demoauthor",
                "password": password or "theUsersPassword"
            }

        }
    }
    if tenant_id is not None:
        creds["auth"]["tenantId"] = tenant_id
    if tenant_name is not None:
        creds["auth"]["tenantName"] = tenant_name
    return test_case.successResultOf(request_func(test_case, root, "POST",
                                                  uri, json.dumps(creds)))


def authenticate_with_api_key(test_case, root, uri='/identity/v2.0/tokens',
                              username=None, api_key=None,
                              tenant_name=None, tenant_id=None):
    """
    Returns a tuple of the response code and json body after authentication
    using the username and api_key.
    """
    creds = {
        "auth": {
            "RAX-KSKEY:apiKeyCredentials": {
                "username": username or "demoauthor",
                "apiKey": api_key or "jhgjhghg-nhghghgh-12222"
            }

        }
    }
    if tenant_id is not None:
        creds["auth"]["tenantId"] = tenant_id
    if tenant_name is not None:
        creds["auth"]["tenantName"] = tenant_name
    return test_case.successResultOf(json_request(test_case, root, "POST",
                                                  uri, creds))


def authenticate_with_token(test_case, root, uri='/identity/v2.0/tokens',
                            token_id=None, tenant_id=None):
    """
    Returns a tuple of the response code and json body after authentication
    using token and tenant ids.
    """
    creds = {
        "auth": {
            "tenantId": tenant_id or "12345",
            "token": {
                "id": token_id or "iuyiuyiuy-uyiuyiuy-1987878"
            }
        }
    }
    return test_case.successResultOf(json_request(test_case, root, "POST",
                                                  uri, creds))


def impersonate_user(test_case, root,
                     uri="http://mybase/identity/v2.0/RAX-AUTH/impersonation-tokens",
                     username=None, impersonator_token=None):
    """
    Returns a tuple of the response code and json body after authentication
    using token and tenant ids.
    """
    headers = {
        'X-Auth-Token': [str(impersonator_token)]} if impersonator_token else None
    return test_case.successResultOf(json_request(
        test_case, root, "POST", uri,
        {"RAX-AUTH:impersonation": {"expire-in-seconds": 30,
                                    "user": {"username": username or "test1"}}},
        headers=headers
    ))


class GetAuthTokenAPITests(SynchronousTestCase):

    """
    Tests for ``/identity/v2.0/tokens``, provided by
    :obj:`mimic.rest.auth_api.AuthApi.get_token_and_service_catalog`
    """

    def test_response_has_auth_token(self):
        """
        The JSON response has a access.token.id key corresponding to its
        MimicCore session, and therefore access.token.tenant.id should match
        that session's tenant_id.
        """
        core, root = core_and_root([])
        (response, json_body) = authenticate_with_username_password(self, root)
        self.assertEqual(200, response.code)
        token = json_body['access']['token']['id']
        tenant_id = json_body['access']['token']['tenant']['id']
        session = core.sessions.session_for_token(token)
        self.assertEqual(token, session.token)
        self.assertEqual(tenant_id, session.tenant_id)

    def test_response_has_user_admin_identity_role(self):
        """
        The JSON response for authenticate has the role `identity:user-admin`.
        """
        core, root = core_and_root([])
        (response, json_body) = authenticate_with_username_password(self, root)
        self.assertEqual(200, response.code)
        self.assertEqual(
            json_body['access']['user']['roles'], HARD_CODED_ROLES)

    def test_response_has_same_roles_despite_number_of_auths(self):
        """
        The JSON response for authenticate has only one `identity:user-admin`
        role, no matter how many times the user authenticates.
        """
        core, root = core_and_root([])
        (response, json_body) = authenticate_with_username_password(self, root)
        self.assertEqual(200, response.code)
        self.assertEqual(
            json_body['access']['user']['roles'], HARD_CODED_ROLES)
        (response1, json_body1) = authenticate_with_username_password(
            self, root)
        self.assertEqual(200, response1.code)
        self.assertEqual(
            json_body1['access']['user']['roles'], HARD_CODED_ROLES)
        (response2, json_body2) = authenticate_with_username_password(
            self, root)
        self.assertEqual(200, response2.code)
        self.assertEqual(
            json_body2['access']['user']['roles'], HARD_CODED_ROLES)

    def test_authentication_request_with_no_body_causes_http_bad_request(self):
        """
        The response for empty body request is bad_request.
        """
        core, root = core_and_root([])

        (response, json_body) = self.successResultOf(json_request(
            self, root, "POST", "/identity/v2.0/tokens", ""))

        self.assertEqual(400, response.code)

    def test_authentication_request_with_invalid_body_causes_http_bad_request(self):
        """
        The response for not JSON body request is bad_request.
        """
        core, root = core_and_root([])

        response = self.successResultOf(request(
            self, root, "POST", "/identity/v2.0/tokens", "{ bad request: }"))

        self.assertEqual(400, response.code)

    def test_auth_accepts_tenant_name(self):
        """
        If "tenantName" is passed, the tenant specified is used instead of a
        generated tenant ID.
        """
        core, root = core_and_root([])

        (response, json_body) = authenticate_with_username_password(
            self,
            root,
            tenant_name="turtlepower")

        self.assertEqual(200, response.code)
        self.assertEqual("turtlepower",
                         json_body['access']['token']['tenant']['id'])
        token = json_body['access']['token']['id']
        session = core.sessions.session_for_token(token)
        self.assertEqual(token, session.token)
        self.assertEqual("turtlepower", session.tenant_id)

    def test_auth_accepts_tenant_id(self):
        """
        If "tenantId" is passed, the tenant specified is used instead of a
        generated tenant ID.
        """
        core, root = core_and_root([])
        (response, json_body) = authenticate_with_username_password(
            self,
            root,
            tenant_id="turtlepower")
        self.assertEqual(200, response.code)
        self.assertEqual("turtlepower",
                         json_body['access']['token']['tenant']['id'])
        token = json_body['access']['token']['id']
        session = core.sessions.session_for_token(token)
        self.assertEqual(token, session.token)
        self.assertEqual("turtlepower", session.tenant_id)

    def test_response_service_catalog_has_base_uri(self):
        """
        The JSON response's service catalog whose endpoints all begin with
        the same base URI as the request.
        """
        core, root = core_and_root([ExampleAPI()])
        (response, json_body) = authenticate_with_username_password(
            self,
            root, uri='http://mybase/identity/v2.0/tokens')
        self.assertEqual(200, response.code)
        services = json_body['access']['serviceCatalog']
        self.assertEqual(1, len(services))

        urls = [
            endpoint['publicURL'] for endpoint in services[0]['endpoints']
        ]
        self.assertEqual(1, len(urls))
        self.assertTrue(urls[0].startswith('http://mybase/'),
                        '{0} does not start with "http://mybase"'
                        .format(urls[0]))


class GetEndpointsForTokenTests(SynchronousTestCase):

    """
    Tests for ``/identity/v2.0/tokens/<token>/endpoints``, provided by
    `:obj:`mimic.rest.auth_api.AuthApi.get_endpoints_for_token`
    """

    def test_session_created_for_token(self):
        """
        A session is created for the token provided
        """
        core, root = core_and_root([])

        token = '1234567890'

        request(
            self, root, "GET",
            "/identity/v2.0/tokens/{0}/endpoints".format(token)
        )

        session = core.sessions.session_for_token(token)
        self.assertEqual(token, session.token)

    def test_response_service_catalog_has_base_uri(self):
        """
        The JSON response's service catalog whose endpoints all begin with
        the same base URI as the request.
        """
        core, root = core_and_root([ExampleAPI()])

        (response, json_body) = self.successResultOf(json_request(
            self, root, "GET",
            "http://mybase/identity/v2.0/tokens/1234567890/endpoints"
        ))

        self.assertEqual(200, response.code)
        urls = [endpoint['publicURL'] for endpoint in json_body['endpoints']]
        self.assertEqual(1, len(urls))

        self.assertTrue(
            urls[0].startswith('http://mybase/'),
            '{0} does not start with "http://mybase"'.format(urls[0]))

    def test_api_service_endpoints_are_not_duplicated(self):
        """
        The service catalog should not duplicate endpoints for an entry/endpoints
        """
        regions_and_versions_list = [
            ("ORD", "v1"), ("DFW", "v1"), ("DFW", "v2"), ("IAD", "v3")]
        core, root = core_and_root([ExampleAPI(
            regions_and_versions=regions_and_versions_list)])

        (response, json_body) = authenticate_with_username_password(self, root)
        self.assertEqual(response.code, 200)
        service_catalog = json_body["access"]["serviceCatalog"]
        self.assertEqual(len(service_catalog), 1)
        endpoints_list = service_catalog[0]["endpoints"]
        self.assertEqual(len(endpoints_list), 4)

    def test_get_token_and_catalog_for_password_credentials(self):
        """
        The response returned should include the password credentials that were supplied
        during authentication
        """
        core, root = core_and_root([ExampleAPI()])
        (response, json_body) = authenticate_with_username_password(self, root,
                                                                    tenant_id='12345')
        self.assertEqual(response.code, 200)
        tenant_id = json_body["access"]["token"]["tenant"]["id"]
        self.assertEqual(tenant_id, "12345")
        tenant_name = json_body["access"]["token"]["tenant"]["name"]
        self.assertEqual(tenant_name, tenant_id)
        user_name = json_body["access"]["user"]["name"]
        self.assertEqual(user_name, "demoauthor")

    def test_get_token_and_catalog_for_api_credentials(self):
        """
        The response returned should include the credentials that were supplied
        during authentication
        """
        core, root = core_and_root([ExampleAPI()])
        (response, json_body) = authenticate_with_api_key(self, root,
                                                          tenant_name='12345')
        self.assertEqual(response.code, 200)
        tenant_id = json_body["access"]["token"]["tenant"]["id"]
        self.assertEqual(tenant_id, "12345")
        tenant_name = json_body["access"]["token"]["tenant"]["name"]
        self.assertEqual(tenant_name, tenant_id)
        user_name = json_body["access"]["user"]["name"]
        self.assertEqual(user_name, "demoauthor")

    def test_get_token_and_catalog_for_token_credentials(self):
        """
        The response returned should include the credentials that were supplied
        during authentication
        """
        core, root = core_and_root([ExampleAPI()])
        (response, json_body) = authenticate_with_token(
            self, root, tenant_id='12345')
        self.assertEqual(response.code, 200)
        tenant_id = json_body["access"]["token"]["tenant"]["id"]
        self.assertEqual(tenant_id, "12345")
        tenant_name = json_body["access"]["token"]["tenant"]["name"]
        self.assertEqual(tenant_name, tenant_id)
        user_name = json_body["access"]["user"]["name"]
        self.assertTrue(user_name)

    def test_token_and_catalog_for_password_credentials_wrong_tenant(self):
        """
        Tenant ID is validated when provided in username/password auth.

        If authed once as one tenant ID, and a second time with a different
        tenant ID, then the second auth will return with a 401 Unauthorized.
        """
        core, root = core_and_root([ExampleAPI()])
        (response, json_body) = authenticate_with_username_password(
            self, root, tenant_id="12345")
        self.assertEqual(response.code, 200)
        username = json_body["access"]["user"]["id"]

        (response, fail_body) = authenticate_with_username_password(
            self, root, tenant_id="23456")
        self.assertEqual(response.code, 401)
        self.assertEqual(fail_body, {
            "unauthorized": {
                "code": 401,
                "message": ("Tenant with Name/Id: '23456' is not valid for "
                            "User 'demoauthor' (id: '{0}')".format(username))
            }
        })

    def test_rax_kskey_apikeycredentials(self):
        """
        Test apiKeyCredentials
        """
        core, root = core_and_root([ExampleAPI()])
        (response, json_body) = self.successResultOf(json_request(
            self, root, "GET",
            "/identity/v2.0/users/1/OS-KSADM/credentials/RAX-KSKEY:apiKeyCredentials"
        ))
        self.assertEqual(response.code, 404)
        self.assertEqual(
            json_body['itemNotFound']['message'], 'User 1 not found')
        creds = {
            "auth": {
                "passwordCredentials": {
                    "username": "HedKandi",
                    "password": "Ministry Of Sound UK"
                },
                "tenantId": "77777"
            }
        }
        (response, json_body) = self.successResultOf(json_request(
            self, root, "POST", "/identity/v2.0/tokens", creds))
        self.assertEqual(response.code, 200)
        user_id = json_body['access']['user']['id']
        username = json_body['access']['user']['name']
        (response, json_body) = self.successResultOf(json_request(
            self, root, "GET",
            "/identity/v2.0/users/" + user_id +
            "/OS-KSADM/credentials/RAX-KSKEY:apiKeyCredentials"
        ))
        self.assertEqual(response.code, 200)
        self.assertEqual(json_body['RAX-KSKEY:apiKeyCredentials']['username'],
                         username)
        self.assertTrue(
            len(json_body['RAX-KSKEY:apiKeyCredentials']['apiKey']) == 32)

    def test_token_and_catalog_for_api_credentials_wrong_tenant(self):
        """
        Tenant ID is validated when provided in api-key auth.

        If authed once as one tenant ID, and a second time with a different
        tenant ID, then the second auth will return with a 401 Unauthorized.
        """
        core, root = core_and_root([ExampleAPI()])
        (response, json_body) = authenticate_with_api_key(
            self, root, tenant_id="12345")
        self.assertEqual(response.code, 200)
        username = json_body["access"]["user"]["id"]

        (response, fail_body) = authenticate_with_api_key(
            self, root, tenant_id="23456")
        self.assertEqual(response.code, 401)
        self.assertEqual(fail_body, {
            "unauthorized": {
                "code": 401,
                "message": ("Tenant with Name/Id: '23456' is not valid for "
                            "User 'demoauthor' (id: '{0}')".format(username))
            }
        })

    def test_token_and_catalog_for_token_credentials_wrong_tenant(self):
        """
        Tenant ID is validated when provided in token auth.

        If authed once as one tenant ID, and a second time with a different
        tenant ID, then the second auth will return with a 401 Unauthorized.
        """
        core, root = core_and_root([ExampleAPI()])
        (response, json_body) = authenticate_with_token(
            self, root, tenant_id="12345")
        self.assertEqual(response.code, 200)

        (response, fail_body) = authenticate_with_token(
            self, root, tenant_id="23456")
        self.assertEqual(response.code, 401)
        self.assertEqual(fail_body, {
            "unauthorized": {
                "code": 401,
                "message": ("Token doesn't belong to Tenant with Id/Name: "
                            "'23456'")
            }
        })

    def test_get_token_and_catalog_for_invalid_json_request_body(self):
        """
        :func: `get_token_and_service_catalog` returns response code 400, when
        an invalid json request body is used to authenticate.
        """
        core, root = core_and_root([ExampleAPI()])

        (response, json_body) = self.successResultOf(json_request(
            self, root, "POST", "/identity/v2.0/tokens",
            {
                "auth": {
                    "token": {
                        "id": "iuyiuyiuy-uyiuyiuy-1987878"
                    }
                }
            }
        ))
        self.assertEqual(response.code, 400)
        self.assertEqual(json_body["message"], "Invalid JSON request body")

    def test_response_for_get_username(self):
        """
        Test to verify :func: `get_username`.
        """
        core, root = core_and_root([ExampleAPI()])

        (response, json_body) = self.successResultOf(json_request(
            self, root, "GET",
            "http://mybase/identity/v1.1/mosso/123456"
        ))
        self.assertEqual(301, response.code)
        self.assertTrue(json_body['user']['id'])

    def test_response_for_impersonation(self):
        """
        Test to verify :func: `get_impersonation_token`.
        """
        core, root = core_and_root([ExampleAPI()])

        (response, json_body) = impersonate_user(self, root)
        self.assertEqual(200, response.code)
        self.assertTrue(json_body['access']['token']['id'])

    def test_impersonation_without_expires_in_seconds_attribute(self):
        """
        Test to verify :func: `get_impersonation_token` when the `expire-in-seconds`
        is not provided.
        """
        core, root = core_and_root([ExampleAPI()])

        (response, json_body) = self.successResultOf(json_request(
            self, root, "POST", "http://mybase/identity/v2.0/RAX-AUTH/impersonation-tokens",
            {"RAX-AUTH:impersonation": {"user": {"username": "user-test"}}}))
        self.assertEqual(200, response.code)
        self.assertTrue(json_body['access']['token']['id'])

    def test_impersonation_request_with_no_body_causes_http_bad_request(self):
        """
        The response for empty body request is bad_request.
        """
        core, root = core_and_root([])

        (response, json_body) = self.successResultOf(json_request(
            self, root, "POST", "http://mybase/identity/v2.0/RAX-AUTH/impersonation-tokens", ""))

        self.assertEqual(400, response.code)

    def test_impersonation_request_with_invalid_body_causes_http_bad_request(self):
        """
        The response for not JSON body request is bad_request.
        """
        core, root = core_and_root([])

        response = self.successResultOf(request(
            self, root, "POST", "http://mybase/identity/v2.0/RAX-AUTH/impersonation-tokens",
                                "{ bad request: }"))

        self.assertEqual(400, response.code)

    def test_response_for_validate_token(self):
        """
        Test to verify :func: `validate_token`.
        """
        core, root = core_and_root([ExampleAPI()])

        (response, json_body) = self.successResultOf(json_request(
            self, root, "GET",
            "http://mybase/identity/v2.0/tokens/123456a?belongsTo=111111"
        ))
        self.assertEqual(200, response.code)
        self.assertEqual(json_body['access']['token']['id'], '123456a')
        self.assertTrue(json_body['access']['user']['id'])
        self.assertTrue(len(json_body['access']['user']['roles']) > 0)
        self.assertTrue(json_body['access'].get('serviceCatalog') is None)

    def test_response_for_validate_token_when_tenant_not_provided(self):
        """
        Test to verify :func: `validate_token` when tenant_id is not
        provided using the argument `belongsTo`
        """
        core, root = core_and_root([ExampleAPI()])

        (response, json_body) = self.successResultOf(json_request(
            self, root, "GET",
            "http://mybase/identity/v2.0/tokens/123456a"
        ))
        self.assertEqual(200, response.code)
        self.assertEqual(json_body['access']['token']['id'], '123456a')
        self.assertTrue(json_body['access']['token']['tenant']['id'])

    def test_response_for_validate_token_then_authenticate(self):
        """
        Test to verify :func: `validate_token` and then authenticate
        """
        core, root = core_and_root([ExampleAPI()])

        (response1, json_body1) = self.successResultOf(json_request(
            self, root, "GET",
            "http://mybase/identity/v2.0/tokens/123456a?belongsTo=111111"
        ))
        self.assertEqual(200, response1.code)
        (response, json_body) = authenticate_with_token(self, root,
                                                        tenant_id="111111",
                                                        token_id="123456a")
        self.assertEqual(response.code, 200)
        self.assertEqual(json_body["access"]["token"]["id"],
                         json_body1["access"]["token"]["id"])
        self.assertEqual(json_body["access"]["token"]["tenant"]["id"],
                         json_body1["access"]["token"]["tenant"]["id"])
        self.assertEqual(json_body["access"]["user"]["name"],
                         json_body1["access"]["user"]["name"])

    def test_response_for_validate_impersonated_token(self):
        """
        Test to verify :func: `validate_token` and then authenticate
        """
        core, root = core_and_root([ExampleAPI()])

        # Authenticate the impersonator (admin user)
        (response0, json_body0) = authenticate_with_token(
            self, root,
            tenant_id="111111",
            token_id="123456a")
        self.assertEqual(200, response0.code)
        impersonator_token = json_body0["access"]["token"]["id"]

        # Authenticate using the username so we know the tenant_id
        (response1, json_body1) = authenticate_with_username_password(
            self, root,
            username="test1",
            tenant_id="12345")
        self.assertEqual(200, response1.code)

        # Impersonate user test1
        (response2, json_body2) = impersonate_user(
            self, root,
            username="test1",
            impersonator_token=impersonator_token)
        self.assertEqual(200, response2.code)
        impersonated_token = json_body2["access"]["token"]["id"]

        # validate the impersonated_token
        (response3, json_body3) = self.successResultOf(json_request(
            self, root, "GET",
            "http://mybase/identity/v2.0/tokens/{0}?belongsTo=12345".format(
                impersonated_token)
        ))
        self.assertEqual(200, response3.code)
        self.assertTrue(json_body3["access"]["RAX-AUTH:impersonator"])

    def test_response_for_validate_impersonated_token_multiple_users(self):
        """
        Test to verify :func: `validate_token` and then authenticate
        """
        core, root = core_and_root([ExampleAPI()])

        # Authenticate the impersonator (admin user 1)
        (response0, json_body0) = authenticate_with_token(
            self, root,
            tenant_id="111111",
            token_id="123456a")
        self.assertEqual(200, response0.code)
        impersonator_token1 = json_body0["access"]["token"]["id"]

        # Authenticate the impersonator (admin user 2)
        (response1, json_body1) = authenticate_with_token(
            self, root,
            tenant_id="222222",
            token_id="123456b")

        self.assertEqual(200, response1.code)
        impersonator_token2 = json_body1["access"]["token"]["id"]

        # Authenticate the impersonatee using the username so we know the
        # tenant_id to make the validate token id call with 'belongsTo'
        (response2, json_body2) = authenticate_with_username_password(
            self, root,
            username="test1",
            tenant_id="12345")
        self.assertEqual(200, response2.code)

        # Impersonate user test1 using admin user1's token
        (response3, json_body3) = impersonate_user(
            self, root,
            username="test1",
            impersonator_token=impersonator_token1)
        self.assertEqual(200, response3.code)
        impersonated_token1 = json_body3["access"]["token"]["id"]

        # Impersonate user test1 using admin user2's token
        (response4, json_body4) = impersonate_user(
            self, root,
            username="test1",
            impersonator_token=impersonator_token2)
        self.assertEqual(200, response4.code)
        impersonated_token2 = json_body4["access"]["token"]["id"]

        # validate the impersonated_token1
        (response5, json_body5) = self.successResultOf(json_request(
            self, root, "GET",
            "http://mybase/identity/v2.0/tokens/{0}?belongsTo=12345".format(
                impersonated_token1)
        ))
        self.assertEqual(200, response5.code)
        self.assertTrue(json_body5["access"]["RAX-AUTH:impersonator"])
        self.assertEqual(json_body5["access"]["RAX-AUTH:impersonator"]["name"],
                         json_body0["access"]["user"]["name"])

        # validate the impersonated_token2
        (response6, json_body6) = self.successResultOf(json_request(
            self, root, "GET",
            "http://mybase/identity/v2.0/tokens/{0}?belongsTo=12345".format(
                impersonated_token2)
        ))
        self.assertEqual(200, response6.code)
        self.assertTrue(json_body6["access"]["RAX-AUTH:impersonator"])
        self.assertEqual(json_body6["access"]["RAX-AUTH:impersonator"]["name"],
                         json_body1["access"]["user"]["name"])

    def test_response_for_validate_token_with_maas_admin_role(self):
        """
        Test to verify :func: `validate_token` when the token_id provided
        is of an maas admin user specified in `mimic_presets`.
        """
        core, root = core_and_root([ExampleAPI()])

        (response, json_body) = self.successResultOf(json_request(
            self, root, "GET",
            "http://mybase/identity/v2.0/tokens/this_is_an_impersonator_token"
        ))
        self.assertEqual(200, response.code)
        self.assertEqual(json_body["access"]["RAX-AUTH:impersonator"]["roles"][0]["name"],
                         "monitoring:service-admin")

    def test_response_for_validate_token_with_racker_role(self):
        """
        Test to verify :func: `validate_token` when the token_id provided
        is of a racker specified in `mimic_presets`.
        """
        core, root = core_and_root([ExampleAPI()])

        (response, json_body) = self.successResultOf(json_request(
            self, root, "GET",
            "http://mybase/identity/v2.0/tokens/this_is_a_racker_token"
        ))
        self.assertEqual(200, response.code)
        self.assertEqual(json_body["access"]["RAX-AUTH:impersonator"]["roles"][0]["name"],
                         "Racker")

    def test_response_for_validate_token_when_invalid(self):
        """
        Test to verify :func: `validate_token` when the token_id provided
        is invalid, as specified in `mimic_presets`.
        """
        core, root = core_and_root([ExampleAPI()])
        token = get_presets["identity"]["token_fail_to_auth"][0]

        (response, json_body) = self.successResultOf(json_request(
            self, root, "GET",
            "http://mybase/identity/v2.0/tokens/{0}".format(token)
        ))
        self.assertEqual(401, response.code)

    def test_response_for_validate_token_with_observer_role(self):
        """
        Test to verify :func: `validate_token` when the tenant_id provided
        is of an observer role, as specified in `mimic_presets`.
        """
        core, root = core_and_root([ExampleAPI()])
        token = get_presets["identity"]["observer_role"][0]

        (response, json_body) = self.successResultOf(json_request(
            self, root, "GET",
            "http://mybase/identity/v2.0/tokens/any_token?belongsTo={0}".format(token)
        ))
        self.assertEqual(200, response.code)
        self.assertEqual(json_body["access"]["user"]["roles"][0]["name"],
                         "observer")
        self.assertEqual(json_body["access"]["user"]["roles"][0]["description"],
                         "Global Observer Role.")

    def test_response_for_validate_token_with_creator_role(self):
        """
        Test to verify :func: `validate_token` when the tenant_id provided
        is of an creator role, as specified in `mimic_presets`.
        """
        core, root = core_and_root([ExampleAPI()])
        token = get_presets["identity"]["creator_role"][0]

        (response, json_body) = self.successResultOf(json_request(
            self, root, "GET",
            "http://mybase/identity/v2.0/tokens/any_token?belongsTo={0}".format(token)
        ))
        self.assertEqual(200, response.code)
        self.assertEqual(json_body["access"]["user"]["roles"][0]["name"],
                         "creator")
        self.assertEqual(json_body["access"]["user"]["roles"][0]["description"],
                         "Global Creator Role.")

    def test_response_for_validate_token_with_admin_and_observer_role(self):
        """
        Test to verify :func: `validate_token` when the tenant_id provided
        is of an admin role, as specified in `mimic_presets`.
        """
        core, root = core_and_root([ExampleAPI()])
        token = get_presets["identity"]["admin_role"][0]

        (response, json_body) = self.successResultOf(json_request(
            self, root, "GET",
            "http://mybase/identity/v2.0/tokens/any_token?belongsTo={0}".format(token)
        ))
        self.assertEqual(200, response.code)
        self.assertEqual(json_body["access"]["user"]["roles"][0]["name"],
                         "admin")
        self.assertEqual(json_body["access"]["user"]["roles"][0]["description"],
                         "Global Admin Role.")
        self.assertEqual(json_body["access"]["user"]["roles"][1]["name"],
                         "observer")
        self.assertEqual(json_body["access"]["user"]["roles"][1]["description"],
                         "Global Observer Role.")

    def test_response_for_list_users(self):
        """
        Test to verify :func: `get_users_details`.
        """
        core, root = core_and_root([ExampleAPI()])

        (response, json_body) = self.successResultOf(json_request(
            self, root, "GET",
            "http://mybase/identity/v2.0/users?name=random_user"
        ))
        self.assertEqual(200, response.code)
        self.assertTrue(json_body['user']['RAX-AUTH:domainId'])

    def test_response_for_list_users_after_authentication(self):
        """
        Test to verify :func: `get_users_details`.
        """
        core, root = core_and_root([ExampleAPI()])
        (response, json_body) = authenticate_with_token(
            self, root, tenant_id="12345")
        self.assertEqual(response.code, 200)
        username = json_body["access"]["user"]["name"]
        user_id = json_body["access"]["user"]["id"]

        (response, json_body) = self.successResultOf(json_request(
            self, root, "GET",
            "http://mybase/identity/v2.0/users?name={0}".format(username)
        ))
        self.assertEqual(200, response.code)
        self.assertEqual(json_body['user']['RAX-AUTH:domainId'], "12345")
        self.assertEqual(json_body['user']['username'], username)
        self.assertEqual(json_body['user']['id'], user_id)


class AuthIntegrationTests(SynchronousTestCase):
    """
    Tests that combine multiple auth calls together and assure that they
    return consistent data.
    """

    def test_user_for_tenant_then_impersonation(self):
        """
        After authenticating once as a particular tenant, get the user that
        tenant, then attempt to impersonate that user.  The tenant IDs should
        be the same.  This is an autoscale regression test.
        """
        core, root = core_and_root([ExampleAPI()])
        tenant_id = "111111"

        # authenticate as that user - this is not strictly necessary, since
        # getting a user for a tenant should work regardless of whether a user
        # was previously in the system, but this will ensure that we can check
        # the username
        response, json_body = authenticate_with_username_password(
            self, root, username="my_user", tenant_id=tenant_id)
        self.assertEqual(200, response.code)
        self.assertEqual(tenant_id,
                         json_body['access']['token']['tenant']['id'])

        # get user for tenant
        response, json_body = self.successResultOf(json_request(
            self, root, "GET", "/identity/v1.1/mosso/111111"))
        self.assertEqual(301, response.code)
        user = json_body['user']['id']
        self.assertEqual("my_user", user)

        # impersonate this user
        response, json_body = impersonate_user(self, root, username=user)
        self.assertEqual(200, response.code)
        token = json_body["access"]['token']["id"]

        # get endpoints for this token, see what the tenant is
        response, json_body = self.successResultOf(json_request(
            self, root, "GET",
            "/identity/v2.0/tokens/{0}/endpoints".format(token)))
        self.assertEqual(200, response.code)
        self.assertEqual(tenant_id,
                         json_body["endpoints"][0]["tenantId"])

        # authenticate with this token and see what the tenant is
        response, json_body = authenticate_with_token(
            self, root, token_id=token, tenant_id=tenant_id)
        self.assertEqual(tenant_id,
                         json_body['access']['token']['tenant']['id'])

    def test_api_key_then_other_token_same_tenant(self):
        """
        After authenticating as a particular tenant with an API key,
        authenticate as the same tenant with a token that is different
        from the one returned by the API key response. Both tokens
        should be accessing the same session.
        """
        core, root = core_and_root([ExampleAPI()])
        tenant_id = "123456"

        response, json_body = authenticate_with_api_key(
            self, root, tenant_id=tenant_id)
        self.assertEqual(200, response.code)
        username_from_api_key = json_body["access"]["user"]["name"]

        response, json_body = authenticate_with_token(
            self, root, token_id="fake_111111", tenant_id=tenant_id)
        self.assertEqual(200, response.code)
        username_from_token = json_body["access"]["user"]["name"]

        # Since usernames are generated if not specified, and token
        # authentication does not specify a username, it is sufficient
        # to check that the usernames are equal. If the sessions are
        # distinct, then the token would have generated a UUID for its
        # username.
        self.assertEqual(username_from_api_key, username_from_token)


auth_behavior_endpoint = (
    "http://mybase/mimic/v1.1/IdentityControlAPI/behaviors/auth")


@behavior_tests_helper_class
class IdentityAuthBehaviorControlPlane(object):
    """
    Helper object used to generate tests for Nova create server behavior
    CRUD operations.
    """
    criteria = [{"username": "failme"}]
    names_and_params = (
        ("fail",
         {"message": "Auth failure", "code": 500, "type": "identityFault"}),
        ("fail",
         {"message": "Invalid creds", "code": 403})
    )

    def __init__(self, test_case):
        """
        Set up the criteria, api mock, etc.
        """
        self.test_case = test_case
        _, self.root = core_and_root([])
        self.behavior_api_endpoint = auth_behavior_endpoint

    def trigger_event(self):
        """
        Create server with with the name "failing_server_name".
        """
        return authenticate_with_username_password(
            self.test_case, self.root, username="failme")

    def validate_injected_behavior(self, name_and_params, response, body):
        """
        Given the behavior that is expected, validate the response and body.
        """
        name, params = name_and_params
        self.test_case.assertEquals(response.code, params['code'])
        if params['code'] == 500:
            expected = {"identityFault": {"message": "Auth failure",
                                          "code": 500}}
        else:
            expected = {"unauthorized": {"message": "Invalid creds",
                                         "code": 403}}

        self.test_case.assertEquals(body, expected)

    def validate_default_behavior(self, response, body):
        """
        Validate the response and body of a successful server create.
        """
        self.test_case.assertEquals(response.code, 200)
        self.test_case.assertIn('access', body)


class IdentityBehaviorInjectionTests(SynchronousTestCase):
    """
    Tests for specific failures and/or criteria.
    """
    def test_username_criteria_works_on_all_auth_methods_with_username(self):
        """
        Failure injection based on the username criteria will work on
        username/password, username/api-key, and impersonation.  But not
        token ID, even if it's with the same tenant.
        """
        core, root = core_and_root([])
        fail_params = {"message": "Invalid creds", "code": 403}

        # make sure a user exists in mimic with the given username tenant
        # associated
        response, body = authenticate_with_username_password(
            self, root, username="failme", tenant_id="123456")
        self.assertEqual(response.code, 200)

        # username auths fail
        register_behavior(self, root, auth_behavior_endpoint,
                          behavior_name="fail",
                          criteria=[{"username": "failme"}],
                          parameters=fail_params)
        for auth_func in (authenticate_with_username_password,
                          authenticate_with_api_key,
                          impersonate_user):
            response, body = auth_func(self, root, username="failme")
            self.assertEqual(response.code, 403)
            self.assertEqual(body, {"unauthorized": fail_params})

        # token auth with that tenant ID succeeds
        response, body = authenticate_with_token(
            self, root, tenant_id="123456")
        self.assertEqual(response.code, 200)

    def test_tenant_id_criteria_works_on_all_auth_methods_with_tenant(self):
        """
        Failure injection based on the username criteria will work on
        username/password, username/api-key, and token.
        But not impersonation.
        """
        core, root = core_and_root([])
        fail_params = {"message": "Invalid creds", "code": 403}

        # make sure a user exists in mimic with the given username tenant
        # associated
        response, body = authenticate_with_username_password(
            self, root, username="failme", tenant_id="123456")
        self.assertEqual(response.code, 200)

        # tenant auths fail
        register_behavior(self, root, auth_behavior_endpoint,
                          behavior_name="fail",
                          criteria=[{"tenant_id": "123456"}],
                          parameters=fail_params)
        for auth_func in (authenticate_with_username_password,
                          authenticate_with_api_key,
                          authenticate_with_token):
            response, body = auth_func(self, root, tenant_id="123456")
            self.assertEqual(response.code, 403)
            self.assertEqual(body, {"unauthorized": fail_params})

        # impersonation with that username succeeds
        response, body = impersonate_user(self, root, username="failme")
        self.assertEqual(response.code, 200)

    def test_string_errors_as_well_as_json_errors(self):
        """
        Failure injection will return a string error response as well as a
        json response.
        """
        core, root = core_and_root([])
        fail_params = {"message": "Failure of JSON", "code": 500,
                       "type": "string"}

        register_behavior(self, root, auth_behavior_endpoint,
                          behavior_name="fail",
                          criteria=[{"username": "failme"}],
                          parameters=fail_params)
        response, body = authenticate_with_username_password(
            self, root, username="failme", request_func=request_with_content)
        self.assertEqual(response.code, 500)
        self.assertEqual(body, "Failure of JSON")


class IdentityNondedicatedFixtureTests(SynchronousTestCase):

    def test_non_dedicated_tokens(self):
        """
        Obtain Identity entries when presented tokens issued to non-dedicated users
        """
        url = "/identity/v2.0/tokens"
        core, root = core_and_root([])
        (response, content) = self.successResultOf(
            json_request(self, root, "GET", url + "/OneTwo"))
        self.assertEqual(200, response.code)
        self.assertEqual(content["access"]["token"]["tenant"]["id"], "135790")

        (response, content) = self.successResultOf(
            json_request(self, root, "GET", url + "/ThreeFour"))
        self.assertEqual(200, response.code)


class IdentityDedicatedFixtureTests(SynchronousTestCase):

    def test_dedicated_tokens(self):
        """
        Obtain Identity entries when presented tokens issued to dedicated users
        """
        url = "/identity/v2.0/tokens"
        core, root = core_and_root([])
        (response, content) = self.successResultOf(
            json_request(self, root, "GET", url + "/HybridOneTwo"))
        self.assertEqual(200, response.code)
        self.assertEqual(content["access"]["token"]["tenant"]["id"], "hybrid:123456")
        self.assertEqual(content["access"]["user"]["RAX-AUTH:contactId"], "12")

        (response, content) = self.successResultOf(
            json_request(self, root, "GET", url + "/HybridThreeFour"))
        self.assertEqual(200, response.code)
        self.assertEqual(content["access"]["token"]["tenant"]["id"], "hybrid:123456")
        self.assertEqual(content["access"]["user"]["RAX-AUTH:contactId"], "34")

        (response, content) = self.successResultOf(
            json_request(self, root, "GET", url + "/HybridFiveSix"))
        self.assertEqual(200, response.code)
        self.assertEqual(content["access"]["token"]["tenant"]["id"], "hybrid:123456")
        self.assertEqual(content["access"]["user"]["RAX-AUTH:contactId"], "56")

        (response, content) = self.successResultOf(
            json_request(self, root, "GET", url + "/HybridSevenEight"))
        self.assertEqual(200, response.code)
        self.assertEqual(content["access"]["token"]["tenant"]["id"], "hybrid:654321")
        self.assertEqual(content["access"]["user"]["RAX-AUTH:contactId"], "78")

        (response, content) = self.successResultOf(
            json_request(self, root, "GET", url + "/HybridNineZero"))
        self.assertEqual(200, response.code)
        self.assertEqual(content["access"]["token"]["tenant"]["id"], "hybrid:654321")
        self.assertEqual(content["access"]["user"]["RAX-AUTH:contactId"], "90")
