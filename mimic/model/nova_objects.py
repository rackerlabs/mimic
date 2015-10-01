"""
Model objects for the Nova mimic.
"""

import re

from characteristic import attributes, Attribute
from random import randrange
from json import loads, dumps
from urllib import urlencode

from six import string_types

from mimic.util.helper import (
    seconds_to_timestamp,
    random_string,
    timestamp_to_seconds
)

from mimic.model.behaviors import (
    BehaviorRegistryCollection, EventDescription, Criterion, regexp_predicate
)
from twisted.web.http import ACCEPTED, BAD_REQUEST, FORBIDDEN, NOT_FOUND, CONFLICT


@attributes(['nova_message'])
class LimitError(Exception):
    """
    Error to be raised when a limit has been exceeded.
    """


@attributes(['nova_message'])
class BadRequestError(Exception):
    """
    Error to be raised when bad input has been received to Nova.
    """


def _nova_error_message(msg_type, message, status_code, request):
    """
    Set the response code on the request, and return a JSON blob representing
    a Nova error body, in the format Nova returns error messages.

    :param str msg_type: What type of error this is - something like
        "badRequest" or "itemNotFound" for Nova.
    :param str message: The message to include in the body.
    :param int status_code: The status code to set
    :param request: the request to set the status code on

    :return: dictionary representing the error body
    """
    request.setResponseCode(status_code)
    return {
        msg_type: {
            "message": message,
            "code": status_code
        }
    }


def bad_request(message, request):
    """
    Return a 400 error body associated with a Nova bad request error.
    Also sets the response code on the request.

    :param str message: The message to include in the bad request body.
    :param request: The request on which to set the response code.

    :return: dictionary representing the error body.
    """
    return _nova_error_message("badRequest", message, BAD_REQUEST, request)


def not_found(message, request):
    """
    Return a 404 error body associated with a Nova not found error.
    Also sets the response code on the request.

    :param str message: The message to include in the bad request body.
    :param request: The request on which to set the response code.

    :return: dictionary representing the error body.
    """
    return _nova_error_message("itemNotFound", message, NOT_FOUND, request)


def forbidden(message, request):
    """
    Return a 403 error body associated with a Nova forbidden error.
    Also sets the response code on the request.

    :param str message: The message to include in the bad request body.
    :param request: The request on which to set the response code.

    :return: dictionary representing the error body.
    """
    return _nova_error_message("forbidden", message, FORBIDDEN, request)


def conflicting(message, request):
    """
    Return a 409 error body associated with a Nova conflicting request error.

    :param str message: The message to include in the bad request body.
    :param request: The request on which to set the response code.

    :return: dictionary representing the error body.
    """
    return _nova_error_message("conflictingRequest", message, CONFLICT, request)


@attributes(["collection", "server_id", "server_name", "metadata",
             "creation_time", "update_time", "public_ips", "private_ips",
             "status", "flavor_ref", "image_ref", "disk_config", "key_name",
             "admin_password", "creation_request_json",
             Attribute('max_metadata_items', instance_of=int,
                       default_value=40)])
