"""
Customet Contacts storage object
"""
import time
from characteristic import attributes, Attribute


@attributes(["tenant_id", "email_address", "role",
             Attribute("firstName", default_value="Test FirstName"),
             Attribute("lastName", default_value="Test LastName")])
class Contact(object):
    """
    A :obj:`Contact` is a representation for each contact for a tenant.
    """

    static_defaults = {
        "firstName": "Pat",
        "lastName": "Example",
        # "customerAccountNumber": req.params.tenantId,
        "customerAccountType": "CLOUD",
        "contactNumber": "RPN-994-758-811",
        "rcn": "RCN-348-367-072",
        "emailAddresses": {
                    "emailAddress": [
                        {
                            "primary": True,
                            "address": None
                        }
                    ]
        },
        "phoneNumbers": {
            "phoneNumber": [
                        {
                            "number": "55555555555"
                        }
            ]
        },
        "roles": {
            "role": []
        },
        "link": [
            {
                "rel": "via",
                "href": "http://link-to-nothing-for-contact-in-customer-api"
            }
        ]
    }

    def generate_contacts(self, tenant_id):
        """

        """
        pass


@attributes([Attribute("contacts_store", default_factory=dict)])
class ContactsStore(object):
    """
    A collection of contact objects for a tenant.
    """

    def add_to_contacts_store(self, tenant_id, contact_list):
        """
        Create a new Contact object for each contact in `contact_list`
        and append it to :obj: `ContactsStore` of the tenant
        """
        self.contacts_store[tenant_id] = [
            Contact(each_contact) for each_contact in contact_list]
        return

    def list_contacts_for_tenant(self, tenant_id):
        """
        Returns the list of contacts for a tenent
        """
        if tenant_id in self.contacts_store:
            return {
                "link": [
                    {
                        "rel": "next",
                        "href": "http://link-to-nothing-in-the-customer-api"
                    }
                ],
                "contact": Contact.generate_contacts(tenant_id)
            }
