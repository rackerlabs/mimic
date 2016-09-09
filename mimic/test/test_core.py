from __future__ import absolute_import, division, unicode_literals

import sys
import uuid

from zope.interface import implementer

from twisted.internet.task import Clock
from twisted.trial.unittest import SynchronousTestCase
from twisted.plugin import IPlugin
from twisted.python.filepath import FilePath
from twisted.web.resource import IResource

from mimic.core import (
    MimicCore,
    ServiceBadInterface,
    ServiceDoesNotExist,
    ServiceExists,
    ServiceHasTemplates,
    ServiceNameExists
)
from mimic.plugins import (nova_plugin, loadbalancer_plugin, swift_plugin,
                           queue_plugin, maas_plugin, rackconnect_v3_plugin,
                           glance_plugin, cloudfeeds_plugin, heat_plugin,
                           neutron_plugin, dns_plugin, cinder_plugin)
from mimic.test.dummy import (
    exampleEndpointTemplate,
    make_example_internal_api,
    make_example_external_api
)
from mimic.test.fixtures import APIMockHelper


class CoreBuildingPluginsTests(SynchronousTestCase):
    """
    Tests for creating a :class:`MimicCore` object with plugins.
    """
    def test_no_uuids_if_no_plugins(self):
        """
        If there are no plugins provided to :class:`MimicCore`, there are no
        uri prefixes or entries for the tenant.
        """
        core = MimicCore(Clock(), [])
        self.assertEqual(0, len(core._uuid_to_api_internal))
        self.assertEqual(0, len(core._uuid_to_api_external))
        self.assertEqual([], list(core.entries_for_tenant('any_tenant', {},
                                                          'http://mimic')))

    def test_from_plugin_includes_all_plugins(self):
        """
        Using the :func:`MimicRoot.fromPlugin` creator for a
        :class:`MimicCore`, the nova and loadbalancer plugins are included.
        """
        core = MimicCore.fromPlugins(Clock())
        plugin_apis = set((
            glance_plugin.glance,
            heat_plugin.heat,
            loadbalancer_plugin.loadbalancer,
            loadbalancer_plugin.loadbalancer_control,
            maas_plugin.maas,
            maas_plugin.maas_control,
            nova_plugin.nova,
            nova_plugin.nova_control_api,
            queue_plugin.queue,
            rackconnect_v3_plugin.rackconnect,
            swift_plugin.swift,
            cloudfeeds_plugin.cloudfeeds,
            cloudfeeds_plugin.cloudfeeds_control,
            neutron_plugin.neutron,
            dns_plugin.dns,
            cinder_plugin.cinder
        ))
        # all plugins should be on the internal listing
        self.assertEqual(
            plugin_apis,
            set(core._uuid_to_api_internal.values()))
        # the external listing should still be empty
        self.assertEqual(
            set([]),
            set(core._uuid_to_api_external.values()))

    def test_load_domain_plugin_includes_all_domain_plugins(self):
        """
        Using the :func:`MimicRoot.fromPlugin` creator for a
        :class:`MimicCore`, domain mocks implementing `class`:`IAPIDomainMock`
        are included.
        """
        self.root = FilePath(self.mktemp())
        self.root.createDirectory()
        plugin = b"""from mimic.test.dummy import ExampleDomainAPI
dummy_domain_plugin = ExampleDomainAPI()
"""
        self.root.child('fake_plugin.py').setContent(plugin)

        import mimic.plugins
        mimic.plugins.__path__.append(self.root.path)
        from mimic.plugins import fake_plugin

        def cleanup():
            sys.modules.pop("mimic.plugins.fake_plugin")
            del mimic.plugins.fake_plugin
        self.addCleanup(cleanup)

        core = MimicCore.fromPlugins(Clock())
        self.assertIn(
            fake_plugin.dummy_domain_plugin,
            core.domains
        )


