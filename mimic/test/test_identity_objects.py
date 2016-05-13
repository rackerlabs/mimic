from __future__ import absolute_import, division, unicode_literals

from twisted.trial.unittest import SynchronousTestCase

from mimic.model.identity_objects import (
    forbidden,
    EndpointTemplateStore
)
from mimic.test.dummy import (
    ExampleEndpointTemplate,
    make_example_external_api
)


class YetToBeDone(SynchronousTestCase):
    """
    Test that are a placeholder for necessary functionality
    that will be needed when the full functionality is implemented.
    """

    def test_stuff_todo(self):
        """
        Temporary for code-coverage until endpoints are
        implemented that will actually use these.
        """
        class reqMock(object):
            def setResponseCode(self, code):
                pass

        forbidden("testing forbidden", reqMock())


class ValidateEndpointTemplateInstance(SynchronousTestCase):
    """
    Validate the :obj:`EndpointTemplateStore`
    """
    @staticmethod
    def get_optional_mapping_value(epts, attribute_name):
        for tname, name, value in epts.optional_mapping:
            if name == attribute_name:
                return (value, tname)

    def validate_mapping(self, epts, data, use_defaults):
        self.assertEqual(data, epts._template_data)
        self.assertEqual(data['id'], epts.id_key)
        self.assertEqual(data['region'], epts.region_key)
        self.assertEqual(data['type'], epts.type_key)
        self.assertEqual(data['name'], epts.name_key)

        validate_attributes = [
            'enabled_key',
            'publicURL',
            'internalURL',
            'adminURL',
            'tenantAlias',
            'versionId',
            'versionInfo',
            'versionList'
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
        epts = EndpointTemplateStore()
        self.assertIsNone(epts._template_data)
        self.assertIsNone(epts.id_key)
        self.assertIsNone(epts.region_key)
        self.assertIsNone(epts.type_key)
        self.assertIsNone(epts.name_key)
        self.assertIsNone(epts.enabled_key)
        self.assertIsNone(epts.publicURL)
        self.assertIsNone(epts.internalURL)
        self.assertIsNone(epts.adminURL)
        self.assertIsNone(epts.tenantAlias)
        self.assertIsNone(epts.versionId)
        self.assertIsNone(epts.versionInfo)
        self.assertIsNone(epts.versionList)

    def test_basic_with_minimal_dict(self):
        data = {
            "id": "some-id",
            "region": "some-region",
            "type": "some-type",
            "name": "some-name"
        }
        epts = EndpointTemplateStore(data)
        self.validate_mapping(epts, data, True)

    def test_deserialize_minimal_invalid(self):
        data = {
            "id": "some-id",
            "type": "some-type",
            "name": "some-name"
        }
        with self.assertRaises(KeyError):
            EndpointTemplateStore(data)

    def test_deserialization(self):
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


class ValidateEndpointTemplates(SynchronousTestCase):
    """
    Validate on Endpoint Template Additions
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
            name=self.eeapi_name,
            set_enabled=True
        )

        class InvalidTemplate(object):
            pass

        with self.assertRaises(TypeError):
            eeapi.add_template(InvalidTemplate())

    def test_duplicate_api_insertion_fails(self):
        """
        Validate only one template for by a given name (id) can
        be added at a time.
        """
        eeapi = make_example_external_api(
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
        class InvalidTemplate(object):
            pass

        eeapi = make_example_external_api(
            name=self.eeapi_name,
            set_enabled=True,
        )

        with self.assertRaises(TypeError):
            eeapi.update_template(InvalidTemplate())

    def test_update_endpoint_template(self):
        new_url = "https://api.new_region.example.com:9090"
        new_region = "NEW_REGION"
        new_eeapi_template_id = u"uuid-alternate-endpoint-template"
        old_eeapi_template = ExampleEndpointTemplate(
            name=self.eeapi_name,
            uuid=new_eeapi_template_id,
            region=new_region,
        )
        new_eeapi_template = ExampleEndpointTemplate(
            name=self.eeapi_name,
            uuid=new_eeapi_template_id,
            region=new_region,
            url=new_url
        )
        eeapi = make_example_external_api(
            name=self.eeapi_name,
            set_enabled=True,
            endpoint_templates=[old_eeapi_template]
        )

        eeapi.update_template(new_eeapi_template)

    def test_update_endpoint_template_invalid(self):
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
            name=self.eeapi_name,
            set_enabled=True,
        )

        with self.assertRaises(IndexError):
            eeapi.update_template(new_eeapi_template)

    def test_remove_endpoint_template_invalid(self):
        eeapi = make_example_external_api(
            name=self.eeapi_name,
            set_enabled=True,
        )

        with self.assertRaises(IndexError):
            eeapi.remove_template("some-invalid-template-id")

    def test_remove_enpoint_template(self):
        eeapi_template_id = u"uuid-alternate-endpoint-template"
        eeapi_template = ExampleEndpointTemplate(
            name=self.eeapi_name,
            uuid=eeapi_template_id
        )
        eeapi = make_example_external_api(
            name=self.eeapi_name,
            set_enabled=True,
            endpoint_templates=[eeapi_template]
        )

        eeapi.remove_template(eeapi_template_id)

    def test_remove_enpoint_template_with_user_registration(self):
        eeapi_template_id = u"uuid-alternate-endpoint-template"
        eeapi_template = ExampleEndpointTemplate(
            name=self.eeapi_name,
            uuid=eeapi_template_id
        )
        eeapi = make_example_external_api(
            name=self.eeapi_name,
            set_enabled=True,
            endpoint_templates=[eeapi_template]
        )
        eeapi.enable_endpoint_for_tenant(
            'some-tenant',
            eeapi_template_id
        )

        eeapi.remove_template(eeapi_template_id)

    def test_remove_enpoint_template_with_user_registration_alternate(self):
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

        eeapi.remove_template(eeapi_template_id)


class EndpointsForTenants(SynchronousTestCase):
    """
    Tests for functionality specific to tenants
    """
    def setUp(self):
        self.eeapi_name = u"externalServiceName"

    def test_invalid_template_endpoint_enable(self):
        """
        Validate enabling an invalid endpoint template
        for a user raises ValueError
        """
        eeapi = make_example_external_api(
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
        Validate disabling an invalid endpoint template
        for a user raises ValueError
        """
        eeapi = make_example_external_api(
            name=self.eeapi_name,
            set_enabled=True
        )

        with self.assertRaises(ValueError):
            eeapi.disable_endpoint_for_tenant(
                'some_tenant',
                'some-invalid-template-id'
            )

    def test_disable_endpoint_template_for_tenant(self):
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
            name=self.eeapi_name,
            set_enabled=True,
            endpoint_templates=[new_eeapi_template]
        )
        eeapi.enable_endpoint_for_tenant(
            'some-tenant',
            new_eeapi_template_id
        )
        eeapi.disable_endpoint_for_tenant(
            'some-tenant',
            new_eeapi_template_id
        )


class EndpointTemplateOperations(SynchronousTestCase):
    """
    Tests for creating a :class:`MimicCore` object with apis
    """
    def setUp(self):
        self.eeapi_name = u"externalServiceName"

    def test_uri_for_service_with_invalid_region(self):
        eeapi = make_example_external_api(
            name=self.eeapi_name,
            set_enabled=True
        )

        with self.assertRaises(IndexError):
            eeapi.uri_for_service('Open', 'Stack')
