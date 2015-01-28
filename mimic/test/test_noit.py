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
        req = request(self, root, "GET", "noit/config/checks")
        response = self.successResultOf(req)
        self.assertEqual(response.code, 200)

    def test_test_check(self):
        """

        """
        core = MimicCore(Clock(), [])
        root = MimicRoot(core).app.resource()
        test_check_payload = xmltodict.unparse({"check": {
            "attributes": {
                "name": "name",
                "module": "module",
                "target": "target",
                "period": "period",
                "timeout": "timeout",
                "filterset": "filterset"
            }
        }}).encode("utf-8")
        req = request(self, root, "POST", "noit/checks/test", body=test_check_payload,
                      headers={'content-type': ['application/xml']})
        response = self.successResultOf(req)
        self.assertEqual(response.code, 200)

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
        req = request(self, root, "PUT", url, body=create_check,
                      headers={'content-type': ['application/xml']})
        response = self.successResultOf(req)
        self.assertEqual(response.code, 200)

    def test_delete_check(self):
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
        req = request(self, root, "PUT", url, body=create_check,
                      headers={'content-type': ['application/xml']})
        response = self.successResultOf(req)
        self.assertEqual(response.code, 200)
        del_req = request(self, root, "DELETE", "noit/checks/delete/{0}".format(check_id))
        del_response = self.successResultOf(del_req)
        self.assertEqual(del_response.code, 200)


    def test_get_check(self):
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
        req = request(self, root, "PUT", url, body=create_check,
                      headers={'content-type': ['application/xml']})
        response = self.successResultOf(req)
        self.assertEqual(response.code, 200)
        get_req = request(self, root, "GET", "noit/checks/show/{0}".format(check_id))
        get_response = self.successResultOf(get_req)
        self.assertEqual(get_response.code, 200)


    def test_create_check_fails_with_500(self):
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

        req = request(self, root, "PUT", url, body=create_check.replace('</check>', ' abc'),
                      headers={'content-type': ['application/xml']})
        response = self.successResultOf(req)
        self.assertEqual(response.code, 500)

