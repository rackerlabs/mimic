from twisted.internet.task import Clock
from twisted.trial.unittest import SynchronousTestCase

from mimic.canned_responses.mimic_presets import get_presets
from mimic.core import MimicCore
from mimic.resource import MimicRoot
from mimic.test.dummy import ExampleAPI
from mimic.test.helpers import json_request, request, request_with_content


def one_api(testCase, core):
    """
    Get the only API registered against a given MimicCore.

    :return: 2-tuple of ``region`` and ``service_id``
    """
    service_id, api = core._uuid_to_api.items()[0]
    region = api.catalog_entries(tenant_id=None)[0].endpoints[0].region
    return (region, service_id)


class ServiceResourceTests(SynchronousTestCase):
    """
    Tests for ``/service/*`` endpoints, handled by
    :func:`MimicRoot.get_service_resource`
    """
    def test_child_resource_gets_base_uri_from_request(self):
        """
        Whatever the URI is used to access mimic is the one that is passed
        back to the plugin when
        :func:`mimic.imimic.IAPMock.resource_for_region` is called.
        """
        example = ExampleAPI()

        core = MimicCore(Clock(), [example])
        root = MimicRoot(core).app.resource()

        # get the region and service id registered for the example API
        (region, service_id) = one_api(self, core)

        request(
            self, root, "GET",
            "http://mybase/mimicking/{0}/{1}/more/stuff".format(service_id, region)
        )

        self.assertEqual(
            "http://mybase/mimicking/{0}/{1}/".format(service_id, region),
            example.store['uri_prefix'])

    def test_service_endpoint_returns_404_if_wrong_service_id(self):
        """
        When the URI used to access a real service has the right region but
        wrong service ID, a 404 is returned and the resource for the service
        is accessed.
        """
        example = ExampleAPI()

        core = MimicCore(Clock(), [example])
        root = MimicRoot(core).app.resource()

        # get the region and service id registered for the example API
        (region, service_id) = one_api(self, core)

        response = self.successResultOf(request(
            self, root, "GET",
            "http://mybase/mimicking/not_{0}/{1}".format(service_id, region)
        ))
        self.assertEqual(404, response.code)
        self.assertEqual([], example.store.keys())

    def test_service_endpoint_returns_404_if_wrong_region(self):
        """
        When the URI used to access a real service has the right service ID
        but wrong service ID, a 404 is returned and the resource for the
        service is accessed.
        """
        example = ExampleAPI()

        core = MimicCore(Clock(), [example])
        root = MimicRoot(core).app.resource()

        # get the region and service id registered for the example API
        (region, service_id) = one_api(self, core)

        response = self.successResultOf(request(
            self, root, "GET",
            "http://mybase/mimicking/not_{0}/{1}".format(service_id, region)
        ))
        self.assertEqual(404, response.code)
        self.assertEqual([], example.store.keys())

    def test_service_endpoint_returns_service_resource(self):
        """
        When the URI used to access a real service has the right service ID
        and right region, the service's resource is used to respond to the
        request.
        """
        core = MimicCore(Clock(), [ExampleAPI('response!')])
        root = MimicRoot(core).app.resource()

        # get the region and service id registered for the example API
        (region, service_id) = one_api(self, core)

        (response, content) = self.successResultOf(request_with_content(
            self, root, "GET",
            "http://mybase/mimicking/{0}/{1}".format(service_id, region)
        ))
        self.assertEqual(200, response.code)
        self.assertEqual('response!', content)


class RootAndPresetTests(SynchronousTestCase):
    """
    Tests for ``/`` (handled by :func:`MimicRoot.help`) and
    ``/mimic/v1.0/presets`` (handled by :func:`MimicRoot.get_mimic_presets`)

    These are placeholder tests because these two endpoints don't do much yet.
    """
    def test_root(self):
        """
        The root (``/``, handled by :func:`MimicRoot.help`) has a bit of help
        text pointing to the identity endpoint
        """
        core = MimicCore(Clock(), [])
        root = MimicRoot(core).app.resource()

        (response, content) = self.successResultOf(request_with_content(
            self, root, 'GET', '/'))
        self.assertEqual(200, response.code)
        self.assertEqual(['text/plain'],
                         response.headers.getRawHeaders('content-type'))
        self.assertIn(' POST ', content)
        self.assertIn('/identity/v2.0/tokens', content)

    def test_presets(self):
        """
        ``/mimic/v1.0/presets`` (handled by
        :func:`MimicRoot.get_mimic_presets`), returns the presets as a JSON
        body with the right headers.
        """
        core = MimicCore(Clock(), [])
        root = MimicRoot(core).app.resource()

        (response, json_content) = self.successResultOf(json_request(
            self, root, 'GET', '/mimic/v1.0/presets'))
        self.assertEqual(200, response.code)
        self.assertEqual(['application/json'],
                         response.headers.getRawHeaders('content-type'))
        self.assertEqual(get_presets, json_content)


    def test_tick(self):
        """
        ``/mimic/v1.1/tick`` (handled by :func:`MimicRoot.advance_time`)
        advances the clock associated with the service.
        """
        clock = Clock()
        def do():
            do.done = True
        do.done = False
        clock.callLater(3.5, do)
        core = MimicCore(clock, [])
        root = MimicRoot(core, clock).app.resource()
        self.assertEqual(do.done, False)
        jreq = json_request(
            self, root, "POST", "/mimic/v1.1/tick", body={"amount": 3.6}
        )
        [response, json_content] = self.successResultOf(jreq)
        self.assertEqual(response.code, 200)
        self.assertEqual(json_content, {"tock": 3.6})
        self.assertEqual(do.done, True)

