"""
Cloudfeeds customer access events
"""
from __future__ import absolute_import, division, unicode_literals

from uuid import uuid4
from six import text_type
from mimic.rest.mimicapp import MimicApp
from mimic.util.helper import json_from_request, seconds_to_timestamp

import attr

from twisted.internet.interfaces import IReactorTime
from twisted.web.template import Tag, flattenString
from twisted.python.url import URL


@attr.s(frozen=True)
class CustomerAccessEvent(object):
    """
    A customer access event
    """
    tenant_id = attr.ib()
    status = attr.ib()
    updated = attr.ib()
    id = attr.ib(default=attr.Factory(lambda: str(uuid4())))

    @classmethod
    def from_dict(cls, d, clock):
        """
        Return new CustomerAccessEvent from given dict and updated from clock
        """
        return CustomerAccessEvent(d["tenant_id"], d["status"], clock.seconds())


@attr.s
class CustomerAccessEventStore(object):
    """
    Collection of :obj:`CustomerAccessEvent`
    """
    # List of :obj:`CustomerAccessEvent`
    events = attr.ib(default=attr.Factory(list))
    # mapping from CustomerAccessEvent.id to index in events list
    events_index = attr.ib(default=attr.Factory(dict))


@attr.s
class CloudFeedsCAPRoutes(object):
    """
    This class implements routes for cloud feeds customer access policy events API
    """
    core = attr.ib()
    clock = attr.ib(validator=attr.validators.provides(IReactorTime))
    # Number of entries to return if not provided
    BATCH_LIMIT = 10

    app = MimicApp()

    def __attrs_post_init__(self):
        """
        Cache store for easy access
        """
        self.store = self.core.cloudfeeds_ca_store

    @app.route("/events", methods=["POST"])
    def add_customer_access_event(self, request):
        """
        Add customer access event. Return 201 on success. Sample request::

        {"events": [
            {"tenant_id": "23535", "status": "SUSPENDED"},
            {"tenant_id": "463423", "status": "TERMINATED"}
        ]}

        NOTE: This is control API.
        """
        content = json_from_request(request)
        events = [CustomerAccessEvent.from_dict(d, self.clock) for d in content["events"]]
        self.store.events = events + self.store.events
        for i, event in enumerate(self.store.events):
            self.store.events_index[event.id] = i
        request.setResponseCode(201)

    @app.route("/customer_access_policy/events", methods=["GET"])
    def get_customer_access_events(self, request):
        """
        Return customer access events atom feed format
        """
        marker = request.args.get(b"marker", [b""])[0].decode("ascii") or None
        direction = (request.args.get(b"direction", [b"forward"])[0]
                     .decode("ascii"))
        limit = int(request.args.get(b"limit",
                                     [text_type(self.BATCH_LIMIT)
                                      .encode("ascii")])[0].decode("ascii"))
        index = self.store.events_index.get(marker, None)
        if direction == u"forward":
            events = self.store.events[:index][:limit]
        elif direction == u"backward":
            events = self.store.events[index + 1:][:limit]
        else:
            raise ValueError("Unknown direction " + direction)
        request.setHeader(b"Content-Type", b"application/atom+xml")
        return generate_feed_xml(events)


def feed_tag():
    """
    Return new <feed> tag
    """
    feed = Tag("feed")(xmlns="http://www.w3.org/2005/Atom")
    feed(Tag("title")(type="text")("customer_access_policy/events"))
    return feed


def entry_tag():
    """
    Return new <entry>, <event> and <product> tag
    """
    entry = Tag("entry")
    for term in ["rgn:GLOBAL", "dc:GLOBAL", "customerservice.access_policy.info",
                 "type:customerservice.access_policy.info"]:
        entry(Tag("category")(term=term))
    entry(Tag("title")(type="text")("CustomerService"))
    content = Tag("content")(type="application/xml")
    entry(content)
    event = Tag("event")(xmlns="http://docs.rackspace.com/core/event", dataCenter="GLOBAL",
                         environment="PROD", region="GLOBAL", type="INFO", version="2")
    product = Tag("product")(xmlns="http://docs.rackspace.com/event/customer/access_policy",
                             previousEvent="", serviceCode="CustomerService", version="1")
    event(product)
    content(event)
    return entry, event, product


def generate_feed_xml(events):
    """
    Generate ATOM feed XML for given events

    :param list events: List of :obj:`CustomerAccessEvent`

    :return: XML text as bytes
    """
    root = URL.fromText(
        "https://mimic-host-port/cloudfeeds_cap/customer_access_events"
    )
    feed = feed_tag()
    if events:
        feed(Tag("link")(href=root
                         .add("direction", "forward")
                         .add("marker", text_type(events[0].id))
                         .asText(),
                         rel="previous"))
        feed(Tag("link")(href=root
                         .add("direction", "backward")
                         .add("marker", text_type(events[-1].id))
                         .asText(), rel="next"))
    for event in events:
        entry, event_tag, product = entry_tag()
        entry(Tag("category")(term="tid:{}".format(event.tenant_id)))
        event_tag(id=event.id, tenantId=event.tenant_id)
        product(status=event.status)
        entry(Tag("updated")(seconds_to_timestamp(event.updated)))
        entry(Tag("published")(seconds_to_timestamp(event.updated)))
        feed(entry)
    return flattenString(None, feed).result
