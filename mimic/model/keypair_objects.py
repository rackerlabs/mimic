"""
Keypair objects for mimic
"""
from mimic.session import SessionStore

from characteristic import attributes, Attribute
from json import loads, dumps
from urllib import urlencode


from characteristic import attributes, Attribute
@attributes(['name', 'public_key'])
class KeyPair(object):
    """
    A KeyPair object
    """
    fingerprint = "TEST::TEST::TEST::TEST:TEST"

    def key_json(self):
        return {
            "keypair": {
                "name": self.name,
                "public_key": self.public_key,
                "fingerprint": self.fingerprint
                }
            }

@attributes(
    ["tenant_id", "region_name", "clock",
     Attribute("keypairs", default_factory=list)]
)
class RegionalKeyPairCollection(object):

    def create_keypair(self, keypair):
        self.keypairs.append(keypair)
        return self.keypair_by_name(keypair.name).key_json()

    def keypair_by_name(self, name):
        for keypair in self.keypairs:
            if keypair.name == name:
                return keypair

    def json_list(self):
        keypairs_json = {}
        for keypair in self.keypairs:
            keypairs_json.update(keypair.key_json())

        result = {
            "keypairs": [
                keypairs_json
            ]
        }
        return dumps(result)

    def remove_keypair(self, name):
        kp_to_remove = self.keypair_by_name(name)
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
