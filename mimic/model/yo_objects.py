"""
Yo API data model
"""

from __future__ import absolute_import, division, unicode_literals

import attr

from attr.validators import instance_of
from six import text_type

from mimic.util.helper import random_hex_generator


@attr.s
class User(object):
    """
    Models a Yo user.
    """
    display_name = attr.ib(validator=instance_of(text_type))
    username = attr.ib(validator=instance_of(text_type))
    is_api_user = attr.ib(validator=instance_of(bool), default=False)
    is_subscribable = attr.ib(validator=instance_of(bool), default=False)
    type = attr.ib(validator=instance_of(text_type), default='user')
    user_id = attr.ib(validator=instance_of(text_type),
                      default=attr.Factory(lambda: random_hex_generator(12)))
    yo_count = attr.ib(validator=instance_of(int), default=0)

    def to_json(self):
        """
        Serializes this Yo user to a JSON-encodable dict.
        """
        return attr.asdict(self)


@attr.s
class YoCollections(object):
    """
    Models the global collection of Yo business objects.
    """
    users = attr.ib(validator=instance_of(dict), default=attr.Factory(dict))

    def get_or_create_user(self, username):
        """
        Gets the user from the collection, or creates it if it does not exist.
        """
        try:
            return self.users[username.upper()]
        except KeyError:
            self.users[username.upper()] = User(display_name=username, username=username.upper())
            return self.users[username.upper()]
