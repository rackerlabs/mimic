"""
Model objects for the Nova mimic.
"""

from characteristic import attributes, Attribute
from random import randrange
from json import loads, dumps

from mimic.util.helper import seconds_to_timestamp
from mimic.util.helper import invalid_resource

from twisted.web.http import ACCEPTED, NOT_FOUND


@attributes(["collection", "server_id", "server_name", "metadata",
             "creation_time", "update_time", "public_ips", "private_ips",
             "status", "flavor_ref", "image_ref", "disk_config",
             "admin_password", "creation_request_json"])
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
        "key_name": None,
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

    @classmethod
    def from_creation_request_json(cls, collection, creation_json,
                                   ipsegment=lambda: randrange(255)):
        """
        Create a :obj:`Server` from a JSON-serializable object that would be in
        the body of a create server request.
        """
        now = collection.clock.seconds()
        server_json = creation_json['server']
        self = cls(
            collection=collection,
            server_name=server_json['name'],
            server_id=('test-server{0}-id-{0}'
                       .format(str(randrange(9999999999)))),
            metadata=server_json.get("metadata") or {},
            creation_time=now,
            update_time=now,
            private_ips=[
                IPv4Address(address="10.180.{0}.{1}"
                            .format(ipsegment(), ipsegment())),
            ],
            public_ips=[
                IPv4Address(address="198.101.241.{0}".format(ipsegment())),
                IPv6Address(address="2001:4800:780e:0510:d87b:9cbc:ff04:513a")
            ],
            creation_request_json=creation_json,
            flavor_ref=server_json['flavorRef'],
            image_ref=server_json['imageRef'] or '',
            disk_config="AUTO",
            # ^ TODO: https://github.com/rackerlabs/mimic/issues/163
            status="ACTIVE",
            admin_password="testpassword",
            # ^ TODO: https://github.com/rackerlabs/mimic/issues/164
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


def metadata_to_creation_behavior(metadata):
    """
    Examine the metadata given to a server creation request, and return a
    behavior based on the values present there.
    """
    if 'create_server_failure' in metadata:
        failure = loads(metadata['create_server_failure'])

        def fail_and_dont_do_anything(collection, http, json, absolutize_url):
            # behavior for failing to even start to build
            http.setResponseCode(failure['code'])
            return dumps(invalid_resource(failure['message'], failure['code']))
        return fail_and_dont_do_anything
    if 'server_building' in metadata:
        @default_with_hook
        def set_building(server):
            server.status = u"BUILD"
            server.collection.clock.callLater(
                float(metadata['server_building']),
                lambda: setattr(server, "status", u"ACTIVE"))
        return set_building
    if 'server_error' in metadata:
        @default_with_hook
        def set_error(server):
            server.status = u"ERROR"
            server.collection.clock.callLater(
                float(metadata['server_error']),
                lambda: setattr(server, "status", u"ACTIVE"))
        return set_error
    return None


@attributes(["tenant_id", "region_name", "clock",
             Attribute("servers", default_factory=list),
             Attribute("creation_behaviors_and_criteria",
                       default_factory=list)])
class RegionalServerCollection(object):
    """
    A collection of servers, in a given region, for a given tenant.
    """

    def server_by_id(self, server_id):
        """
        Retrieve a :obj:`Server` object by its ID.
        """
        for server in self.servers:
            if server.server_id == server_id:
                return server

    def register_creation_behavior_for_criteria(self, behavior, criteria):
        """
        Register the given behavior for server creation based on the given
        criteria.
        """
        self.creation_behaviors_and_criteria.append((behavior, criteria))

    def registered_creation_behavior(self, creation_http_request,
                                     creation_json):
        """
        Retrieve a behavior that was previously registered via a control plane
        request to inject an error in advance, based on whether it matches the
        parameters in the given creation JSON and HTTP request properties.
        """
        creation_attributes = {
            "tenant_id": self.tenant_id,
            "server_name": creation_json["server"]["name"],
            "metadata": creation_json["server"].get("metadata")
        }
        for behavior, criteria in self.creation_behaviors_and_criteria:
            if criteria.evaluate(creation_attributes):
                return behavior
        return None

    def request_creation(self, creation_http_request, creation_json,
                         absolutize_url):
        """
        Request that a server be created.
        """
        behavior = metadata_to_creation_behavior(
            creation_json.get('server', {}).get('metadata', {}))
        if behavior is None:
            behavior = self.registered_creation_behavior(creation_http_request,
                                                         creation_json)
        if behavior is None:
            behavior = default_create_behavior
        return behavior(self, creation_http_request, creation_json,
                        absolutize_url)

    def request_read(self, http_get_request, server_id, absolutize_url):
        """
        Request the information / details for an individual server.
        """
        server = self.server_by_id(server_id)
        if server is None:
            http_get_request.setResponseCode(404)
            return None
        return dumps({"server": server.detail_json(absolutize_url)})

    def request_ips(self, http_get_ips_request, server_id):
        """
        Request the addresses JSON for a specific server.
        """
        http_get_ips_request.setResponseCode(200)
        server = self.server_by_id(server_id)
        if server is None:
            http_get_ips_request.setResponseCode(NOT_FOUND)
            return None
        return dumps({"addresses": server.addresses_json()})

    def request_list(self, http_get_request, include_details, absolutize_url,
                     name=u""):
        """
        Request the list JSON for all servers.

        Note: only supports filtering by name right now, but will need to
        support more going forward.
        """
        return dumps(
            {"servers": [
                server.brief_json(absolutize_url) if not include_details
                else server.detail_json(absolutize_url)
                for server in self.servers
                if name in server.server_name
            ]}
        )

    def request_delete(self, http_delete_request, server_id):
        """
        Delete a server with the given ID.
        """
        server = self.server_by_id(server_id)
        if server is None:
            http_delete_request.setResponseCode(404)
            return b''
        if 'delete_server_failure' in server.metadata:
            srvfail = loads(server.metadata['delete_server_failure'])
            if srvfail['times']:
                srvfail['times'] -= 1
                server.metadata['delete_server_failure'] = dumps(srvfail)
                http_delete_request.setResponseCode(500)
                return b''
        http_delete_request.setResponseCode(204)
        self.servers.remove(server)
        return b''


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
