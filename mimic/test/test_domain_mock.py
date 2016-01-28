from twisted.internet.task import Clock
from twisted.trial.unittest import SynchronousTestCase

import treq

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
        A GET on ``http://mimic-host.example.com:port/domain`` should return
        the list of all the domains; empty, if no plugins are registered.
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
        return the list of all the domains, enumerating all registered plugins.
        """
        example_domain_api = ExampleDomainAPI()
        core = MimicCore(Clock(), [], [example_domain_api])
        root = MimicRoot(core).app.resource()

        response, content = self.successResultOf(json_request(
            self, root, b"GET",
            "http://mybase/domain"))
        self.assertEqual(200, response.code)
        self.assertEqual(content, [u'api.example.com'])

    def test_domain_mock_child(self):
        """
        Any request to ``http://mimic-host.example.com:port/domain/<a-domain>``
        should be fielded by the :obj:`IAPIDomainMock` which returns
        ``<a-domain>`` from its ``domain()`` method.
        """
        example_domain_api = ExampleDomainAPI()
        core = MimicCore(Clock(), [], [ExampleDomainAPI(u'api2.example.com',
                                                        b'"other-value"'),
                                       example_domain_api])
        root = MimicRoot(core).app.resource()
        response, content = self.successResultOf(json_request(
            self, root, b"GET",
            "http://mybase/domain/api.example.com/"))
        self.assertEqual(200, response.code)
        self.assertEqual(content, u'test-value')

    def test_domain_mock_no_child(self):
        """
        A GET on
        ``http://mimic-host.example.com:port/domain/non-existent.example.com``
        should return a 404 status assuming that there is no registered domain
        mock with that name.
        """
        example_domain_api = ExampleDomainAPI()
        core = MimicCore(Clock(), [], [example_domain_api])
        root = MimicRoot(core).app.resource()

        response = self.successResultOf(request(
            self, root, b"GET",
            b"http://mybase/domain/nope.example.com"))
        self.assertEqual(404, response.code)
        self.assertEqual(self.successResultOf(treq.content(response)),
                         b"No such domain.")
