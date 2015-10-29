"""
Contains the base Klein app for Mimic.
"""

from __future__ import absolute_import, division, unicode_literals

from klein import Klein


class MimicApp(Klein):
    """
    Base app that extends Klein to override route.
    """
    def route(self, *args, **kwargs):
        """
        Default strict_slashes to False
        """
        kwargs['strict_slashes'] = False
        return super(MimicApp, self).route(*args, **kwargs)
