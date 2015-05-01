"""
Models relating to identity.
"""
from attr import attributes, attr


@attributes
class IdentitySession(object):
    """
    An identity session for a tenant.
    """
    @classmethod
    def from_store(cls, session_store, tenant_id):
        """
        Get the identity session for the given tenant.
        """
        return (session_store
                .session_for_tenant_id(tenant_id)
                .data_for_api(cls, cls))

    identity_admin = attr(default=False)