class Server(object):
    """
    A :obj:`Server` is a representation of all the state associated with a nova
    server.  It can produce JSON-serializable objects for various pieces of
    state that are required for API responses.
    """

    static_defaults = {
        "OS-EXT-STS:power_state": 1,
        "OS-EXT-STS:task_state": None,
        "accessIPv4": "198.101.241.238",  # TODO: same as public IP
        "accessIPv6": "2001:4800:780e:0510:d87b:9cbc:ff04:513a",
        "hostId": "33ccb6c82f3625748b6f2338f54d8e9df07cc583251e001355569056",
        "progress": 100,
        "user_id": "170454"
    }

    def addresses_json(self):
        """
        Create a JSON-serializable data structure describing the public and
        private IPs associated with this server.
        """
        return {
            "private": [addr.json() for addr in self.private_ips],
            "public": [addr.json() for addr in self.public_ips]
        }

    def links_json(self, absolutize_url):
        """
        Create a JSON-serializable data structure describing the links to this
        server.

        :param callable absolutize_url: see :obj:`default_create_behavior`.
        """
        tenant_id = self.collection.tenant_id
        server_id = self.server_id
        return [
            {
                "href": absolutize_url("v2/{0}/servers/{1}"
                                       .format(tenant_id, server_id)),
                "rel": "self"
            },
            {
                "href": absolutize_url("{0}/servers/{1}"
                                       .format(tenant_id, server_id)),
                "rel": "bookmark"
            }
        ]

    def brief_json(self, absolutize_url):
        """
        Brief JSON-serializable version of this server, for the non-details
        list servers request.
        """
        return {
            'name': self.server_name,
            'links': self.links_json(absolutize_url),
            'id': self.server_id
        }

    def detail_json(self, absolutize_url):
        """
        Long-form JSON-serializable object representation of this server, as
        returned by either a GET on this individual server or a member in the
        list returned by the list-details request.
        """
        template = self.static_defaults.copy()
        tenant_id = self.collection.tenant_id
        template.update({
            "id": self.server_id,
            "OS-DCF:diskConfig": self.disk_config,
            "OS-EXT-STS:vm_state": self.status,
            "addresses": self.addresses_json(),
            "created": seconds_to_timestamp(self.creation_time),
            "updated": seconds_to_timestamp(self.update_time),
            "flavor": {
                "id": self.flavor_ref,
                "links": [{
                    "href": absolutize_url(
                        "{0}/flavors/{1}".format(tenant_id, self.flavor_ref)),
                    "rel": "bookmark"}],
            },
            "image": {
                "id": self.image_ref,
                "links": [{
                    "href": absolutize_url("{0}/images/{1}".format(
                        tenant_id, self.flavor_ref)),
                    "rel": "bookmark"
                }]
            }
            if self.image_ref is not None else '',
            "links": self.links_json(absolutize_url),
            "key_name": self.key_name,
            "metadata": self.metadata,
            "name": self.server_name,
            "tenant_id": tenant_id,
            "status": self.status
        })
        return template

    def creation_response_json(self, absolutize_url):
        """
        A JSON-serializable object returned for the initial creation of this
        server.
        """
        return {
            'server': {
                "OS-DCF:diskConfig": self.disk_config,
                "id": self.server_id,
                "links": self.links_json(absolutize_url),
                "adminPass": self.admin_password,
            }
        }

    def set_metadata(self, metadata):
        """
        Replace all metadata with given metadata
        """
        self.metadata = metadata
        self.update_time = self.collection.clock.seconds()

    def set_metadata_item(self, key, value):
        """
        Set a metadata item on the server.

        All the response messages have been verified as of 2015-04-23 against
        Rackspace Nova.
        """
        if key not in self.metadata:
            if len(self.metadata) == self.max_metadata_items:
                raise LimitError(nova_message=(
                    "Maximum number of metadata items exceeds {0}"
                    .format(self.max_metadata_items)))

        if not isinstance(value, string_types):
            raise BadRequestError(nova_message=(
                "Invalid metadata: The input is not a string or unicode"))

        self.metadata[key] = value
        self.update_time = self.collection.clock.seconds()

    def update_status(self, status):
        """
        Update status on the server. This will also update the `update_time`
        of the server
        """
        self.status = status
        self.update_time = self.collection.clock.seconds()

    @classmethod
    def validate_metadata(cls, metadata, max_metadata_items=40):
        """
        Validate the given metadata - this is the complete metadata dict.

        All the response messages have been verified as of 2015-04-23 against
        Rackspace Nova.
        """
        if not isinstance(metadata, dict):
            raise BadRequestError(nova_message="Malformed request body")
        if len(metadata) > max_metadata_items:
            raise LimitError(nova_message=(
                "Maximum number of metadata items exceeds {0}"
                .format(max_metadata_items)))
        if not all(isinstance(v, string_types) for v in metadata.values()):
            raise BadRequestError(nova_message=(
                "Invalid metadata: The input is not a string or unicode"))

    @classmethod
    def from_creation_request_json(cls, collection, creation_json,
                                   ipsegment=lambda: randrange(255),
                                   max_metadata_items=40):
        """
        Create a :obj:`Server` from a JSON-serializable object that would be in
        the body of a create server request.
        """
        now = collection.clock.seconds()
        server_json = creation_json['server']
        disk_config = server_json.get('OS-DCF:diskConfig', None) or "AUTO"
        if disk_config not in ["AUTO", "MANUAL"]:
            raise BadRequestError(nova_message=(
                "OS-DCF:diskConfig must be either 'MANUAL' or 'AUTO'."))

        metadata = server_json.get("metadata") or {}
        cls.validate_metadata(metadata, max_metadata_items)

        while True:
            private_ip = IPv4Address(
                address="10.180.{0}.{1}".format(ipsegment(), ipsegment()))
            if private_ip not in [addr for server in collection.servers
                                  for addr in server.private_ips]:
                break

        self = cls(
            collection=collection,
            server_name=server_json['name'],
            server_id=('test-server{0}-id-{0}'
                       .format(str(randrange(9999999999)))),
            metadata=metadata,
            creation_time=now,
            update_time=now,
            private_ips=[private_ip],
            public_ips=[
                IPv4Address(address="198.101.241.{0}".format(ipsegment())),
                IPv6Address(address="2001:4800:780e:0510:d87b:9cbc:ff04:513a")
            ],
            key_name=None if 'key_name' not in server_json else server_json['key_name'],
            creation_request_json=creation_json,
            flavor_ref=server_json['flavorRef'],
            image_ref=server_json['imageRef'] or '',
            disk_config=disk_config,
            status="ACTIVE",
            admin_password=random_string(12),
            max_metadata_items=max_metadata_items
        )
        collection.servers.append(self)
        return self


