from mimic.model import cloudfeeds
from twisted.trial.unittest import SynchronousTestCase


class TestCloudFeeds(SynchronousTestCase):
    def test_creation(self):
        """
        A new CloudFeeds plugin should have no products when created.
        """
        cf = cloudfeeds.CloudFeeds()
        self.assertEquals(len(cf.get_product_endpoints()), 0)

    def test_product_registration(self):
        """
        Registering a new product should create a new ATOM feed.
        """
        cf = cloudfeeds.CloudFeeds()
        cf.register_product(title='The hoohaw product.', href='hoohaw')
        self.assertEquals(len(cf.get_product_endpoints()), 1)

    def test_product_reregistration(self):
        """
        Re-registering a new product should do nothing.
        """
        cf = cloudfeeds.CloudFeeds()
        cf.register_product(title='The hoohaw product', href='hoohaw')
        cf.register_product(title='The OTHER hoohaw product', href='hoohaw')
        self.assertEquals(len(cf.get_product_endpoints()), 1)
        p = cf.get_product_by_href('hoohaw')
        self.assertEquals(p.title, 'The hoohaw product')


class TestCloudFeedsProduct(SynchronousTestCase):
    def test_creation(self):
        """
        A new product queue should be empty.
        """
        cfp = cloudfeeds.CloudFeedsProduct(title='title', href='href')
        self.assertEquals(len(cfp.events), 0)

    def test_post(self):
        """
        Posting a new event to a queue should tack said event onto the end
        of said queue.
        """
        cfp = cloudfeeds.CloudFeedsProduct(title='title', href='href')
        cfp.post("TROLOLOLOLOL!!!")
        cfp.post("This is a totally fake event-like thing.")
        self.assertEquals(
            cfp.events,
            ["TROLOLOLOLOL!!!", "This is a totally fake event-like thing."]
        )
