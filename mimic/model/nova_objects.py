from characteristic import attributes, Attribute
from random import randrange
from json import loads, dumps

from mimic.util.helper import seconds_to_timestamp
from mimic.util.helper import invalid_resource

@attributes(["collection", "server_id", "server_name", "metadata",
             "creation_time", "update_time", "public_ips", "private_ips",
             "status", "flavor_ref", "image_ref", "disk_config",
             "admin_password", "creation_request_json"])
class Server(object):
    """
    
    """

    static_defaults = {
        "OS-EXT-STS:power_state": 1,
        "OS-EXT-STS:task_state": None,
        "accessIPv4": "198.101.241.238", # TODO: same as public IP
        "accessIPv6": "2001:4800:780e:0510:d87b:9cbc:ff04:513a",
        "key_name": None,
        "hostId": "33ccb6c82f3625748b6f2338f54d8e9df07cc583251e001355569056",
        "progress": 100,
        "user_id": "170454"
    }

    def addresses_json(self):
        """
        
        """
        return {
            "private": [addr.json() for addr in self.private_ips],
            "public": [addr.json() for addr in self.public_ips]
        }

    def links_json(self, absolutize_url):
        """
        
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
        Brief version of this server, for the non-details list servers request.
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
        template.update({
            "OS-DCF:diskConfig": self.disk_config,
            "OS-EXT-STS:vm_state": self.status,
            "addresses": self.addresses_json(),
            "created": seconds_to_timestamp(self.creation_time),
            "updated": seconds_to_timestamp(self.updated_time),
            "flavor": {
                "id": self.flavor_ref,
                "links": [{"href": absolutize_url(
                    "{0}/flavors/{1}".format(self.tenant_id,
                                             self.flavor_ref))}],
                "rel": "bookmark"
            },
            "image": {
                "id": self.image_ref,
                "links": [{
                    "href": absolutize_url("{0}/images/{1}".format(
                        self.tenant_id, self.flavor_ref))
                }]
            }
            if self.image_ref is not None else '',
            "links": self.links_json(),
            "metadata": self.metadata,
            "name": self.name,
            "tenant_id": self.tenant_id,
            "status": self.status
        })

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

    def from_creation_request_json(self, collection, json,
                                   ipsegment=lambda: randrange(255)):
        """
        Create a :obj:`Server` from a JSON-serializable object that would be in
        the body of a create server request.
        """
        now = collection.clock.seconds()
        return Server(
            collection=collection,
            server_name=json['name'],
            server_id=('test-server{0}-id-{0}'
                       .format(str(randrange(9999999999)))),
            metadata=json.get("metadata") or {},
            created_time=now,
            update_time=now,
            private_ips=[
                IPv4Address("10.180.{0}.{1}".format(ipsegment(), ipsegment())),
            ],
            public_ips=[
                IPv4Address(address="198.101.241.{0}".format(ipsegment())),
                IPv6Address(address="2001:4800:780e:0510:d87b:9cbc:ff04:513a")
            ],
            creation_request_json=json,
            flavor_ref=json['flavorRef'],
            image_ref=json['imageRef'] or '',
            disk_config=json['OS-DCF:diskConfig'],
        )


@attributes(["address"])
class IPv4Address(object):
    """
    An IPv6 address for a server.
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
                            ipsegment=lambda: randrange(255)):
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
    """
    new_server = Server.from_creation_request_json(collection, json, ipsegment)
    response = new_server.creation_response_json(absolutize_url)
    http.setResponseCode(201)
    return dumps(response)


def metadata_to_creation_behavior(metadata):
    """
    Examine the metadata given to a server creation request, and return a
    behavior based on the values present there.
    """
    if 'create_server_failure' in metadata:
        def fail_and_dont_do_anything(collection, http, json, absolutize_url):
            # behavior for failing to even start to build
            failure = loads(metadata['create_server_failure'])
            http.setResponseCode(failure['code'])
            return invalid_resource(failure['message', failure['code']])
    return None


@attributes(["tenant_id", "region_name", "clock",
             Attribute("servers", default_factory=list)])
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

    def registered_creation_behavior(self, creation_http_request,
                                     creation_json):
        """
        Retrieve a behavior that was previously registered via a control plane
        request to inject an error in advance, based on whether it matches the
        parameters in the given creation JSON and HTTP request properties.
        """
        return None

    def request_creation(self, creation_http_request, creation_json,
                         absolutize_url):
        """
        Request that a server be created.
        """
        behavior = metadata_to_creation_behavior(
            creation_json.get('metadata'))
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
        return dumps(self.server_by_id(server_id).detail_json(absolutize_url))

    def request_ips(self, http_get_ips_request, server_id):
        """
        Request the addresses JSON for a specific server.
        """
        http_get_ips_request.setResponseCode(200)
        server = self.server_by_id(server_id)
        return {"addresses": server.addresses_json()}

    def request_list(self, http_get_request, include_details, absolutize_url,
                     name=None):
        """
        Request the list JSON for all servers.

        Note: only supports filtering by name right now, but will need to
        support more going forward.
        """
        return dumps({"servers": [
            server.brief_json(url) if not include_details
            else server.detail_json(url)
            for server in self.servers]})

    def request_delete(self, http_delete_request, server_id):
        """
        Delete a server with the given ID.
        """
        http_delete_request.setResponseCode(204)
        self.servers.remove(self.server_by_id(server_id))
        return b''


@attributes(["tenant_id", "clock",
             Attribute("regional_collections", default_factory=dict)])
class GlobalServerCollections(object):
    """
    
    """

    def collection_for_region(self, region_name):
        """
        
        """
        if region_name not in self.regional_collections:
            self.regional_collections[region_name] = (
                RegionalServerCollection(tenant_id=self.tenant_id,
                                         region_name=region_name,
                                         clock=self.clock)
            )
        return self.regional_collections[region_name]
