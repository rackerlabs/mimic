"""
Mailgun object storage
"""
import time
from characteristic import attributes, Attribute


@attributes(["message_id", "to", "msg_from", "subject", "body",
             Attribute("headers", default_factory=dict)])
class Messages(object):
    """
    A message object representing an email in mailgun.
    """

    static_defaults = {
        "tags": [],
        "delivery-status": {
            "message": "",
            "code": 0,
            "description": None,
            "session-seconds": 1.114408016204834
        },
        "envelope": {
            "transport": "smtp",
            "sending-ip": "127.0.0.1",
        },
        "recipient-domain": "mailgun.com",
        "id": "mimic-LCZuENBlS0iWjs-yBpNJaQ",
        "campaigns": [],
        "user-variables": {},
        "flags": {
            "is-routed": None,
            "is-authenticated": True,
            "is-system-test": False,
            "is-test-mode": False
        },
        "log-level": "info",
        "timestamp": time.time(),
        "message": {
            "headers": {},
            "attachments": [],
            "recipients": [],
            "size": 0
        },
        "recipient": None,
        "event": "delivered"
    }

    def generate_events(self):
        """
        Create an event for each message created.
        """
        template = self.static_defaults.copy()
        template.update({
            "envelope": {
                "sender": self.msg_from,
                "targets": self.to
            },
            "message": {
                "headers": {
                    "to": self.to,
                    "message-id": self.message_id,
                    "from": self.msg_from,
                    "subject": self.subject
                },
                "recipients": [self.to],
                "recipient": self.to
            }
        })
        return template


@attributes([Attribute("message_store", default_factory=list)])
class MessageStore(object):
    """
    A collection of message objects.
    """

    def _add_to_message_store(self, **attributes):
        """
        Add messages to the message storage
        """
        msg = Messages(**attributes)
        self.message_store.append(msg)
        return

    def _list_messages(self, filter_by=None):
        """
        List events pertaining to the messages
        """
        to_be_listed = self.message_store
        if filter_by:
            events = [msg.generate_events()
                      for msg in to_be_listed if msg.to in filter_by]
        else:
            events = [msg.generate_events() for msg in to_be_listed]
        return {
            "items": events,
            "paging": {
                "next": "http://i-am-a-fake-link-to-nothing",
                "last": "http://i-am-a-fake-link-to-nothing",
                "first": "http://i-am-a-fake-link-to-nothing=",
                "previous": "http://i-am-a-fake-link-to-nothing=="
            }}

    def message_by_to_address(self, to_address):
        """
        Retrieve a :obj:`Message` object by its `to` address.
        """
        for each_msg in self.message_store:
            if each_msg.to == to_address[0]:
                return each_msg
