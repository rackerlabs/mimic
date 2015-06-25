from twisted.trial.unittest import SynchronousTestCase
from twisted.internet.task import Clock

from mimic.core import MimicCore
from mimic.resource import MimicRoot
from mimic.test.helpers import json_request


class CustomerAPITests(SynchronousTestCase):

    """
    Tests for the Customer API
    """

    def setUp(self):
        """
        Initialize core and root
        """
        self.core = MimicCore(Clock(), [])
        self.root = MimicRoot(self.core).app.resource()

    def get_contacts(self, root, tenant):
        """
        Get contacts and verify that the responce code was 200.
        Returns the contacts list
        """
        (response, content) = self.successResultOf(json_request(
            self, root, "GET",
            "/v1/customer_accounts/CLOUD/{0}/contacts".format(tenant)))
        self.assertEqual(200, response.code)
        return content

    def test_get_default_contacts_for_a_tenant_successfully(self):
        """
        The ``GET \contacts`` call returns a list of default contacts
        for a tenant with the response code 200.
        """
        response = self.get_contacts(self.root, "111111")
        self.assertEqual(len(response["contact"]), 2)
        default_emails = [each_contact["emailAddresses"]["emailAddress"][0]["address"]
                          for each_contact in response["contact"]]
        self.assertTrue("example@example.com" in default_emails)
        self.assertTrue("example2@example.com" in default_emails)

    def test_get_default_contacts_for_multiple_tenants_successfully(self):
        """
        The ``GET \contacts`` call returns a list of default contacts
        for multiple tenants with the response code 200.
        """
        for each_tenant in ['22222', '33333', '444444']:
            response = self.get_contacts(self.root, each_tenant)
            self.assertEqual(len(response["contact"]), 2)
            default_emails = [each_contact["emailAddresses"]["emailAddress"][0]["address"]
                              for each_contact in response["contact"]]
            self.assertTrue("example@example.com" in default_emails)
            self.assertTrue("example2@example.com" in default_emails)