class CoreApiBuildingTests(SynchronousTestCase):
    """
    Tests for creating a :class:`MimicCore` object with apis.
    """
    def setUp(self):
        self.eeapi_name = u"externalServiceName"

    def test_load_external_api(self):
        """
        Validate loading a valid external API object.
        """
        eeapi = make_example_external_api(
            self,
            name=self.eeapi_name,
            set_enabled=True
        )
        APIMockHelper(self, [eeapi])

    def test_load_internal_api(self):
        """
        Validate loading a valid internal API object.
        """
        APIMockHelper(self, [make_example_internal_api(self)])

    def test_load_invalid_api(self):
        """
        Using a dummy interface that implements :obj:`IPlugin`, try to add an
        object that does not implement either :obj:`IAPIMock` or
        :obj:`IExternalAPIMock`.
        """
        @implementer(IPlugin)
        class brokenApiMock(object):
            pass

        with self.assertRaises(ServiceBadInterface):
            MimicCore(Clock(), [brokenApiMock()])

    def test_load_duplicate_api_uuid(self):
        """
        Adding an API with the same UUID as an existing API will generate a
        ValueError exception.
        """
        eeapi = make_example_external_api(
            self,
            name=self.eeapi_name,
        )
        eeapi2 = make_example_external_api(
            self,
            name="alternate " + self.eeapi_name
        )
        eeapi2.uuid_key = eeapi.uuid_key

        with self.assertRaises(ServiceExists):
            MimicCore(Clock(), [eeapi, eeapi2])

    def test_load_duplicate_api_name(self):
        """
        Adding an API with the same Name as an existing API will generate a
        ValueError exception.
        """
        eeapi = make_example_external_api(
            self,
            name=self.eeapi_name,
        )
        eeapi2 = make_example_external_api(
            self,
            name=self.eeapi_name
        )
        # .. note:: make_example_external_api makes the UUID
        # to be uuid-<name> so we need to change it for eeapi2
        eeapi2.uuid_key = str(uuid.uuid4())

        with self.assertRaises(ServiceNameExists):
            MimicCore(Clock(), [eeapi, eeapi2])

    def test_remove_api(self):
        """
        Removing an API.
        """
        eeapi = make_example_external_api(
            self,
            name=self.eeapi_name,
            set_enabled=True
        )
        self.assertIsNotNone(eeapi)

        template_ids = [ept.id_key for ept in eeapi.list_templates()]
        for template_id in template_ids:
            eeapi.remove_template(template_id)

        core = MimicCore(Clock(), [eeapi])
        core.remove_external_api(
            eeapi.uuid_key
        )

    def test_remove_api_invalid(self):
        """
        Validate API removal fails when it does not find the
        api name in the listing
        """
        core = MimicCore(Clock(), [])
        with self.assertRaises(ServiceDoesNotExist):
            core.remove_external_api(
                'some-id'
            )

    def test_remove_api_with_endpoints(self):
        """
        Validate an API cannot be removed if it still has
        endpoints assigned to it
        """
        eeapi = make_example_external_api(
            self,
            name=self.eeapi_name,
            set_enabled=True
        )
        self.assertIsNotNone(eeapi)
        core = MimicCore(Clock(), [eeapi])
        with self.assertRaises(ServiceHasTemplates):
            core.remove_external_api(
                eeapi.uuid_key
            )

    def test_get_external_apis(self):
        """
        Validate retrieving the list of external APIs
        """
        eeapi = make_example_external_api(
            self,
            name=self.eeapi_name,
            set_enabled=True
        )

        core = MimicCore(Clock(), [])
        self.assertEqual(len(core.get_external_apis()), 0)

        core.add_api(eeapi)
        api_list = core.get_external_apis()
        self.assertEqual(len(api_list), 1)
        self.assertEqual(list(api_list), [eeapi.uuid_key])

    def test_get_external_api(self):
        """
        Validate retrieving an external API.
        """
        eeapi = make_example_external_api(
            self,
            name=self.eeapi_name,
            set_enabled=True
        )

        core = MimicCore(Clock(), [eeapi])
        api_from_core = core.get_external_api(
            eeapi.uuid_key
        )
        self.assertEqual(eeapi, api_from_core)

    def test_get_external_api_invalid(self):
        """
        Validate retrieving a non-existent external API which should raise an
        `IndexError` exception.
        """
        core = MimicCore(Clock(), [])
        with self.assertRaises(ServiceDoesNotExist):
            core.get_external_api(self.eeapi_name)

    def test_service_with_region_external(self):
        """
        Validate that an external service does not provide an internal
        service resource.
        """
        eeapi = make_example_external_api(
            self,
            name=self.eeapi_name,
            set_enabled=True
        )
        helper = APIMockHelper(self, [eeapi])
        core = helper.core

        self.assertIsNone(
            core.service_with_region(
                u"EXTERNAL",
                u"some-region-name",
                u"http://some/random/prefix"
            )
        )

    def test_service_with_region_internal(self):
        """
        Validate that an external service does not provide an internal service
        resource.
        """
        iapi = make_example_internal_api(self)
        helper = APIMockHelper(self, [iapi])
        core = helper.core

        service_id = None
        for a_service_id in core._uuid_to_api_internal:
            if core._uuid_to_api_internal[a_service_id] == iapi:
                service_id = a_service_id

        resource = core.service_with_region(
            u"ORD",
            service_id,
            u"http://some/random/prefix"
        )
        self.assertTrue(
            IResource.providedBy(resource)
        )

    def test_uri_for_service(self):
        """
        Validate that the URI returned by uri_for_service returns the
        appropriate base URI.
        """
        iapi = make_example_internal_api(self)
        helper = APIMockHelper(self, [iapi])
        core = helper.core

        service_id = None
        for a_service_id in core._uuid_to_api_internal:
            if core._uuid_to_api_internal[a_service_id] == iapi:
                service_id = a_service_id

        base_uri = "http://some/random/prefix"

        uri = core.uri_for_service(
            u"ORD",
            service_id,
            base_uri
        )
        self.assertTrue(
            uri.startswith(base_uri + '/')
        )

    def test_entries_for_tenant_external(self):
        """
        Validate that the external API shows up in the service catalog for a
        given tenant.
        """
        eeapi = make_example_external_api(
            self,
            name=self.eeapi_name,
            set_enabled=True
        )

        core = MimicCore(Clock(), [eeapi])

        prefix_map = {}
        base_uri = "http://some/random/prefix"
        catalog_entries = [
            entry
            for entry in core.entries_for_tenant(
                'some-tenant',
                prefix_map,
                base_uri
            )
        ]

        self.assertEqual(len(core._uuid_to_api_internal), 0)
        self.assertEqual(len(core._uuid_to_api_external), 1)
        self.assertEqual(len(catalog_entries), 1)
        self.assertEqual(catalog_entries[0].type, eeapi.type_key)
        self.assertEqual(catalog_entries[0].name, eeapi.name_key)
        self.assertEqual(catalog_entries[0].tenant_id, "some-tenant")
        self.assertEqual(len(catalog_entries[0].endpoints), 1)

    def test_entries_for_tenant_external_with_tenantid_replacement(self):
        """
        Validate that the external API shows up in the service catalog for a
        given tenant and the tenant id is in the URL.
        """
        eeapi = make_example_external_api(
            self,
            name=self.eeapi_name,
            set_enabled=True
        )

        tenant_id = 'some-tenant-other'

        ept_internal_url = "http://internal.url/v1/" + tenant_id
        ept_public_url = "http://public.url/v1/" + tenant_id
        for ept in eeapi.endpoint_templates.values():
            ept.internal_url = "http://internal.url/v1/%tenant_id%"
            ept.public_url = "http://public.url/v1/%tenant_id%"

        core = MimicCore(Clock(), [eeapi])

        prefix_map = {}
        base_uri = "http://some/random/prefix"
        catalog_entries = [
            entry
            for entry in core.entries_for_tenant(
                tenant_id,
                prefix_map,
                base_uri
            )
        ]

        self.assertEqual(len(core._uuid_to_api_internal), 0)
        self.assertEqual(len(core._uuid_to_api_external), 1)
        self.assertEqual(len(catalog_entries), 1)
        self.assertEqual(catalog_entries[0].type, eeapi.type_key)
        self.assertEqual(catalog_entries[0].name, eeapi.name_key)
        self.assertEqual(catalog_entries[0].tenant_id, tenant_id)
        self.assertEqual(len(catalog_entries[0].endpoints), 1)
        self.assertEqual(
            catalog_entries[0].endpoints[0].internal_url,
            ept_internal_url
        )
        self.assertEqual(
            catalog_entries[0].endpoints[0].complete_url,
            ept_public_url
        )

    def test_entries_for_tenant_internal(self):
        """
        Validate that the internal API shows up in the service catalog for a
        given tenant.
        """
        iapi = make_example_internal_api(self)
        core = MimicCore(Clock(), [iapi])

        prefix_map = {}
        base_uri = "http://some/random/prefix"
        catalog_entries = [
            entry
            for entry in core.entries_for_tenant(
                'some-tenant',
                prefix_map,
                base_uri
            )
        ]

        self.assertEqual(len(core._uuid_to_api_internal), 1)
        self.assertEqual(len(core._uuid_to_api_external), 0)
        self.assertEqual(len(catalog_entries), 1)
        self.assertEqual(catalog_entries[0].type, "serviceType")
        self.assertEqual(catalog_entries[0].name, "serviceName")
        self.assertEqual(catalog_entries[0].tenant_id, "some-tenant")
        self.assertEqual(len(catalog_entries[0].endpoints), 1)

    def test_entries_for_tenant_combined(self):
        """
        Validate that both internal and external APIs show up in the service
        catalog for a given tenant.
        """
        eeapi = make_example_external_api(
            self,
            name=self.eeapi_name,
            set_enabled=True
        )

        core = MimicCore(Clock(), [eeapi, make_example_internal_api(self)])

        prefix_map = {}
        base_uri = "http://some/random/prefix"
        catalog_entries = [
            entry
            for entry in core.entries_for_tenant(
                'some-tenant',
                prefix_map,
                base_uri
            )
        ]

        self.assertEqual(len(core._uuid_to_api_internal), 1)
        self.assertEqual(len(core._uuid_to_api_external), 1)
        self.assertEqual(len(catalog_entries), 2)

        found_internal = False
        found_external = False

        for catalog_entry in catalog_entries:
            if catalog_entry.name == eeapi.name_key:
                found_external = True
                self.assertEqual(catalog_entry.type, eeapi.type_key)
                self.assertEqual(catalog_entry.name, eeapi.name_key)
                self.assertEqual(catalog_entry.tenant_id, "some-tenant")
                self.assertEqual(len(catalog_entry.endpoints), 1)

            elif catalog_entry.name == "serviceName":
                found_internal = True
                self.assertEqual(catalog_entry.type, "serviceType")
                self.assertEqual(catalog_entry.name, "serviceName")
                self.assertEqual(catalog_entry.tenant_id, "some-tenant")
                self.assertEqual(len(catalog_entry.endpoints), 1)

        self.assertTrue(found_internal)
        self.assertTrue(found_external)

    def test_entries_for_tenant_external_multiple_regions(self):
        """
        Test with multiple regions for the External APIs.
        """
        iapi = make_example_internal_api(self)
        eeapi = make_example_external_api(
            self,
            name=self.eeapi_name,
            set_enabled=True
        )
        eeapi2_name = "alternate-external-api"
        eeapi2_template_id = u"uuid-alternate-endpoint-template"
        eeapi2_template = exampleEndpointTemplate(
            name=eeapi2_name,
            endpoint_uuid=eeapi2_template_id,
            region=u"NEW_REGION",
            url=u"https://api.new_region.example.com:9090"
        )
        eeapi2 = make_example_external_api(
            self,
            name=eeapi2_name,
            endpoint_templates=[eeapi2_template],
            set_enabled=True
        )

        core = MimicCore(Clock(), [eeapi, eeapi2, iapi])

        prefix_map = {}
        base_uri = "http://some/random/prefix"
        catalog_entries = [
            entry
            for entry in core.entries_for_tenant(
                'some-tenant',
                prefix_map,
                base_uri
            )
        ]

        self.assertEqual(len(core._uuid_to_api_internal), 1)
        self.assertEqual(len(core._uuid_to_api_external), 2)
        self.assertEqual(len(catalog_entries), 3)

        found_internal = False
        found_first_external = False
        found_second_external = False

        for catalog_entry in catalog_entries:
            if catalog_entry.name == eeapi.name_key:
                found_first_external = True
                self.assertEqual(catalog_entry.type, eeapi.type_key)
                self.assertEqual(catalog_entry.name, eeapi.name_key)
                self.assertEqual(catalog_entry.tenant_id, "some-tenant")
                self.assertEqual(len(catalog_entry.endpoints), 1)

            elif catalog_entry.name == eeapi2.name_key:
                found_second_external = True
                self.assertEqual(catalog_entry.type, eeapi2.type_key)
                self.assertEqual(catalog_entry.name, eeapi2.name_key)
                self.assertEqual(catalog_entry.tenant_id, "some-tenant")
                self.assertEqual(len(catalog_entry.endpoints), 1)

            elif catalog_entry.name == "serviceName":
                found_internal = True
                self.assertEqual(catalog_entry.type, "serviceType")
                self.assertEqual(catalog_entry.name, "serviceName")
                self.assertEqual(catalog_entry.tenant_id, "some-tenant")
                self.assertEqual(len(catalog_entry.endpoints), 1)

        self.assertTrue(found_internal)
        self.assertTrue(found_first_external)
        self.assertTrue(found_second_external)
