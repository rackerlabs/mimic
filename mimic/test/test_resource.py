
from twisted.internet.task import Clock
from twisted.trial.unittest import SynchronousTestCase

from mimic.core import MimicCore
from mimic.resource import MimicRoot
from mimic.test.dummy import ExampleAPI
from mimic.test.helpers import request


class PluginResourceTests(SynchronousTestCase):
    """
    Tests for ``/service/*`` endpoints.
    """
    def test_child_resource_gets_base_uri_from_request(self):
        """
        A session is created for the token provided
        """
        example = ExampleAPI()

        core = MimicCore(Clock(), [example])
        root = MimicRoot(core).app.resource()

        # get the region and service id registered for the example API
        (region, service_id) = core.uri_prefixes.keys()[0]

        request(
            self, root, "GET",
            "http://mybase/service/{0}/{1}/more/stuff".format(region,
                                                              service_id)
        )

        self.assertEqual(
            "http://mybase/service/{0}/{1}/".format(region, service_id),
            example.store['uri_prefix'])
