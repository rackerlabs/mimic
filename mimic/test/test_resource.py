import json
import re

from functools import partial

from twisted.internet.task import Clock
from twisted.trial.unittest import SynchronousTestCase

# We can just import from twisted.logger once mimic drops support for
# twisted < 15.2.0
try:
    from twisted.logger.globalLogPublisher import addObserver, removeObserver
except ImportError:
    from twisted.python.log import addObserver, removeObserver

try:
    from twisted.logger import formatEvent as get_log_message
except ImportError:
    from twisted.python.log import textFromEventDict as get_log_message

from mimic.canned_responses.mimic_presets import get_presets
from mimic.core import MimicCore
from mimic.resource import MimicRoot, get_site
from mimic.test.dummy import ExampleAPI
from mimic.test import helpers

json_request = helpers.json_request
request = helpers.request
request_with_content = helpers.request_with_content


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
        expected = {
            'advanced': 3.6,
            'now': '1970-01-01T00:00:03.600000Z',
        }
        self.assertEqual(json_content, expected)
        self.assertEqual(do.done, True)

    def test_fastly(self):
        """
        The /fastly pointing to the fastly endpoint
        """
        core = MimicCore(Clock(), [])
        root = MimicRoot(core).app.resource()

        (response, json_content) = self.successResultOf(json_request(
            self, root, 'GET', '/fastly'))
        self.assertEqual(200, response.code)
        self.assertEqual(json_content, {'status': 'ok'})

    def test_send_grid(self):
        """
        ``/sendgrid/mail.send.json`` returns response code 200.
        """
        core = MimicCore(Clock(), [])
        root = MimicRoot(core).app.resource()

        response = self.successResultOf(request(
            self, root, "POST", "/sendgrid/mail.send.json"))
        self.assertEqual(200, response.code)


class RequestTests(SynchronousTestCase):
    """
    Tests for :obj:`mimic.resource.MimicRequest` and
    :obj:`mimic.resource.MimicRequest`, and :obj:`mimic.resource.get_site`.
    """
    def make_request_to_site(self):
        """
        Make a request and return the response.
        """
        core = MimicCore(Clock(), [ExampleAPI('response!')])
        root = MimicRoot(core).app.resource()

        # get the region and service id registered for the example API
        (region, service_id) = one_api(self, core)
        url = "/mimicking/{0}/{1}".format(service_id, region)
        response = self.successResultOf(request(
            self, root, "GET", url, headers={"one": ["two"]}
        ))
        return (response, url)

    def test_default_content_type(self):
        """
        The default content type of all Mimic responses is application/json.
        """
        response, _ = self.make_request_to_site()
        self.assertEqual(['application/json'],
                         response.headers.getRawHeaders('content-type'))

    def test_verbose_logging(self):
        """
        If verbose logging is turned on, the full request and response is
        logged.
        """
        self.patch(helpers, 'get_site', partial(get_site, logging=True))
        logged_events = []
        addObserver(logged_events.append)
        self.addCleanup(removeObserver, logged_events.append)

        response, url = self.make_request_to_site()

        self.assertEqual(2, len(logged_events))
        self.assertTrue(all([not event['isError'] for event in logged_events]))

        messages = [get_log_message(event) for event in logged_events]

        request_match = re.compile(
            "^Received request: GET (?P<url>.+)\n"
            "Headers: (?P<headers>\{.+\})\n\s*$"
        ).match(messages[0])
        self.assertNotEqual(None, request_match)
        self.assertEqual(url, request_match.group('url'))
        headers = json.loads(request_match.group('headers'))
        self.assertEqual(['two'], headers.get('One'))

        response_match = re.compile(
            "^Responding with 200 for: GET (?P<url>.+)\n"
            "Headers: (?P<headers>\{.+\})\n"
            "\nresponse\!\n\s*$"
        ).match(messages[1])
        self.assertNotEqual(None, response_match)
        self.assertEqual(url, response_match.group('url'))
        headers = json.loads(response_match.group('headers'))
        self.assertEqual(['application/json'], headers.get('Content-Type'))
