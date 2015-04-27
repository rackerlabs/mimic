"""
Tests for the identity admin API.
"""

from twisted.plugin import IPlugin
from twisted.trial.unittest import SynchronousTestCase

from zope.interface.verify import verifyObject

from mimic.imimic import IAPIMock
from mimic.rest.identity_admin_api import IdentityAdminAPI


class IdentityAdminAPITests(SynchronousTestCase):
    """
    Tests for the identity admin API mock.
    """
    def setUp(self):
        """
        Create a identity API mock instance for testing.
        """
        self.mock = IdentityAdminAPI()

    def test_interface(self):
        """
        The identity admin implements the IPlugin and IAPIMock interfaces
        faithfully.
        """
        verifyObject(IAPIMock, self.mock)
        verifyObject(IPlugin, self.mock)
