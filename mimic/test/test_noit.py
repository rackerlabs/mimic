import uuid
import xmltodict
import treq
import json
from twisted.trial.unittest import SynchronousTestCase
from twisted.internet.task import Clock
from mimic.rest.noit_api import NoitApi
from mimic.core import MimicCore
from mimic.resource import MimicRoot
from mimic.test.helpers import request


class NoitAPITests(SynchronousTestCase):

    """
    Tests for noit API plugin
    """

    def test_get_all_checks(self):
        """

        """
        core = MimicCore(Clock(), [])
        root = MimicRoot(core).app.resource()
        req = request(self, root, "GET", "noit/checks")
        response = self.successResultOf(req)
        self.assertEqual(response.code, 200)
        # self.assertEqual(treq.response)

    def test_create_check(self):
        """

        """
        core = MimicCore(Clock(), [])
        root = MimicRoot(core).app.resource()
        create_check = xmltodict.unparse({"check": {
            "attributes": {
                "name": "name",
                "module": "module",
                "target": "target",
                "period": "period",
                "timeout": "timeout",
                "filterset": "filterset"
            }
        }}).encode("utf-8")
        check_id = uuid.uuid4()
        url = "noit/checks/set/{0}".format(check_id)
        print create_check
        req = request(self, root, "POST", "noit/checks/test", body=create_check,
                      headers={'content-type': ['application/xml']})
        response = self.successResultOf(req)
        self.assertEqual(response.code, 200)
