"""
Mailgun object storage
"""
import time
from characteristic import attributes, Attribute


@attributes(["message_id", "to", "msg_from", "subject", "body",
             Attribute("custom_headers", default_factory=dict)])
class Message(object):
    """
    A :obj:`Message` is a representation of an email in Mailgun.
    It can produce JSON-serializable objects for various pieces of
    state that are required for API responses.
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
        Long-form JSON-serializable object representation of this message, as
        returned by a GET on this individual message.
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

    def add_to_message_store(self, **attributes):
        """
        Create a new Message object and add it to the
        :obj: `message_store`
        """
        msg = Message(**attributes)
        self.message_store.append(msg)
        return

    def list_messages(self, filter_by=None):
        """
        List all the messages.

        :param str filter_by: supports filtering the List by
        `to` addresses only currently.
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

    def filter_message_by_to_address(self, to_address):
        """
        Retrieve a :obj:`Message` object by its `to` address.
        """
        for each_msg in self.message_store:
            if each_msg.to == to_address[0]:
                return each_msg
