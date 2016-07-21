from __future__ import absolute_import, division, unicode_literals

from twisted.trial.unittest import SynchronousTestCase

from mimic.model.identity_objects import (
    EndpointTemplateStore,
    bad_request,
    conflict,
    not_found,
    unauthorized,
)
from mimic.test.dummy import (
    ExampleEndpointTemplate,
    make_example_external_api,
)
from mimic.test.helpers import get_template_id


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
        conflict("testing conflict", reqMock())
        not_found("testing not-found", reqMock())
        unauthorized("testing unauthorized", reqMock())


class EndpointTemplateInstanceTests(SynchronousTestCase):
    """
    Validate the :obj:`EndpointTemplateStore`
    """
    @staticmethod
    def get_optional_mapping_value(epts, attribute_name):
        """
        Access default value and template name in the optional
        mappings in the provided endoint template.
        """
        for m in epts.optional_mapping:
            if m.attr_name == attribute_name:
                return (m.default_value, m.spec_key)

    def validate_mapping(self, epts, data, use_defaults):
        """
        Validate that the template matches the expected data.
        """
        self.assertEqual(data, epts._template_data)
        self.assertEqual(data['id'], epts.id_key)
        self.assertEqual(data['region'], epts.region_key)
        self.assertEqual(data['type'], epts.type_key)
        self.assertEqual(data['name'], epts.name_key)

        validate_attributes = [
            'enabled_key',
            'public_url',
            'internal_url',
            'admin_url',
            'tenant_alias',
            'version_id',
            'version_info',
            'version_list'
        ]
        for epts_attribute in validate_attributes:
            actual_value = getattr(epts, epts_attribute)
            default_value, data_name = self.get_optional_mapping_value(
                epts,
                epts_attribute
            )
            if use_defaults:
                self.assertEqual(
                    actual_value,
                    default_value
                )
            else:
                self.assertEqual(
                    actual_value,
                    data[data_name]
                )

    def test_basic_no_dict(self):
        """
        Check the default state where all values should be set to `None`.
        """
        epts = EndpointTemplateStore()
        self.assertIsNone(epts._template_data)
        self.assertIsNone(epts.id_key)
        self.assertIsNone(epts.region_key)
        self.assertIsNone(epts.type_key)
        self.assertIsNone(epts.name_key)
        self.assertIsNone(epts.enabled_key)
        self.assertIsNone(epts.public_url)
        self.assertIsNone(epts.internal_url)
        self.assertIsNone(epts.admin_url)
        self.assertIsNone(epts.tenant_alias)
        self.assertIsNone(epts.version_id)
        self.assertIsNone(epts.version_info)
        self.assertIsNone(epts.version_list)

    def test_basic_with_minimal_dict(self):
        """
        Check setting up the template with the minimal mappings.
        """
        data = {
            "id": "some-id",
            "region": "some-region",
            "type": "some-type",
            "name": "some-name"
        }
        epts = EndpointTemplateStore(data)
        self.validate_mapping(epts, data, True)

    def test_deserialize_minimal_invalid(self):
        """
        Check missing one of the minimal values will raise an exception.
        """
        data = {
            "id": "some-id",
            "type": "some-type",
            "name": "some-name"
        }
        with self.assertRaises(KeyError):
            EndpointTemplateStore(data)

    def test_deserialization(self):
        """
        Check deserialization correctly maps the values to the object.
        """
        data = {
            "id": "some-id",
            "region": "some-region",
            "type": "some-type",
            "name": "some-name",
            "enabled": True,
            "publicURL": "http://public.url",
            "internalURL": "http://internal.url",
            "adminURL": "http://admin.internal.url",
            "RAX-AUTH:tenantAlias": "{{tenant_id}}",
            "versionId": "http://some.url/version",
            "versionInfo": "http://some.url/version/info",
            "versionList": "http://some.url/version/list"
        }
        epts = EndpointTemplateStore(data)
        self.validate_mapping(epts, data, False)

    def test_serialize_basic(self):
        """
        Serializing the minimal data will result in the correct dict object.
        """
        data = {
            "id": "some-id",
            "region": "some-region",
            "type": "some-type",
            "name": "some-name"
        }
        epts = EndpointTemplateStore()
        epts.id_key = data['id']
        epts.region_key = data['region']
        epts.type_key = data['type']
        epts.name_key = data['name']
        serialized_data = epts.serialize()
        for k, v in serialized_data.items():
            if k not in data:
                self.assertIsNone(v)
            else:
                self.assertEqual(v, data[k])

    def test_serialize_complete(self):
        """
        Serializing the full data will result in the correct dict object.
        """
        data = {
            "id": "some-id",
            "region": "some-region",
            "type": "some-type",
            "name": "some-name",
            "enabled": True,
            "publicURL": "http://public.url",
            "internalURL": "http://internal.url",
            "adminURL": "http://admin.internal.url",
            "RAX-AUTH:tenantAlias": "{{tenant_id}}",
            "versionId": "http://some.url/version",
            "versionInfo": "http://some.url/version/info",
            "versionList": "http://some.url/version/list"
        }
        epts = EndpointTemplateStore(data)
        serialized_data = epts.serialize()
        self.assertEqual(data, serialized_data)

    def test_serialize_tenant(self):
        """
        Serializing for a tenant with the full data will give the dict object.
        """
        tenant_id = "some-tenant"
        data = {
            "id": "some-id",
            "region": "some-region",
            "type": "some-type",
            "name": "some-name",
            "enabled": True,
            "publicURL": "http://public.url",
            "internalURL": "http://internal.url",
            "adminURL": None,
            "RAX-AUTH:tenantAlias": "{{tenant_id}}",
            "versionId": "http://some.url/version",
            "versionInfo": "http://some.url/version/info",
            "versionList": "http://some.url/version/list"
        }
        expected_result = {
            "id": data['id'],
            "tenantId": tenant_id,
            "region": data['region'],
            "type": data['type'],
            "publicURL": data['publicURL'],
            "internalURL": data['internalURL'],
        }

        epts = EndpointTemplateStore(data)
        serialized_data = epts.serialize(tenant_id=tenant_id)
        self.assertEqual(expected_result, serialized_data)

    def test_replace_tenant_id_default_replacement(self):
        """
        Serializing for a tenant with the default tenantid spec will result
        in the correct URLs being generated.
        """
        tenant_id = "some-tenant"
        final_public_url = "http://public.url/" + tenant_id
        final_internal_url = "http://internal.url/" + tenant_id

        data = {
            "id": "some-id",
            "region": "some-region",
            "type": "some-type",
            "name": "some-name",
            "enabled": True,
            "publicURL": "http://public.url/%tenant_id%",
            "internalURL": "http://internal.url/%tenant_id%",
            "adminURL": None,
            "RAX-AUTH:tenantAlias": None,
            "versionId": "http://some.url/version",
            "versionInfo": "http://some.url/version/info",
            "versionList": "http://some.url/version/list"
        }

        epts = EndpointTemplateStore(data)
        self.assertEqual(
            final_public_url,
            epts.get_url(
                epts.public_url,
                tenant_id
            )
        )
        self.assertEqual(
            final_internal_url,
            epts.get_url(
                epts.internal_url,
                tenant_id
            )
        )

    def test_replace_tenant_id_user_replacement(self):
        """
        Serializing for a tenant with a user specified tenantid spec will
        result in the correct URLs being generated.
        """
        tenant_id = "some-tenant"
        final_public_url = "http://public.url/" + tenant_id
        final_internal_url = "http://internal.url/" + tenant_id

        data = {
            "id": "some-id",
            "region": "some-region",
            "type": "some-type",
            "name": "some-name",
            "enabled": True,
            "publicURL": "http://public.url/{{tenant_id}}",
            "internalURL": "http://internal.url/{{tenant_id}}",
            "adminURL": None,
            "RAX-AUTH:tenantAlias": "{{tenant_id}}",
            "versionId": "http://some.url/version",
            "versionInfo": "http://some.url/version/info",
            "versionList": "http://some.url/version/list"
        }

        epts = EndpointTemplateStore(data)
        self.assertEqual(
            final_public_url,
            epts.get_url(
                epts.public_url,
                tenant_id
            )
        )
        self.assertEqual(
            final_internal_url,
            epts.get_url(
                epts.internal_url,
                tenant_id
            )
        )


