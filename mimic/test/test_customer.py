import json

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
        Initialize core and root.

        `default_contacts` is the default contact set for any tenant,
        when the contacts are not set using ``POST /contacts``.
        """
        self.core = MimicCore(Clock(), [])
        self.root = MimicRoot(self.core).app.resource()
        self.default_contacts = [{"email": "example@example.com", "role": "TECHNICAL"},
                                 {"email": "example2@example.com", "role": "TECHNICAL"}]

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

    def validate_contact_list(self, response, expected_contacts):
        """
        Validate that contacts in the `response` is same as the
        `expected_contacts`
        """
        self.assertEqual(len(response["contact"]), len(expected_contacts))
        contact_emails = [each_contact["emailAddresses"]["emailAddress"][0]["address"]
                          for each_contact in response["contact"]]
        self.assertTrue(expected_contacts[0]["email"] in contact_emails)
        self.assertTrue(expected_contacts[1]["email"] in contact_emails)
        contact_roles = [each_contact["roles"]["role"][0]
                         for each_contact in response["contact"]]
        self.assertTrue(expected_contacts[0]["role"] in contact_roles)
        self.assertTrue(expected_contacts[1]["role"] in contact_roles)

    def test_get_default_contacts_for_a_tenant_successfully(self):
        """
        The ``GET /contacts`` call returns a list of default contacts
        for a tenant with the response code 200.
        """
        response = self.get_contacts(self.root, "111111")
        self.validate_contact_list(response, self.default_contacts)

    def test_get_default_contacts_for_multiple_tenants_successfully(self):
        """
        The ``GET /contacts`` call returns a list of default contacts
        for multiple tenants with the response code 200.
        """
        for each_tenant in ['111111', '22222', '33333', '444444']:
            response = self.get_contacts(self.root, each_tenant)
            self.validate_contact_list(response, self.default_contacts)

    def test_set_contacts_for_a_tenant_successfully(self):
        """
        The ``POST /contacts`` call adds contacts to a tenant, which is then
        listed by the ``GET /contacts`` calls
        """
        expected_contacts = [{"email": "test@email.com", "role": "PRIMARY"},
                             {"email": "new@email.com", "role": "TECHNICAL"}]
        response = self.successResultOf(request(
            self, self.root, "POST",
            "/v1/customer_accounts/CLOUD/555555/contacts",
            json.dumps(expected_contacts)))
        self.assertEqual(200, response.code)
        response = self.get_contacts(self.root, "555555")
        self.validate_contact_list(response, expected_contacts)

    def test_change_contacts_from_default_contacts(self):
        """
        The ``GET /contacts`` call returns a list of default contacts then
        change the contacts using ``POST /contacts``
        """
        response = self.get_contacts(self.root, "111111")
        self.validate_contact_list(response, self.default_contacts)
        expected_contacts = [{"email": "test1@email.com", "role": "PRIMARY"},
                             {"email": "new1@email.com", "role": "TECHNICAL"}]
        response = self.successResultOf(request(
            self, self.root, "POST",
            "/v1/customer_accounts/CLOUD/555555/contacts",
            json.dumps(expected_contacts)))
        self.assertEqual(200, response.code)
        response = self.get_contacts(self.root, "555555")
        self.validate_contact_list(response, expected_contacts)

    def test_set_contacts_to_be_null(self):
        """
        The ``POST /contacts`` call adds empty contacts to a tenant, which
        is then listed by the ``GET /contacts`` calls
        """
        expected_contacts = []
        response = self.successResultOf(request(
            self, self.root, "POST",
            "/v1/customer_accounts/CLOUD/77777/contacts",
            json.dumps(expected_contacts)))
        self.assertEqual(200, response.code)
        response = self.get_contacts(self.root, "77777")
        self.assertEqual(len(response["contact"]), 0)
