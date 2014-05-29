
from unittest import TestCase

from mimic.canned_responses.auth import (
    get_token, HARD_CODED_TOKEN, HARD_CODED_USER_ID,
    HARD_CODED_USER_NAME, HARD_CODED_ROLES,
    get_endpoints
)


class ExampleCatalogEndpoint:
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
        self.endpoints = [ExampleCatalogEndpoint(tenant_id, n+1, idgen())
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


class CatalogGenerationTests(TestCase):
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
                entry_generator=example_endpoints(lambda: 1)
            ),
            {
                "access": {
                    "token": {
                        "id": HARD_CODED_TOKEN,
                        "expires": "<<<timestamp>>>",
                        "tenant": {
                            "id": tenant_id,
                            "name": tenant_id, # TODO: parameterize later
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

