from __future__ import absolute_import, division, unicode_literals

from twisted.trial.unittest import SynchronousTestCase

from mimic.model.identity_objects import (
    bad_request,
    not_found,
    forbidden
)
from mimic.test.dummy import (
    ExampleEndpointTemplate,
    make_example_external_api
)


class YetToBeDone(SynchronousTestCase):
    """
    Test that are a placeholder for necessary functionality that will be needed
    when the full functionality is implemented.
    """

    def test_stuff_todo(self):
        """
        Temporary for code-coverage until endpoints are implemented that will
        actually use these.
        """
        class reqMock(object):
            def setResponseCode(self, code):
                pass

        bad_request("testing bad request", reqMock())
        not_found("testing not found", reqMock())
        forbidden("testing forbidden", reqMock())


class EndpointTemplatesTests(SynchronousTestCase):
    """
    Test Endpoint Template Functionality: list, add, update, remove.
    """
    def setUp(self):
        self.eeapi_name = u"externalServiceName"

    def test_listing_templates(self):
        eeapi_template_id = 'some-template-id'
        eeapi_template = ExampleEndpointTemplate(
            name=self.eeapi_name,
            uuid=eeapi_template_id,
        )
        eeapi = make_example_external_api(
            self,
            name=self.eeapi_name,
            endpoint_templates=[eeapi_template]
        )

        self.assertEqual(len(eeapi.list_templates()), 1)
        eeapi.remove_template(eeapi_template_id)
        self.assertEqual(len(eeapi.list_templates()), 0)

    def test_invalid_endpoint_template(self):
        """
        Validate the endpoint template interface gate check
        """
        eeapi = make_example_external_api(
            self,
            name=self.eeapi_name,
            set_enabled=True
        )

        class InvalidTemplate(object):
            pass

        with self.assertRaises(TypeError):
            eeapi.add_template(InvalidTemplate())

    def test_duplicate_api_insertion_fails(self):
        """
        Validate only one template for by a given name (id) can be added at a
        time.
        """
        eeapi = make_example_external_api(
            self,
            name=self.eeapi_name,
            set_enabled=True
        )
        new_url = "https://api.new_region.example.com:9090"
        new_region = "NEW_REGION"
        new_eeapi_template_id = u"uuid-alternate-endpoint-template"
        new_eeapi_template = ExampleEndpointTemplate(
            name=self.eeapi_name,
            uuid=new_eeapi_template_id,
            region=new_region,
            url=new_url
        )

        # first time succeeds
        eeapi.add_template(new_eeapi_template)

        # second time fails
        with self.assertRaises(ValueError):
            eeapi.add_template(new_eeapi_template)

    def test_update_with_invalid_template(self):
        """
        Validate that an endpoint template must provide the correct
        interfaces, namely :obj:`IEndpointTemplate`.
        """
        class InvalidTemplate(object):
            pass

        eeapi = make_example_external_api(
            self,
            name=self.eeapi_name,
            set_enabled=True,
        )

        with self.assertRaises(TypeError):
            eeapi.update_template(InvalidTemplate())

    def test_update_endpoint_template(self):
        """
        Validate that an endpoint template can be updated provided that
        the id field matches.
        """
        eeapi_template_id = u"uuid-alternate-endpoint-template"

        new_url = "https://api.new_region.example.com:9090"
        new_region = "NEW_REGION"
        old_eeapi_template = ExampleEndpointTemplate(
            name=self.eeapi_name,
            uuid=eeapi_template_id,
            region=new_region,
        )
        new_eeapi_template = ExampleEndpointTemplate(
            name=self.eeapi_name,
            uuid=eeapi_template_id,
            region=new_region,
            url=new_url
        )
        eeapi = make_example_external_api(
            self,
            name=self.eeapi_name,
            set_enabled=True,
            endpoint_templates=[old_eeapi_template]
        )

        self.assertEqual(eeapi.endpoint_templates[eeapi_template_id],
                         old_eeapi_template)
        eeapi.update_template(new_eeapi_template)
        self.assertEqual(eeapi.endpoint_templates[eeapi_template_id],
                         new_eeapi_template)

    def test_update_endpoint_template_invalid(self):
        """
        Validate that the :obj:`ExternalApiStore` will raise the `IndexError`
        exception if the template id is not found when doing an update; in
        otherwords, update != (update or add).
        """
        new_url = "https://api.new_region.example.com:9090"
        new_region = "NEW_REGION"
        new_eeapi_template_id = u"uuid-alternate-endpoint-template"
        new_eeapi_template = ExampleEndpointTemplate(
            name=self.eeapi_name,
            uuid=new_eeapi_template_id,
            region=new_region,
            url=new_url
        )
        eeapi = make_example_external_api(
            self,
            name=self.eeapi_name,
            set_enabled=True,
        )

        with self.assertRaises(IndexError):
            eeapi.update_template(new_eeapi_template)

    def test_remove_endpoint_template_invalid(self):
        """
        Validate that :obj:`ExternalApiStore` will raise the `IndexError`
        exception if the template id is not found when trying to remove a
        template id that does not exist.
        """
        eeapi = make_example_external_api(
            self,
            name=self.eeapi_name,
            set_enabled=True,
        )

        with self.assertRaises(IndexError):
            eeapi.remove_template("some-invalid-template-id")

    def test_remove_endpoint_template(self):
        """
        Validate that an endpoint template can be removed from the
        :obj:`ExternalApiStore`.
        """
        eeapi_template_id = u"uuid-alternate-endpoint-template"
        eeapi_template = ExampleEndpointTemplate(
            name=self.eeapi_name,
            uuid=eeapi_template_id
        )
        eeapi = make_example_external_api(
            self,
            name=self.eeapi_name,
            set_enabled=True,
            endpoint_templates=[eeapi_template]
        )

        self.assertIn(eeapi_template_id, eeapi.endpoint_templates)
        eeapi.remove_template(eeapi_template_id)
        self.assertNotIn(eeapi_template_id, eeapi.endpoint_templates)

    def test_remove_endpoint_template_with_user_registration(self):
        """
        Validate that an endpoint template can be removed even if it enabled
        for a specific tenant.
        """
        eeapi_template_id = u"uuid-alternate-endpoint-template"
        eeapi_template = ExampleEndpointTemplate(
            name=self.eeapi_name,
            uuid=eeapi_template_id
        )
        eeapi = make_example_external_api(
            self,
            name=self.eeapi_name,
            set_enabled=True,
            endpoint_templates=[eeapi_template]
        )
        eeapi.enable_endpoint_for_tenant(
            'some-tenant',
            eeapi_template_id
        )

        self.assertIn(eeapi_template_id, eeapi.endpoint_templates)
        eeapi.remove_template(eeapi_template_id)
        self.assertNotIn(eeapi_template_id, eeapi.endpoint_templates)

    def test_remove_endpoint_template_with_user_registration_alternate(self):
        """
        Validate that only the endpoint template that is suppose to be removed
        is removed.
        """
        eeapi_template_id = u"uuid-alternate-endpoint-template"
        alternate_eeapi_template_id = u"uuid-alternate-endpoint-template-alt"
        eeapi_template = ExampleEndpointTemplate(
            name=self.eeapi_name,
            uuid=eeapi_template_id
        )
        alternate_eeapi_template = ExampleEndpointTemplate(
            name=self.eeapi_name,
            uuid=alternate_eeapi_template_id
        )
        eeapi = make_example_external_api(
            self,
            name=self.eeapi_name,
            set_enabled=True,
            endpoint_templates=[
                eeapi_template,
                alternate_eeapi_template
            ]
        )
        eeapi.enable_endpoint_for_tenant(
            'some-tenant',
            eeapi_template_id
        )
        eeapi.enable_endpoint_for_tenant(
            'some-other-tenant',
            alternate_eeapi_template_id
        )

        self.assertIn(eeapi_template_id, eeapi.endpoint_templates)
        self.assertIn(alternate_eeapi_template_id, eeapi.endpoint_templates)
        eeapi.remove_template(eeapi_template_id)
        self.assertNotIn(eeapi_template_id, eeapi.endpoint_templates)
        self.assertIn(alternate_eeapi_template_id, eeapi.endpoint_templates)


