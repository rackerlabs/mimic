
from json import dumps

from twisted.trial.unittest import SynchronousTestCase
from twisted.internet.task import Clock

import treq

from mimic.rest.swift_api import SwiftMock
from mimic.resource import MimicRoot
from mimic.core import MimicCore
from mimic.test.helpers import request


class SwiftTests(SynchronousTestCase):
    """
    tests for swift API
    """

    def test_service_catalog(self):
        """
        When provided with a :obj:`SwiftMock`, :obj:`MimicCore` yields a
        service catalog containing a swift endpoint.
        """
        core = MimicCore(Clock(), [SwiftMock()])
        root = MimicRoot(core).app.resource()
        response = request(self, root, "POST", "/identity/v2.0/tokens",
                           dumps({
                               "auth": {
                                   "passwordCredentials": {
                                       "username": "test1",
                                       "password": "test1password"
                                   }
                               }
                           }))
        responseNow = self.successResultOf(response)
        self.assertEqual(responseNow.code, 200)
        jsonBody = self.successResultOf(treq.json_content(responseNow))
        self.assertTrue(jsonBody)
        # FIXME: assert something about the actual correctness of this data.