@attributes(["address"])
class IPv4Address(object):
    """
    An IPv4 address for a server.
    """

    def json(self):
        """
        A JSON-serializable representation of this address.
        """
        return {"addr": self.address, "version": 4}


@attributes(["address"])
class IPv6Address(object):
    """
    An IPv6 address for a server.
    """

    def json(self):
        """
        A JSON-serializable representation of this address.
        """
        return {"addr": self.address, "version": 6}


server_creation = EventDescription()


@server_creation.declare_criterion("server_name")
def server_name_criterion(value):
    """
    Return a Criterion which matches the given regular expression string
    against the ``"server_name"`` attribute.
    """
    return Criterion(name='server_name', predicate=regexp_predicate(value))


@server_creation.declare_criterion("metadata")
def metadata_criterion(value):
    """
    Return a Criterion which matches against metadata.

    :param value: a dictionary, mapping a regular expression of a metadata key
        to a regular expression describing a metadata value.
    :type value: dict mapping unicode to unicode
    """
    def predicate(attribute):
        for k, v in value.items():
            if not re.compile(v).match(attribute.get(k, "")):
                return False
        return True
    return Criterion(name='metadata', predicate=predicate)


@server_creation.declare_default_behavior
def default_create_behavior(collection, http, json, absolutize_url,
                            ipsegment=lambda: randrange(255), hook=None):
    """
    Default behavior in response to a server creation.

    :param absolutize_url: A 1-argument function that takes a string and
        returns a string, where the input is the list of segments identifying a
        particular object within the compute service's URL hierarchy within a
        region, and the output is an absolute URL that identifies that same
        object.  Note that the region's URL hierarchy begins before the version
        identifier, because bookmark links omit the version identifier and go
        straight to the tenant ID.  Be sure to include the 'v2' first if you
        are generating a versioned URL; the tenant ID itself should always be
        passed in as part of the input, either the second or first segment,
        depending on whether the version is included or not respectively.

        Note that this is passed in on every request so that servers do not
        retain a memory of their full URLs internally, and therefore you may
        access Mimic under different hostnames and it will give you URLs
        appropriate to how you accessed it every time.  This is intentionally
        to support the use-case of running tests against your local dev machine
        as 'localhost' and then showing someone else the state that things are
        in when they will have to access your machine under a different
        hostname and therefore a different URI.

    :param ipsegment: A hook provided for IP generation so the IP addresses in
        tests are deterministic; normally a random number between 0 and 255.
    :param callable hook: a 1-argument callable which, if specified, will be
        invoked with the :obj:`Server` object after creating it, but before
        generating the response.  This allows for invoking the default behavior
        with a small tweak to alter the server's state in some way.
    """
    new_server = Server.from_creation_request_json(collection, json, ipsegment)
    if hook is not None:
        hook(new_server)
    response = new_server.creation_response_json(absolutize_url)
    http.setResponseCode(ACCEPTED)
    return dumps(response)


