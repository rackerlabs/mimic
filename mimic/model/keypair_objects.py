"""
Keypair objects for mimic
"""

from characteristic import attributes, Attribute
@attributes(['name', 'public_key', 'user_id'])
class KeyPair(object):
    """
    A KeyPair object
    """
    static_defaults = {
        "fingerprint": "TEST",
        "private_key": """-----TEST-----\TODO: INSERT RANDOM STRING-----TEST-----\n"""
    }

    def key_json(self):
        template = self.static_defaults.copy()
        template.update({
            "name": self.name,
            "public_key": self.public_key,
            "user_id": self.user_id
        })

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
