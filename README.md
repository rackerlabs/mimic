<img alt="MIMIC" src="https://i.imgur.com/eodn4M4.png" height="75">

Mimic is an API-compatible mock service for  __Openstack Compute__ and __Rackspace's implementation of Identity and Cloud Load balancers__. It is backed by in-memory data structure rather than a potentially expensive database.

Mimic helps with:
* fast set-up
* instant response
* cost efficient
* enables offline development
* enables ability to test unusual behaviors/errors of an api
* acts as a central repository for mocked responses from services

### Quick start

The fastest way to install and start Mimic is:

    pip install mimic
    twistd -n mimic

You can test the server started successfully by sending this request and checking for the
welcome message:

    curl http://localhost:8900
    >> To get started with Mimic, POST an authentication request to:
    >> /identity/v2.0/tokens

You can use the command below to test authentication and see your service catalog. The service catalog contains the endpoints for other available APIs.

    curl -s -XPOST -d '{"auth":{"RAX-KSKEY:apiKeyCredentials":{"username":"mimic","apiKey":"12345"}}}' http://localhost:8900/identity/v2.0/tokens | python -m json.tool

In order to use Mimic with most other projects you just need to override the Authentication Endpoint. In many projects, including the [OpenStack Client CLI](https://wiki.openstack.org/wiki/OpenStackClient) or the [OpenStack Keystone client](https://github.com/openstack/python-keystoneclient/) you can do that by setting the `OS_AUTH_URL` environment variable or the `--os-auth-url` option. For example:

    keystone --os-username mimic --os-password 1235 --os-auth-url http://localhost:8900/identity/v2.0/ catalog

### Come join us develop Mimic! Talk to us at ##mimic on irc.freenode.net ###

#### Build status: ####
[![Build Status](https://travis-ci.org/rackerlabs/mimic.svg?branch=master)](https://travis-ci.org/rackerlabs/mimic)

[![codecov.io](https://codecov.io/github/rackerlabs/mimic/coverage.svg?branch=master)](https://codecov.io/github/rackerlabs/mimic?branch=master)

## Compute ##

#### Calls supported: ####
https://github.com/rackerlabs/mimic/blob/master/mimic/rest/nova_api.py

1. LIST servers - Lists servers on the tenant, in mimic
2. POST server - Creates a server in mimic *(look at the 'Errors or unusual behaviors supported for compute' below)*
3. GET server - Returns the server, if it exists in mimic else returns a 404
4. DELETE server - Deletes the server, if it exists in mimic else returns 404
5. LIST addresses - Lists the private and public Ips for the given server. 404 if not found.
6. GET image - If the image ID is anything but what is listed in the mimic presets, `invalid_image_ref`
			   returns 200. Else returns a 400.
7. GET flavor - If the flavor ID is anything but what is listed in the mimic presets, `invalid_flavor_ref`
			   returns 200. Else returns a 400.
8. GET limits - Returns only the absolute limits for compute

#### Errors or unusual behaviors supported for compute: ####
Based on the metadata ([mimic_presets](https://github.com/rackerlabs/mimic/blob/master/mimic/canned_responses/mimic_presets.py)) provided when a server is being created, a server can be made to behave as follows:
* Fail with the given response message and response code
* Go into an error state on creation
* Remain in building state for the specified amount of time
* Fails to delete the server, with the specified response code for the number of times specified
* Returns 'image not found' or 'flavor not found' responses for specified IDs

Eg:
Request for create server that remains in building for 120 seconds:

`{
    "server" : {
        "name" : "api-test-server-1",
        "imageRef" : "3afe97b2-26dc-49c5-a2cc-a2fc8d80c001",
        "flavorRef" : "2",
        "metadata": {"server_building": 120}
    }
 }`


## Rackspace Auth ##

#### Calls supported: ####
https://github.com/rackerlabs/mimic/blob/master/mimic/rest/auth_api.py

1. Authenticate - Given a tenant id, username and password, returns the service catalog with links to compute and load balancer links within mimic, and a test token.
2. Impersonate user (Admin call) - Given a token created by mimic in the header, returns a test token for the username.
3. GET endpoints - Given token created by mimic, returns the service catalog for that user.


## Cloud Load Balancer ##

#### Calls supported: ####
https://github.com/rackerlabs/mimic/blob/master/mimic/rest/loadbalancer_api.py

1. LIST load balancers - Lists the load balancers created in mimic
2. POST load balancer - Creates a load balancer *(look at the 'Errors or unusual behaviors supported for cloud load balancers' below)*
3. GET load balancer - Returns the load balancer if it exists, else 404
4. DELETE load balancer - Deletes the load balancer if it exists, else returns 404
5. LIST nodes - Lists the nodes on the load balancer
6. POST node - Creates a node on the load balancer
7. GET node - Returns the node if it exists, else returns 404
8. DELETE node - Deletes the node if it exists, else returns 404

#### Errors or unusual behaviors supported for cloud load balancers: ####
Based on key and value of the metadata ([mimic_presets](https://github.com/rackerlabs/mimic/blob/master/mimic/canned_responses/mimic_presets.py)) provided when a load balancer is being created, a load balancer can be made to behave as follows:
* Remain in 'BUILD' state for the specified amount of time
* Load balancer goes into 'PENDING-UPDATE' state on every add/delete node for the specified amout of time
* Load balancer goes into 'PENDING-DELETE' state on delete load balancer for the specified amout of time
* Load balancer goes into an error state on creation

Eg:
Request for create load balancer that is expected to go into 'PENDING-UPDATE' state on every add/delete
node, for 20 seconds:

`{"loadBalancer": {"name": "a-new-loadbalancer2", "protocol": "HTTP", "virtualIps": [{"type": "PUBLIC"}], "metadata": [{"key": "lb_pending_update", "value": 20}], "nodes": []}}`

## Fastly CDN ##

Fastly is one of the leading CDN providers with great API support.
Fastly is also one of the CDN providers, supported by the Openstack Poppy
project. Mimic supports all Fastly API calls needed by Openstack Poppy in its
Fastly implementation. See below for the complete list.

#### Calls supported: ####
https://github.com/rackerlabs/mimic/blob/master/mimic/rest/fastly_api.py

 1. GET /current_customer
 2. POST /service
 3. POST /service/{service_id}/version
 4. GET /service/search
 5. POST /service/{service_id}/version/{version_id}/domain
 6. GET /service/{service_id}/version/{version_id}/domain/check_all
 7. POST /service/{service_id}/version/{version_id}/backend
 8. GET /service/{service_id}/version
 9. PUT /service/{service_id}/version/{version_number}/activate
 10. DELETE /service/{service_id}
 11. GET /service/{service_id}/details
 12. GET / (health check)

## Mimic Control APIs ##

When any of Mimic's included plugins schedule a timeout, you will need to cause
Mimic's internal clock to advance for any of those timeouts to fire.

You can do this with the `tick` endpoint, like so:

    curl -s -XPOST -d '{"amount": 1.0}' http://localhost:8900/mimic/v1.1/tick | python -m json.tool

which should result in output like this:

    {
        "advanced": 1.0,
        "now": "1970-01-01T00:00:04.000000Z"
    }

Note that Mimic begins its timekeeping when all time began, in 1970.
If you would prefer to advance Mimic to something resembling the present day instead, a command like this right after Mimic starts up will do that:

    curl -s -XPOST -d '{"amount": '"$(date +%s)"'}' http://localhost:8900/mimic/v1.1/tick | python -m json.tool


## Mimic does not: ##
* support XML
* validate the auth token

## Running Mimic on a cloud server ##
1. create a cloud server with an image that by default comes with python 2.7 (eg: ubuntu 12.04) and ssh into it
2. `git clone https://github.com/rackerlabs/mimic.git`
3. `pip install -r requirements.txt` from within the mimic folder (if there is a gcc error, `apt-get install python-dev`)
4. cd into mimic or add the mimic to the PYTHONPATH and run `twistd -n mimic`

## Running Mimic on Docker ##

The repository root has a `Dockerfile` that does what you want. It exposes Mimic on port 8900 by default.

To play around with Mimic locally, try:

```
docker build -t mimic . && docker run --restart=no --rm=true -p 8900:8900 mimic
```

This will expose Mimic on port 8900, so you can access it directly from the host. The default port exposure is intended for communication between containers; see the Docker documentation for more information. If you're using `boot2docker`, run `boot2docker ip` to find the right IP.