def default_with_hook(function):
    """
    A convenience decorator to make it easy to write a slightly-customized
    version of :obj:`default_create_behavior`.

    :param Server function: a 1-argument function taking a :obj:`Server` and
        returning Nothing.

    :return: a creation behavior, i.e. a function with the same signature as
             :obj:`default_create_behavior`, which does the default behavior of
             creating a server, adding it to the collection, and returning a
             successful ``ACCEPTED`` response, but with the server's state
             first modified by whatever the input ``function`` does.
    """
    def hooked(collection, http, json, absolutize_url):
        return default_create_behavior(collection, http, json, absolutize_url,
                                       hook=function)
    return hooked


def _get_failure_behavior(parameters, create=False):
    """
    Helper function to produce a failure to create function.  Either creating
    the server or not.

    Takes three parameters:

    ``"code"``, an integer describing the HTTP response code, and
    ``"message"``, a string describing a textual message.
    ``"type"``, a string representing what type of error message it is

    If ``type`` is "string", the message is just returned as the string body.
    Otherwise, the following JSON body will be synthesized (as per the
    canonical Nova error format):

    ```
    {
        <type>: {
            "message": <message>,
            "code": <code>
        }
    }

    The default type is computeFault, the default code is 500, and the default
    message is "The server has either erred or is incapable of performing the
    requested operation".
    """
    status_code = parameters.get("code", 500)
    failure_type = parameters.get("type", "computeFault")
    failure_message = parameters.get(
        "message",
        ("The server has either erred or is incapable of performing the "
         "requested operation"))

    if failure_type == "string":
        fail_body = failure_message
    else:
        fail_body = dumps({
            failure_type: {
                "message": failure_message,
                "code": status_code
            }
        })

    def _fail(collection, http, json, absolutize_url):
        if create:
            Server.from_creation_request_json(
                collection, json, lambda: randrange(255))

        http.setResponseCode(status_code)
        return fail_body
    return _fail


@server_creation.declare_behavior_creator("fail")
def create_fail_behavior(parameters):
    """
    Create a failing behavior for server creation.

    Takes three parameters:

    ``"code"``, an integer describing the HTTP response code, and
    ``"message"``, a string describing a textual message.
    ``"type"``, a string representing what type of error message it is

    If ``type`` is "string", the message is just returned as the string body.
    Otherwise, the following JSON body will be synthesized (as per the
    canonical Nova error format):

    ```
    {
        <type>: {
            "message": <message>,
            "code": <code>
        }
    }

    The default type is computeFault, the default code is 500, and the default
    message is "The server has either erred or is incapable of performing the
    requested operation".
    """
    return _get_failure_behavior(parameters)


@server_creation.declare_behavior_creator("false-negative")
def create_success_report_failure_behavior(parameters):
    """
    Create a behavior that reports failure, but actually succeeds, for server
    creation.

    Takes three parameters:

    ``"code"``, an integer describing the HTTP response code, and
    ``"message"``, a string describing a textual message.
    ``"type"``, a string representing what type of error message it is

    If ``type`` is "string", the message is just returned as the string body.
    Otherwise, the following JSON body will be synthesized (as per the
    canonical Nova error format):

    ```
    {
        <type>: {
            "message": <message>,
            "code": <code>
        }
    }

    The default type is computeFault, the default code is 500, and the default
    message is "The server has either erred or is incapable of performing the
    requested operation".
    """
    return _get_failure_behavior(parameters, create=True)


