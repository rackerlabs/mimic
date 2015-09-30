"""
Model objects for the Valkyrie mimic.
"""
from characteristic import attributes, Attribute
from json import dumps

from mimic.util.helper import random_hex_generator


class AccountContactPermission(object):
    """
    An intersection object representing a certain contact's permissions on a certain account's items
    """

    permission_type_map = {
        6: "view_domain",
        4: "view_billing",
        14: "admin_product",  # device.admin
        10: "manage_users",
        8: "manage_certificates",
        19: "edit_firewall_config",
        2: "edit_ticket",
        18: "view_firewall_config",
        15: "account_admin",  # account.admin
        7: "edit_domain",
        13: "edit_product",   # device.admin
        3: "view_community",
        17: "view_reports",
        16: "move_manager",
        12: "view_product",   # device.observer
        11: "manage_contact",
        9: "upgrade_account",
        5: "edit_billing",
        1: "view_ticket"}

    item_type_map = {
        1: "accounts",
        2: "devices"}

    def __init__(self, account_number, contact_id, permission_type, item_id, item_type_id):
        """
        Constructor
        """
        self.account_number = account_number
        self.contact_id = contact_id
        self.permission_type = permission_type
        self.permission_name = self.permission_type_map.get(self.permission_type, "unknown")
        self.item_id = item_id
        self.item_type_id = item_type_id
        self.item_type_name = self.item_type_map.get(self.item_type_id, "unknown")

    def json(self):
        """
        Create a JSON representation of self
        """
        return {
            "account_number": self.account_number,
            "contact_id": self.contact_id,
            "permission_type": self.permission_type,
            "permission_name": self.permission_name,
            "item_id": self.item_id,
            "item_type_id": self.item_type_id,
            "item_type_name": self.item_type_name
        }


@attributes([Attribute("valkyrie_store", default_factory=list)])
class ValkyrieStore(object):
    """

    Extremely barebones Valkyrie backing store with some direct, static permissions.

    No create or delete permissions endpoints are implemented.
    No logic for determining effective permissions from indirect permissions is present.

    A GET on the following URI, for example, should always return four effective permissions:

        http://localhost:8900/valkyrie/v2/account/123456/permissions/contacts/devices/by_contact/12/effective

    ...while a GET on this URI should return one:

        http://localhost:8900/valkyrie/v2/account/123456/permissions/contacts/devices/by_contact/56/effective

    """

    permissions = []
    # Arguments are: account, contact, (direct) permission, item, item_type (1=account or 2=device)
    permissions.append(AccountContactPermission(123456, 12, 12, 256, 2))
    permissions.append(AccountContactPermission(123456, 12, 12, 4096, 2))
    permissions.append(AccountContactPermission(123456, 12, 13, 16384, 2))
    permissions.append(AccountContactPermission(123456, 12, 14, 65536, 2))
    permissions.append(AccountContactPermission(123456, 34, 15, 123456, 1))
    permissions.append(AccountContactPermission(123456, 56, 12, 256, 2))

    permissions.append(AccountContactPermission(654321, 78, 14, 262144, 2))
    permissions.append(AccountContactPermission(654321, 90, 12, 1048576, 2))
    permissions.append(AccountContactPermission(654321, 90, 15, 654321, 1))

    def create_token(self, request):
        """
        Create an auth token without even interrogating the POSTed credential data
        """
        request.setResponseCode(200)
        token = {"X-Auth-Token": str(random_hex_generator(16))}
        return dumps(token)

    def get_permissions(self, request, account_number, contact_id, item_type):
        """
        Retrieve the permissions (if any) belonging to the given account,
        contact, and item type (item_type=1 -> accounts, item_type=2 -> devices
        """
        pm = [p for p in self.permissions if (p.account_number == account_number and
                                              p.contact_id == contact_id and
                                              (item_type is None or p.item_type_id == item_type))]

        response_message = {"contact_permissions": []}
        for p in pm:
            response_message['contact_permissions'].append(p.json())

        return dumps(response_message)
