from __future__ import absolute_import, division, unicode_literals

from uuid import uuid4
from urllib import urlencode
from mimic.rest.mimicapp import MimicApp
from mimic.util.helper import json_from_request, seconds_to_timestamp

import attr

from twisted.internet.interfaces import IReactorTime
from twisted.web.template import Tag, flattenString


@attr.s(frozen=True)
class CustomerAccessEvent(object):
    """
    A customer access event
    """
    tenant_id = attr.ib()
    status = attr.ib()
    updated = attr.ib()
    id = attr.ib(default=attr.Factory(lambda: str(uuid4)))

    @classmethod
    def from_dict(cls, d, clock):
        return CustomerAccessEvent(d["tenant_id"], d["status"],
                                   seconds_to_timestamp(clock.seconds()))


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
    This class implements routes for cloud feeds customer access events API
    """
    core = attr.ib()
    clock = attr.ib(validator=attr.validators.provides(IReactorTime))
    # Number of entries to return if not provided
    BATCH_LIMIT = 25

    app = MimicApp()

    def __attrs_post_init__(self):
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
        marker = request.args.get(u"marker", [None])[0]
        direction = request.args.get(u"direction", [u"forward"])[0]
        limit = request.args.get(u"limit", [self.BATCH_LIMIT])[0]
        index = self.store.events_index.get(marker, 0)
        if direction == u"forward":
            events = self.store.events[:index][:limit]
        elif direction == u"backward":
            events = self.store.events[index:][:limit]
        else:
            raise ValueError("Unknown direction " + direction)
        request.setHeader(b"Content-Type", [b"application/atom+xml"])
        return generate_feed_xml(events)


def feed_tag():
    feed = Tag("feed")(xmlns="http://www.w3.org/2005/Atom")
    feed(Tag("title")(type="text")("customer_access_policy/events"))
    return feed

#"""
#<feed xmlns="http://www.w3.org/2005/Atom">
#  <title type="text">customer_access_policy/events</title>
#  <link href="{previous}" rel="previous"/>
#  <link href="{next}" rel="next"/>
#  {entries}
#</feed>
#"""

def entry_tag():
    entry = Tag("entry")
    for term in ["rgn:GLOBAL", "dc:GLOBAL", "customerservice.access_policy.info",
                 "type:customerservice.access_policy.info"]:
        entry(Tag("category")(term=term))
    entry(Tag("title")(type="text")("CustomerService"))
    entry(Tag("content")(type="application/xml"))
    event = Tag("event")(xmlns="http://docs.rackspace.com/core/event", dataCenter="GLOBAL",
                         environment="PROD", region="GLOBAL", type="INFO", version="2")
    product = Tag("product")(xmlns="http://docs.rackspace.com/event/customer/access_policy",
                             previousEvent="", serviceCode="CustomerService", version="1")
    event(product)
    entry(event)
    return entry, event, product

#u"""
#<entry>
#  <atom:category xmlns:atom="http://www.w3.org/2005/Atom" term="tid:{tenant_id}"/>
#  <atom:category xmlns:atom="http://www.w3.org/2005/Atom" term="rgn:GLOBAL"/>
#  <atom:category xmlns:atom="http://www.w3.org/2005/Atom" term="dc:GLOBAL"/>
#  <atom:category xmlns:atom="http://www.w3.org/2005/Atom" term="customerservice.access_policy.info"/>
#  <atom:category xmlns:atom="http://www.w3.org/2005/Atom" term="type:customerservice.access_policy.info"/>
#  <title type="text">CustomerService</title>
#  <content type="application/xml">
#    <event xmlns="http://docs.rackspace.com/core/event" xmlns:ns2="http://docs.rackspace.com/event/customer/access_policy" dataCenter="GLOBAL" environment="PROD" id="{id}" region="GLOBAL" tenantId="{tenant_id}" type="INFO" version="2">
#      <ns2:product previousEvent="" serviceCode="CustomerService" status="{status}" version="1"/>
#    </event>
#  </content>
#  <updated>{updated}</updated>
#  <published>{updated}</published>
#</entry>
#"""


def generate_feed_xml(events):
    """
    Generate ATOM feed XML for given events

    :param list events: List of :obj:`CustomerAccessEvent`

    :return: XML text as bytes
    """
    root = u"https://mimic-host-port"
    feed = feed_tag()
    if events:
        prev = "{}?{}".format(root, urlencode({u"marker": events[0].id, u"direction": u"forward"}))
        next = "{}?{}".format(root, urlencode({u"marker": events[-1].id, u"direction": u"backward"}))
        feed(Tag("link")(href=prev, rel="previous"))
        feed(Tag("link")(href=next, rel="next"))
    for event in events:
        entry, event_tag, product = entry_tag()
        entry(Tag("category")(term="tid:{}".format(event.tenant_id)))
        event_tag(tenant_id=event.tenant_id)
        product(status=event.status)
        entry(Tag("updated")(event.updated))
        entry(Tag("published")(event.updated))
        feed(entry)
    return flattenString(None, feed).result
