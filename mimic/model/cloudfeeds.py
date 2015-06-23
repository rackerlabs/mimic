"""
Emulate the behavior of Rackspace Cloud Feeds service.
Please refer to
http://docs.rackspace.com/cloud-feeds/api/v1.0/feeds-devguide/content/overview.html
for more details.
"""

import attr
from six import string_types


@attr.s
class CloudFeedsProduct(object):
    """
    Models a single CloudFeed product endpoint and its respective
    functionality.
    """
    title = attr.ib(validator=attr.validators.instance_of(string_types))
    href = attr.ib(validator=attr.validators.instance_of(string_types))

    events = attr.ib(default=attr.Factory(list))

    def post(self, event):
        """
        Post an event to the product queue.
        """
        self.events.append(event)


@attr.s
class CloudFeeds(object):
    """
    Models CloudFeeds support at the plugin-level.
    """
    tenant_id = attr.ib(validator=attr.validators.instance_of(string_types))
    clock = attr.ib()
    _endpoints = attr.ib(default=attr.Factory(dict))

    def get_product_endpoints(self):
        """
        Return a dictionary of product endpoints registered with this class.
        """
        return dict(self._endpoints)

    def register_product(self, title, href):
        """
        If the product, identified by href, doesn't already exist in the
        registry, then register a product by creating a URL that one can GET
        and/or POST from/to, and providing a descriptive title for it in the
        product endpoint listing.

        If the product already appears in the registry, take no action.

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


def render_product_dict(the_product):
    """
    Return Python dictionary suitable for JSON encoding in requests and
    responses to/from cloudfeeds.  This dictionary contains a single product
    endpoint descriptor.
    """
    return {
        "title": the_product.title,
        "collection": {
            "title": the_product.title,
            "href": the_product.href,
        }
    }


def render_product_endpoints_dict(the_products):
    """
    Return Python dictionary suitable for JSON encoding in requests and
    responses to/from cloudfeeds.  This dictionary contains the complete set
    of product endpoints.
    """
    return {
        "service": {
            "workspace": [
                render_product_dict(the_products[p]) for p in the_products
            ],
        },
    }