class EndpointsForTenantsTests(SynchronousTestCase):
    """
    Tests for functionality specific to tenants
    """
    def setUp(self):
        self.eeapi_name = u"externalServiceName"

    def test_invalid_template_endpoint_enable(self):
        """
        Validate enabling an invalid endpoint template for a user raises
        `ValueError`.
        """
        eeapi = make_example_external_api(
            self,
            name=self.eeapi_name,
            set_enabled=True
        )

        with self.assertRaises(ValueError):
            eeapi.enable_endpoint_for_tenant(
                'some_tenant',
                'some-invalid-template-id'
            )

    def test_invalid_template_endpoint_disable(self):
        """
        Validate disabling an invalid endpoint template for a user raises
        `ValueError`.
        """
        eeapi = make_example_external_api(
            self,
            name=self.eeapi_name,
            set_enabled=True
        )

        with self.assertRaises(ValueError):
            eeapi.disable_endpoint_for_tenant(
                'some_tenant',
                'some-invalid-template-id'
            )

    def test_disable_endpoint_template_for_tenant(self):
        """
        Validate that an endpoint template can be enabled and disabled for a
        given tenant.
        """
        new_url = "https://api.new_region.example.com:9090"
        new_region = "NEW_REGION"
        new_eeapi_template_id = u"uuid-alternate-endpoint-template"
        new_eeapi_template = ExampleEndpointTemplate(
            name=self.eeapi_name,
            uuid=new_eeapi_template_id,
            region=new_region,
            url=new_url
        )
        eeapi = make_example_external_api(
            self,
            name=self.eeapi_name,
            set_enabled=False,
            endpoint_templates=[new_eeapi_template]
        )

        ept_for_tenant = eeapi.list_tenant_endpoints('some-tenant')
        self.assertEqual(len(ept_for_tenant), 0)

        eeapi.enable_endpoint_for_tenant(
            'some-tenant',
            new_eeapi_template_id
        )
        ept_for_tenant = eeapi.list_tenant_endpoints('some-tenant')
        self.assertEqual(len(ept_for_tenant), 1)
        self.assertEqual(ept_for_tenant[0].tenant_id, 'some-tenant')
        self.assertEqual(ept_for_tenant[0].region, new_region)
        self.assertEqual(ept_for_tenant[0].endpoint_id, new_eeapi_template_id)
        self.assertEqual(ept_for_tenant[0].prefix, "v1")
        self.assertTrue(ept_for_tenant[0].external)
        self.assertIsNotNone(ept_for_tenant[0].complete_url)
        self.assertEqual(ept_for_tenant[0].complete_url, new_url)

        eeapi.disable_endpoint_for_tenant(
            'some-tenant',
            new_eeapi_template_id
        )
        ept_for_tenant = eeapi.list_tenant_endpoints('some-tenant')
        self.assertEqual(len(ept_for_tenant), 0)


class EndpointTemplateOperationsTests(SynchronousTestCase):
    """
    Operational tests for endpoint templates via :obj:`ExternalApiStore`.
    """
    def setUp(self):
        self.eeapi_name = u"externalServiceName"

    def test_uri_for_service_with_invalid_region(self):
        """
        Validate that the :obj:`ExternalApiStore`'s version of
        `uri_for_service` will raise the `IndexError` exception when it cannot
        find a matching region.
        """
        eeapi = make_example_external_api(
            self,
            name=self.eeapi_name,
            set_enabled=True
        )

        with self.assertRaises(IndexError):
            eeapi.uri_for_service('Open', 'Stack')
