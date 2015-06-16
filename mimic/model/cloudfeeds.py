"""
Emulate the behavior of Rackspace Cloud Feeds service.
"""

import attr


@attr.s
class CloudFeedsProduct(object):
    """
    Models a single CloudFeed product endpoint and its respective
    functionality.
    """
    title = attr.ib(attr.validators.instance_of(str))
    href = attr.ib(attr.validators.instance_of(str))


@attr.s
class CloudFeeds(object):
    """
    Models CloudFeeds support at the plugin-level.
    """
    _endpoints = attr.ib(default=attr.Factory(dict))

    def get_product_endpoints(self):
        """
        Return a list of product endpoints registered with this class.
        """
        return list(self._endpoints)

    def register_product(self, title, href):
        """
        Register a product by creating a URL that one can GET and/or POST from/to,
        and providing a descriptive title for it in the product endpoint
        listing.

        :param str title: This provides the human-readable description of the
            product to the user when they GET the list of endpoints.
        :param str href: This provides the unique component of an HTTP reference
            URL that a client can use to talk to this specific feed.
        """
        if not self.get_product_by_href(href):
            self._endpoints[href] = CloudFeedsProduct(title=title, href=href)

    def get_product_by_href(self, href):
        """
        If it exists, returns the product endpoint for the given href.
        If no such endpoint exists, return None.
        """
        return self._endpoints.get(href, None)
