"""
Keypair objects for mimic
"""

import json

from characteristic import attributes, Attribute


@attributes(['name', 'public_key'])
class KeyPair(object):
    """
    A KeyPair object
    """
    fingerprint = "aa:aa:aa:aa:aa:aa:aa:aa:aa:aa:aa:aa:aa:aa:aa:aa"
    user_id = "fake"

    def key_json(self):
        """
        Serialize a :obj:`Keypair` into JSON
        """
        return {
            "keypair": {
                "name": self.name,
                "public_key": self.public_key,
                "fingerprint": self.fingerprint,
                "user_id": self.user_id
            }
        }


@attributes(
    ["tenant_id", "region_name", "clock",
     Attribute("keypairs", default_factory=list)]
)
class RegionalKeyPairCollection(object):
    """
    A :obj:`ReionalKeyPairCollection` is a collection of
    :obj:`KeyPair` objects owned by a given tenant for a region.
    """

    def create_keypair(self, keypair):
        """
        Add a :obj:`KeyPair` to the list of keypairs
        """
        self.keypairs.append(keypair)
        return self.keypair_by_name(keypair.name).key_json()

    def keypair_by_name(self, name):
        """
        Return a :obj:`KeyPair` by name from the current keypairs list
        """
        for keypair in self.keypairs:
            if keypair.name == name:
                return keypair

    def json_list(self):
        """
        JSON List of all :obj:`KeyPair` for a region
        """
        result = {"keypairs": []}
        if len(self.keypairs) > 0:
            keypairs_json = {}
            for keypair in self.keypairs:
                keypairs_json.update(keypair.key_json())
            result = {
                "keypairs": [
                    keypairs_json
                ]
            }

        return json.dumps(result)

    def remove_keypair(self, name):
        """
        Remove a :obj:`KeyPair` from the list of keypairs
        """
        kp_to_remove = self.keypair_by_name(name)
        if kp_to_remove is None:
            raise ValueError("Keypair Not Found")

        self.keypairs.remove(kp_to_remove)


@attributes(["tenant_id", "clock",
             Attribute("regional_collections", default_factory=dict)])
class GlobalKeyPairCollections(object):
    """
    A :obj:`GlobalKeyPairCollections` is a set of all the
    :obj:`RegionalKeyPairCollection` objects owned by a given tenant.  In other
    words, all the objects that a single tenant owns globally.
    """

    def collection_for_region(self, region_name):
        """
        Get a :obj:`RegionalServerCollection` for the region identified by the
        given name.
        """
        if region_name not in self.regional_collections:
            self.regional_collections[region_name] = (
                RegionalKeyPairCollection(tenant_id=self.tenant_id,
                                          region_name=region_name,
                                          clock=self.clock)
            )
        return self.regional_collections[region_name]
