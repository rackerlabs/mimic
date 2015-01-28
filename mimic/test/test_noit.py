import uuid
import xmltodict

from twisted.trial.unittest import SynchronousTestCase
from twisted.internet.task import Clock

from mimic.core import MimicCore
from mimic.resource import MimicRoot
from mimic.test.helpers import request


class NoitAPITests(SynchronousTestCase):

    """
    Tests for noit API plugin
    """

    def setUp(self):
        """
        Create a check
        """
        core = MimicCore(Clock(), [])
        self.root = MimicRoot(core).app.resource()
        self.create_check = {
            "check": {
                "attributes": {
                    "name": "name",
                    "module": "module",
                    "target": "target",
                    "period": "period",
                    "timeout": "timeout",
                    "filterset": "filterset"
                }
            }}
        self.create_check_xml_payload = xmltodict.unparse(self.create_check
                                                          ).encode("utf-8")
        self.check_id = uuid.uuid4()
        url = "noit/checks/set/{0}".format(self.check_id)

        req = request(self, self.root, "PUT", url,
                      body=self.create_check_xml_payload,
                      headers={'content-type': ['application/xml']})
        self.response = self.successResultOf(req)

    def test_get_all_checks(self):
        """
        Test to verify :func:`get_all_checks` on ``GET /config/checks``
        """
        req = request(self, self.root, "GET", "noit/config/checks")
        response = self.successResultOf(req)
        self.assertEqual(response.code, 200)

    def test_test_check(self):
        """
        Test to verify :func:`test_check` on ``POST /checks/test``
        """
        req = request(self, self.root, "POST", "noit/checks/test",
                      body=self.create_check_xml_payload,
                      headers={'content-type': ['application/xml']})
        response = self.successResultOf(req)
        self.assertEqual(response.code, 200)

    def test_create_check(self):
        """
        Test to verify :func:`set_check` on ``PUT /checks/set/<check_id>``
        """
        self.assertEqual(self.response.code, 200)

    def test_update_check(self):
        """
        Test to verify update check on :func:`set_check` using
        ``PUT /checks/set/<check_id>``
        """
        self.create_check["check"]["attributes"]["names"] = "rename"
        req = request(self, self.root, "PUT",
                      "noit/checks/set/{0}".format(self.check_id),
                      body=xmltodict.unparse(self.create_check
                                             ).encode("utf-8"),
                      headers={'content-type': ['application/xml']})
        self.response = self.successResultOf(req)
        self.assertEqual(self.response.code, 200)

    def test_get_check(self):
        """
        Test to verify :func:`get_checks` on ``GET /checks/show/<check_id>``
        """
        get_req = request(self, self.root, "GET",
                          "noit/checks/show/{0}".format(self.check_id))
        get_response = self.successResultOf(get_req)
        self.assertEqual(get_response.code, 200)

    def test_delete_check(self):
        """
        Test to verify :func:`delete_checks` on
        ``DELETE /checks/delete/<check_id>``
        """
        del_req = request(self, self.root, "DELETE",
                          "noit/checks/delete/{0}".format(self.check_id))
        del_response = self.successResultOf(del_req)
        self.assertEqual(del_response.code, 200)

    def test_create_check_fails_with_500(self):
        """
        Test to verify :func:`set_check` results in error 500,
        when the xml cannot be parsed.
        """
        req = request(self, self.root, "PUT",
                      "noit/checks/set/{0}".format(self.check_id),
                      body=self.create_check_xml_payload.replace(
                          '</check>', ' abc'),
                      headers={'content-type': ['application/xml']})
        response = self.successResultOf(req)
        self.assertEqual(response.code, 500)

    def test_create_check_fails_with_500_for_invalid_check_id(self):
        """
        Test to verify :func:`set_check` results in error 500,
        when the xml cannot be parsed.
        """
        req = request(self, self.root, "PUT",
                      "noit/checks/set/123444",
                      body=self.create_check_xml_payload,
                      headers={'content-type': ['application/xml']})
        response = self.successResultOf(req)
        self.assertEqual(response.code, 500)
