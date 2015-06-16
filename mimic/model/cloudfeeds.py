"""
Emulate the behavior of Rackspace Cloud Feeds service.
"""

import attr


@attr.s
class CloudFeeds(object):
    """
    Models CloudFeeds support at the plugin-level.
    """
    _endpoints = attr.ib(default=attr.Factory(list))

    def get_product_endpoints(self):
        """
        Return a list of product endpoints registered with this class.
        """
        return list(self._endpoints)