class EndpointTemplatesTests(SynchronousTestCase):
    """
    Test Endpoint Template Functionality: list, add, has, update, remove.
    """
    def setUp(self):
        self.eeapi_name = u"externalServiceName"

    def test_listing_templates(self):
        """
        Listing templates provides entries and changes as expected.
        Template status is not dependant on whether or not the template is enabled.
        """
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

    def test_listing_templates_tenant(self):
        """
        Listing templates for a tenant provides entries and changes as expected.
        Template status is dependant on whether or not the template is enabled;
        this test works the same as the global test.
        """
        tenant_id = 'some-tenant'
        eeapi_template_id = 'some-template-id'
        eeapi_template = ExampleEndpointTemplate(
            name=self.eeapi_name,
            uuid=eeapi_template_id,
        )
        eeapi = make_example_external_api(
            self,
            name=self.eeapi_name,
            endpoint_templates=[eeapi_template],
            set_enabled=True
        )

        listing = [ept for ept in eeapi.list_tenant_templates(tenant_id)]
        self.assertEqual(len(listing), 1)
        eeapi.remove_template(eeapi_template_id)
        new_listing = [ept for ept in eeapi.list_tenant_templates(tenant_id)]
        self.assertEqual(len(new_listing), 0)

    def test_listing_templates_tenant_with_specific_enabled(self):
        """
        Listing templates for a tenant provides entries and changes as expected.
        Template status is dependant on whether or not the template is enabled;
        this disables the template instead of removing it.
        """
        tenant_id = 'some-tenant'
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
        eeapi.enable_endpoint_for_tenant(tenant_id, eeapi_template_id)

        listing = [ept for ept in eeapi.list_tenant_templates(tenant_id)]
        self.assertEqual(len(listing), 1)
        eeapi.disable_endpoint_for_tenant(tenant_id, eeapi_template_id)
        new_listing = [ept for ept in eeapi.list_tenant_templates(tenant_id)]
        self.assertEqual(len(new_listing), 0)

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

    def test_add_template_with_mismatching_service_type(self):
        """
        Validate that adding a template the service type must match
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
        new_eeapi_template.type_key = "random-type"

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

    def test_update_endpoint_template_invalid_type_value(self):
        """
        Validate that the :obj:`ExternalApiStore` will raise the `IndexError`
        exception if the template id is not found when doing an update; in
        otherwords, update != (update or add).
        """
        new_url = "https://api.new_region.example.com:9090"
        new_region = "NEW_REGION"
        eeapi = make_example_external_api(
            self,
            name=self.eeapi_name,
            set_enabled=True,
        )
        new_eeapi_template = ExampleEndpointTemplate(
            name=self.eeapi_name,
            uuid=get_template_id(self, eeapi),
            region=new_region,
            url=new_url
        )
        new_eeapi_template.type_key = "some-other-type"

        with self.assertRaises(ValueError):
            eeapi.update_template(new_eeapi_template)

    def test_update_endpoint_template_invalid_id_value(self):
        """
        Validate that the :obj:`ExternalApiStore` will raise the `IndexError`
        exception if the template id is not found when doing an update; in
        otherwords, update != (update or add).
        """
        new_url = "https://api.new_region.example.com:9090"
        new_region = "NEW_REGION"
        eeapi = make_example_external_api(
            self,
            name=self.eeapi_name,
            set_enabled=True,
        )
        old_eeapi_template_id = get_template_id(self, eeapi)
        new_eeapi_template_id = u"uuid-alternate-endpoint-template"
        new_eeapi_template = ExampleEndpointTemplate(
            name=self.eeapi_name,
            uuid=old_eeapi_template_id,
            region=new_region,
            url=new_url
        )
        eeapi.endpoint_templates[old_eeapi_template_id].id_key = \
            new_eeapi_template_id

        with self.assertRaises(ValueError):
            eeapi.update_template(new_eeapi_template)

    def test_has_endpoint_template_invalid(self):
        """
        Validate that :obj:`ExternalApiStore` will return False if it
        does not have the template id
        """
        eeapi = make_example_external_api(
            self
        )
        self.assertFalse(
            eeapi.has_template('some-template-id')
        )

    def test_has_endpoint_template(self):
        """
        Validate that :obj:`ExternalApiStore` will return True if it
        does have the template id
        """
        eeapi = make_example_external_api(
            self
        )
        ept_template_id = get_template_id(self, eeapi)
        self.assertTrue(
            eeapi.has_template(ept_template_id)
        )

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