@server_creation.declare_behavior_creator("build")
def create_building_behavior(parameters):
    """
    Create a "build" behavior for server creation.

    Puts the server into the "BUILD" status immediately, transitioning it to
    "ACTIVE" after a requested amount of time.

    Takes one parameter:

    ``"duration"`` which is a Number, the duration of the build process in
    seconds.
    """
    duration = parameters["duration"]

    @default_with_hook
    def set_building(server):
        server.update_status(u"BUILD")
        server.collection.clock.callLater(
            duration,
            server.update_status,
            u"ACTIVE")
    return set_building


@server_creation.declare_behavior_creator("error")
def create_error_status_behavior(parameters=None):
    """
    Create an "error" behavior for server creation.

    The created server will go into the ``"ERROR"`` state immediately.

    Takes no parameters.
    """
    @default_with_hook
    def set_error(server):
        server.update_status(u"ERROR")
    return set_error


@server_creation.declare_behavior_creator("active-then-error")
def active_then_error(parameters):
    """
    Sometimes, a server goes into "active", but later (for unknown reasons)
    goes into "error"; presumably due to a hardware failure or similar
    operational issue.

    Takes one parameter:

    ``"duration"`` which is a Number, the duration of the time spent in the
    ``ACTIVE`` state.
    """
    duration = parameters["duration"]

    @default_with_hook
    def fail_later(server):
        server.update_status(u"ACTIVE")
        server.collection.clock.callLater(
            duration,
            server.update_status,
            u"ERROR")
    return fail_later


def metadata_to_creation_behavior(metadata):
    """
    Examine the metadata given to a server creation request, and return a
    behavior based on the values present there.
    """
    if 'create_server_failure' in metadata:
        return create_fail_behavior(loads(metadata['create_server_failure']))
    if 'server_building' in metadata:
        return create_building_behavior(
            {"duration": float(metadata['server_building'])}
        )
    if 'server_error' in metadata:
        return create_error_status_behavior()
    return None


