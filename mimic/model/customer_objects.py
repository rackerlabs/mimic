"""
Customet Contacts storage object
"""
from characteristic import attributes, Attribute


@attributes(["tenant_id", "email_address", "role",
             Attribute("first_name", default_value="Test FirstName"),
             Attribute("last_name", default_value="Test LastName")])
class Contact(object):
    """
    A :obj:`Contact` is a representation for each contact for a tenant.
    """

    static_defaults = {
        "firstName": "Pat",
        "lastName": "Example",
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

    def generate_contacts(self):
        """
        Long-form JSON-serializable object representation of this contact, as
        returned by a GET.
        """
        template = self.static_defaults.copy()
        template.update({
            "firstName": self.first_name,
            "lastName": self.last_name,
            "customerAccountNumber": self.tenant_id,
            "roles": {
                "role": [self.role]
            },
            "emailAddresses": {
                "emailAddress": [
                    {
                        "primary": True,
                        "address": self.email_address
                    }
                ]
            }
        })
        return template


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
            Contact(tenant_id=each_contact[0], email_address=each_contact[1],
                    role=each_contact[2]) for each_contact in contact_list]
        return

    def list_contacts_for_tenant(self, tenant_id):
        """
        Returns the list of contacts for a tenent
        """
        if tenant_id not in self.contacts_store:
            default_contact_list = [(tenant_id, 'example@example.com', 'TEST'),
                                    (tenant_id, 'example2@example.com', 'TECHNICAL')]
            self.add_to_contacts_store(tenant_id, default_contact_list)

        contacts = [each.generate_contacts()
                    for each in self.contacts_store[tenant_id]]

        return {
            "link": [
                {
                    "rel": "next",
                    "href": "http://link-to-nothing-in-the-customer-api"
                }
            ],
            "contact": contacts
        }
