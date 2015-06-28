from twisted.trial.unittest import SynchronousTestCase
from twisted.internet.task import Clock

from mimic.core import MimicCore
from mimic.resource import MimicRoot
from mimic.test.helpers import json_request, request


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

    def test_get_default_contacts_for_tenant_successfully(self):
        """
        The ``GET \contacts`` call returns a list of default contacts
        for a tenant with the response code 200.
        """
        self.get_contacts(self.root, "111111")