@attributes(
    ["tenant_id", "region_name", "clock",
     Attribute("servers", default_factory=list),
     Attribute("image_store", default_factory=list),
     Attribute(
         "behavior_registry_collection",
         default_factory=lambda: BehaviorRegistryCollection())]
)
class RegionalServerCollection(object):
    """
    A collection of servers, in a given region, for a given tenant.
    """

    def server_by_id(self, server_id):
        """
        Retrieve a :obj:`Server` object by its ID.
        """
        for server in self.servers:
            if server.server_id == server_id and server.status != u"DELETED":
                return server

    def request_creation(self, creation_http_request, creation_json,
                         absolutize_url):
        """
        Request that a server be created.
        """
        metadata = creation_json.get('server', {}).get('metadata') or {}
        behavior = metadata_to_creation_behavior(metadata)
        if behavior is None:
            registry = self.behavior_registry_collection.registry_by_event(
                server_creation)
            behavior = registry.behavior_for_attributes({
                "tenant_id": self.tenant_id,
                "server_name": creation_json["server"]["name"],
                "metadata": creation_json["server"].get("metadata", {})
            })
        return behavior(self, creation_http_request, creation_json,
                        absolutize_url)

    def request_read(self, http_get_request, server_id, absolutize_url):
        """
        Request the information / details for an individual server.

        Not found response verified against Rackspace Cloud Servers as of
        2015-04-30.
        """
        server = self.server_by_id(server_id)
        if server is None:
            return dumps(not_found("Instance could not be found",
                                   http_get_request))
        return dumps({"server": server.detail_json(absolutize_url)})

    def request_ips(self, http_get_ips_request, server_id):
        """
        Request the addresses JSON for a specific server.

        Not found response verified against Rackspace Cloud Servers as of
        2015-04-30.
        """
        http_get_ips_request.setResponseCode(200)
        server = self.server_by_id(server_id)
        if server is None:
            return dumps(not_found("Instance does not exist",
                                   http_get_ips_request))
        return dumps({"addresses": server.addresses_json()})

    def request_list(self, http_get_request, include_details, absolutize_url,
                     name=u"", limit=None, marker=None, changes_since=None):
        """
        Request the list JSON for all servers.

        :param str changes_since: ISO8601 formatted datetime. Based on
            http://docs.rackspace.com/servers/api/v2/cs-devguide/content/ChangesSince.html

        Note: only supports filtering by name right now, but will need to
        support more going forward.

        Pagination behavior verified against Rackspace Nova as of 2015-04-29.
        """
        to_be_listed = self.servers

        if changes_since is not None:
            since = timestamp_to_seconds(changes_since)
            to_be_listed = filter(lambda s: s.update_time >= since, to_be_listed)

        # marker can be passed without limit, in which case the whole server
        # list, after the server that matches the marker, is returned
        if marker is not None:
            last_seen = [i for i, server in enumerate(to_be_listed)
                         if server.server_id == marker]
            if not last_seen:
                # Error response and body verified against Rackspace Nova as
                # of 2015-04-29
                return dumps(bad_request(
                    "marker [{0}] not found".format(marker),
                    http_get_request))
            else:
                last_seen = last_seen[0]
                to_be_listed = to_be_listed[last_seen + 1:]

        # A valid marker is an ID in the entire server list.  It does not
        # have to be for a server that matches the given name.
        to_be_listed = [server for server in to_be_listed
                        if name in server.server_name]

        if changes_since is None:
            to_be_listed = filter(lambda s: s.status != u"DELETED", to_be_listed)

        if limit is not None:
            try:
                limit = int(limit)
            except ValueError:
                return dumps(bad_request("limit param must be an integer",
                                         http_get_request))
            if limit < 0:
                return dumps(bad_request("limit param must be positive",
                                         http_get_request))

            to_be_listed = to_be_listed[:limit]

        result = {
            "servers": [
                server.brief_json(absolutize_url) if not include_details
                else server.detail_json(absolutize_url)
                for server in to_be_listed
            ]
        }

        # A server links blob is included only if limit is passed.  If
        # only the marker was provided, no server links blob is included.
        # Note that if limit=0, an empty server list is returned and no
        # server link blob is returned.
        if limit and len(to_be_listed) >= limit:
            query_params = {'limit': limit}
            query_params['marker'] = to_be_listed[-1].server_id
            if name:
                query_params['name'] = name

            path = "v2/{0}/servers{1}?{2}".format(
                self.tenant_id,
                "/detail" if include_details else "",
                urlencode(query_params))
            result["servers_links"] = [{
                "href": absolutize_url(path),
                "rel": "next"
            }]

        return dumps(result)

    def request_delete(self, http_delete_request, server_id):
        """
        Delete a server with the given ID.

        Not found response verified against Rackspace Cloud Servers as of
        2015-04-30.
        """
        server = self.server_by_id(server_id)
        if server is None:
            return dumps(not_found("Instance could not be found",
                                   http_delete_request))
        if 'delete_server_failure' in server.metadata:
            srvfail = loads(server.metadata['delete_server_failure'])
            if srvfail['times']:
                srvfail['times'] -= 1
                server.metadata['delete_server_failure'] = dumps(srvfail)
                http_delete_request.setResponseCode(500)
                return b''
        http_delete_request.setResponseCode(204)
        server.update_status(u"DELETED")
        return b''

    def request_action(self, http_action_request, server_id, absolutize_url):
        """
        Perform the requested action on the provided server
        """
        server = self.server_by_id(server_id)
        if server is None:
            return dumps(not_found("Instance " + server_id + " could not be found",
                                   http_action_request))
        action_json = loads(http_action_request.content.read())
        if 'resize' in action_json:
            flavor = action_json['resize'].get('flavorRef')
            if not flavor:
                return dumps(bad_request("Resize requests require 'flavorRef' attribute",
                                         http_action_request))

            server.status = 'VERIFY_RESIZE'
            server.oldFlavor = server.flavor_ref
            server.flavor_ref = flavor
            http_action_request.setResponseCode(202)
            return b''

        elif 'confirmResize' in action_json or 'revertResize' in action_json:
            if server.status == 'VERIFY_RESIZE' and 'confirmResize' in action_json:
                server.status = 'ACTIVE'
                http_action_request.setResponseCode(204)
                return b''
            elif server.status == 'VERIFY_RESIZE' and 'revertResize' in action_json:
                server.status = 'ACTIVE'
                server.flavor_ref = server.oldFlavor
                http_action_request.setResponseCode(202)
                return b''
            else:
                return dumps(conflicting("Cannot '" + action_json.keys()[0] + "' instance " + server_id +
                                         " while it is in vm_state active", http_action_request))
        elif 'rescue' in action_json:
            if server.status != 'ACTIVE':
                return dumps(conflicting("Cannot 'rescue' instance " + server_id +
                                         " while it is in task state other than active",
                                         http_action_request))
            else:
                server.status = 'RESCUE'
                http_action_request.setResponseCode(200)
                password = random_string(12)
                return dumps({"adminPass": password})

        elif 'unrescue' in action_json:
            if server.status == 'RESCUE':
                server.status = 'ACTIVE'
                http_action_request.setResponseCode(200)
                return b''
            else:
                return dumps(conflicting("Cannot 'unrescue' instance " + server_id +
                                         " while it is in task state other than rescue",
                                         http_action_request))

        elif 'reboot' in action_json:
            reboot_type = action_json['reboot'].get('type')
            if not reboot_type:
                return dumps(bad_request("Missing argument 'type' for reboot",
                                         http_action_request))
            if reboot_type == 'HARD':
                server.status = 'HARD_REBOOT'
                http_action_request.setResponseCode(202)
                server.collection.clock.callLater(
                    6.0,
                    server.update_status,
                    u"ACTIVE")
                return b''
            elif reboot_type == 'SOFT':
                server.status = 'REBOOT'
                http_action_request.setResponseCode(202)
                server.collection.clock.callLater(
                    3.0,
                    server.update_status,
                    u"ACTIVE")
                return b''
            else:
                return dumps(bad_request("Argument 'type' for reboot is not HARD or SOFT",
                                         http_action_request))

        elif 'changePassword' in action_json:
            password = action_json['changePassword'].get('adminPass')
            if not password:
                return dumps(bad_request("No adminPass was specified",
                                         http_action_request))
            if server.status == 'ACTIVE':
                http_action_request.setResponseCode(202)
                return b''
            else:
                return dumps(conflicting("Cannot 'changePassword' instance " + server_id +
                                         " while it is in task state other than active",
                                         http_action_request))

        elif 'rebuild' in action_json:
            image_ref = action_json['rebuild'].get('imageRef')
            if not image_ref:
                return dumps(bad_request("Could not parse imageRef from request.", http_action_request))
            if server.status == 'ACTIVE':
                server.image_ref = image_ref
                server.status = 'REBUILD'
                http_action_request.setResponseCode(202)
                server.collection.clock.callLater(
                    5.0,
                    server.update_status,
                    u"ACTIVE")
                server_details = server.detail_json(absolutize_url)
                server_details['adminPass'] = 'password'
                return dumps({"server": server_details})
            else:
                return dumps(conflicting("Cannot 'rebuild' instance " + server_id +
                                         " while it is in task state other than active",
                                         http_action_request))

        else:
            return dumps(bad_request("There is no such action currently supported", http_action_request))


@attributes(["tenant_id", "clock",
             Attribute("regional_collections", default_factory=dict)])
class GlobalServerCollections(object):
    """
    A :obj:`GlobalServerCollections` is a set of all the
    :obj:`RegionalServerCollection` objects owned by a given tenant.  In other
    words, all the objects that a single tenant owns globally in a Nova
    service.
    """

    def collection_for_region(self, region_name):
        """
        Get a :obj:`RegionalServerCollection` for the region identified by the
        given name.
        """
        if region_name not in self.regional_collections:
            self.regional_collections[region_name] = (
                RegionalServerCollection(tenant_id=self.tenant_id,
                                         region_name=region_name,
                                         clock=self.clock)
            )
        return self.regional_collections[region_name]
