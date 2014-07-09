
from json import dumps

from twisted.trial.unittest import SynchronousTestCase
from twisted.internet.task import Clock

import treq

from mimic.rest.swift_api import SwiftMock
from mimic.resource import MimicRoot
from mimic.core import MimicCore
from mimic.rest.swift_api import normal_tenant_id_to_crazy_mosso_id
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
                                       "password": "test1password",
                                   },
                                   # TODO: should this really be 'tenantId'?
                                   "tenantName": "fun_tenant",
                               }
                           }))
        responseNow = self.successResultOf(response)
        self.assertEqual(responseNow.code, 200)
        jsonBody = self.successResultOf(treq.json_content(responseNow))
        self.assertTrue(jsonBody)
        sampleEntry = jsonBody['access']['serviceCatalog'][0]
        self.assertEqual(sampleEntry['type'], u'object-store')
        self.assertEqual(
            sampleEntry['endpoints'][0]['tenantId'],
            normal_tenant_id_to_crazy_mosso_id("fun_tenant")
        )
