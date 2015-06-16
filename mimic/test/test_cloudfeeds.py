from mimic.model import cloudfeeds
from twisted.trial.unittest import SynchronousTestCase


class TestCloudFeeds(SynchronousTestCase):
    def test_creation(self):
        """
        A new CloudFeeds plugin should have no products when created.
        """
        cf = cloudfeeds.CloudFeeds()
        self.assertEquals(len(cf.get_product_endpoints()), 0)
