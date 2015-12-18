from twisted.internet.task import Clock
from twisted.trial.unittest import SynchronousTestCase
from mimic.resource import MimicRoot
from mimic.test.helpers import request, json_request
from mimic.core import MimicCore
from mimic.test.dummy import ExampleDomainAPI


class TestDomainMock(SynchronousTestCase):
    """
    Test cases to verify the :obj:`IAPIDomainMock`.
    """

    def test_domain_mock(self):
        """
        A GET on the ``http://mimic-host.example.com:port/domain`` should
        return the list of all the domains.
        """

        core = MimicCore(Clock(), [])
        root = MimicRoot(core).app.resource()

        response = self.successResultOf(request(
            self, root, b"GET",
            "http://mybase/domain"))
        self.assertEqual(200, response.code)

    def test_domain_mock_with_an_example_mock(self):
        """
        A GET on the ``http://mimic-host.example.com:port/domain`` should
        return the list of all the domains.
        """
        example_domain_api = ExampleDomainAPI()
        core = MimicCore(Clock(), [], [example_domain_api])
        root = MimicRoot(core).app.resource()

        response, content = self.successResultOf(json_request(
            self, root, b"GET",
            "http://mybase/domain"))
        self.assertEqual(200, response.code)
        self.assertEqual(content, [u'api.example.com'])
