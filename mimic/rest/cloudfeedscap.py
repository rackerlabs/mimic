from __future__ import absolute_import, division, unicode_literals

from uuid import uuid4
from six import text_type
from zope.interface import implementer
from twisted.plugin import IPlugin
from mimic.catalog import Endpoint, Entry
from mimic.imimic import IAPIMock
from mimic.rest.mimicapp import MimicApp
from mimic.core import MimicCore

import attr

from toolz.functoolz import compose


@attr.s(frozen=True)
class CustomerAccessEvent(object):
    """
    A customer access event
    """
    tenant_id = attr.ib()
    status = attr.ib()
    updated = attr.ib()
    id = attr.ib(default=attr.Factory(compose(str, uuid4)))


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
    core = attr.ib(validator=aiof(MimicCore))
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
        events = list(map(CustomerAccessEvent.from_json, content["events"]))
        for i, event in enumerate(events):
            self.store.events_index[event.id] = i
        self.store.events = events + self.store.events
        request.setResponseCode(201)

    @app.route("/customer_access_policy/events", methods=["GET"])
    def get_customer_access_events(self, request):
        marker = request.args.get("marker", [None])[0]
        direction = request.args.get("direction", ["forward"])[0]
        limit = request.args.get("limit", [BATCH_LIMIT])[0]
        index = self.store.events_index.get(marker, 0)
        if direction == "forward":
            events = self.store.events[:index][:limit]
        elif direction == "backward":
            events = self.store.events[index:][:limit]
        else:
            raise ValueError("Unknown direction " + direction)
        request.setHeader(b"Content-Type", [b"application/atom+xml"])
        return generate_cap_feed(events)


feed_fmt = """
<feed xmlns="http://www.w3.org/2005/Atom">
  <title type="text">customer_access_policy/events</title>
  <link href="{previous}" rel="previous"/>
  <link href="{next}" rel="next"/>
  {entries}
</feed>
"""

entry_fmt = """
<entry>
  <atom:category xmlns:atom="http://www.w3.org/2005/Atom" term="tid:{tenant_id}"/>
  <atom:category xmlns:atom="http://www.w3.org/2005/Atom" term="rgn:GLOBAL"/>
  <atom:category xmlns:atom="http://www.w3.org/2005/Atom" term="dc:GLOBAL"/>
  <atom:category xmlns:atom="http://www.w3.org/2005/Atom" term="customerservice.access_policy.info"/>
  <atom:category xmlns:atom="http://www.w3.org/2005/Atom" term="type:customerservice.access_policy.info"/>
  <title type="text">CustomerService</title>
  <content type="application/xml">
    <event xmlns="http://docs.rackspace.com/core/event" xmlns:ns2="http://docs.rackspace.com/event/customer/access_policy" dataCenter="GLOBAL" environment="PROD" id="{id}" region="GLOBAL" tenantId="{tenant_id}" type="INFO" version="2">
      <ns2:product previousEvent="" serviceCode="CustomerService" status="{status}" version="1"/>
    </event>
  </content>
  <updated>{updated}</updated>
  <published>{updated}</published>
</entry>
"""


def generate_feed(events):
    """
    Generate ATOM feed XML for given events

    :param list events: List of :obj:`CustomerAccessEvent`

    :return: XML text as bytes
    """
    root = "https://mimic-host-port"
    prev = "{}?{}".format(root, urlencode({"marker": events[0].id, "direction": "forward"}))
    next = "{}?{}".format(root, urlencode({"marker": events[-1].id, "direction": "backward"}))
    entries = ''.join(entry_fmt.format(**event.asdict()) for event in events)
    return feed_fmt.format(previous=prev, next=next, entries=entries).encode("utf-8")
