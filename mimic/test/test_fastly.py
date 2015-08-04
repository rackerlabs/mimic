from twisted.trial.unittest import SynchronousTestCase
from twisted.internet.task import Clock

from mimic.canned_responses import fastly
from mimic.core import MimicCore
from mimic.resource import MimicRoot
from mimic.test.helpers import json_request


class FastlyAPITests(SynchronousTestCase):

    """
    Tests for the Fastly api
    """

    def setUp(self):
        """
        Create a :obj:`MimicCore` with :obj:`FastlyApi` as the only plugin,
        and create a service
        """
        self.core = MimicCore(Clock(), [])
        self.root = MimicRoot(self.core).app.resource()
        self.uri = '/fastly'
        self.fastly_response = fastly.FastlyResponse()

        self.customer_id = 42
        self.service_name = 'yumyum'

        (self.response, self.service_json) = self.successResultOf(json_request(
            self, self.root, "POST",
            self.uri + '/service?customer_id={0}&name={1}'.format(
                self.customer_id, self.service_name)))

        self.service_id = self.service_json['versions'][0]['service_id']
        self.version_id = self.service_json['versions'][0]['number']

    def test_get_customer(self):
        """
        ``GET /current_customer`` against the fastly API mock returns
        JSON-serialized customer details.
        """
        (response, customer_json) = self.successResultOf(json_request(
            self, self.root, "GET", self.uri + '/current_customer'))
        customer_details = self.fastly_response.get_current_customer()

        self.assertEqual(200, response.code)
        self.assertEqual(sorted(customer_json), sorted(customer_details))

    def test_create_service(self):
        """
        ``POST /service`` against the fastly API mock stores the created
        service and returns JSON-serialized service details.
        """
        service_details = self.fastly_response.create_service(
            [('customer_id', [self.customer_id]),
             ('name', [self.service_name])])

        self.assertEqual(200, self.response.code)
        self.assertEqual(sorted(self.service_json), sorted(service_details))

        (response, json_by_service_name) = self.successResultOf(json_request(
            self, self.root, "GET",
            self.uri + '/service/search?name={0}'.format(self.service_name)))
        self.assertEqual(200, self.response.code)

        (response, json_by_service_id) = self.successResultOf(json_request(
            self, self.root, "GET",
            self.uri + '/service/{0}/details'.format(self.service_id)))
        self.assertEqual(200, self.response.code)
        self.assertEqual(sorted(json_by_service_name['service_details']),
                         sorted(json_by_service_id['versions'][0]))

    def test_create_version(self):
        """
        ``POST /service/{service_id}/version)`` creates a new version of the
        service and returns JSON-serialized service details for the specific
        version.
        """
        (response, version_json) = self.successResultOf(json_request(
            self, self.root, "POST",
            self.uri + '/service/<{0}/version'.format(self.service_id)))

        version_details = self.fastly_response.create_version(
            service_id=self.service_id)

        self.assertEqual(200, self.response.code)
        self.assertEqual(sorted(version_json), sorted(version_details))

    def test_get_service_by_name(self):
        """
        ``GET /service/search`` against the Fastly mock searches by service name
        and returns JSON-serialized service details.
        """
        (response, json_body) = self.successResultOf(json_request(
            self, self.root, "GET",
            self.uri + '/service/search?name={0}'.format(self.service_name)))
        service_details = self.fastly_response.get_service_by_name(
            service_name=self.service_name)

        self.assertEqual(200, response.code)
        self.assertEqual(sorted(json_body), sorted(service_details))

    def test_create_domain(self):
        """
        ``POST/service/{service_id}/version/{version_id}/domain`` against Fastly
        mock associates a domain to the specific version of the Fastly service
        and returns JSON-serialized service details.
        """
        uri = self.uri + '/service/{0}/version/{1}/domain' \
            '?name=llamallama&comment=redpajama'.format(
                self.service_id, self.version_id)

        (response, json_body) = self.successResultOf(json_request(
            self, self.root, "POST", uri))
        domain_details = self.fastly_response.create_domain(
            url_data=[('comment', ['comment']),
                      ('name', [self.service_name])],
            service_id=self.service_id,
            service_version=self.version_id)

        self.assertEqual(200, response.code)
        self.assertEqual(sorted(json_body), sorted(domain_details))

    def test_check_domains(self):
        """
        ``GET/service/{service_id}/version/{version_id}/domain/check_all`` against
        Fastly mock returns an array with the status of all domain DNS records
        for a service version.
        """
        uri = self.uri + '/service/{0}/version/{1}/domain' \
            '?name=llamallama&comment=redpajama'.format(
                self.service_id, self.version_id)

        (response, json_body) = self.successResultOf(json_request(
            self, self.root, "POST", uri))

        uri = self.uri + '/service/{0}/version/{1}/domain/check_all' \
            '?name=llamallama&comment=redpajama'.format(
                self.service_id, self.version_id)

        (response, json_body) = self.successResultOf(json_request(
            self, self.root, "GET", uri))
        domain_details = self.fastly_response.check_domains(
            service_id=self.service_id,
            service_version=self.version_id)

        self.assertEqual(200, response.code)
        self.assertEqual(sorted(json_body), sorted(domain_details))

    def test_create_backend(self):
        """
        ``POST /service/{service_id}/version/{version_id}/backend`` against
        Fastly mock creates a backend(origin) for a particular service and
        version and returns JSON-serialized response.
        """
        uri = self.uri + '/service/{0}/version/{1}/backend' \
            '?name=winniepoo&address=honeytree&use_ssl=False&port=80'.format(
                self.service_id, self.version_id)

        (response, json_body) = self.successResultOf(json_request(
            self, self.root, "POST", uri))

        url_data = [('name', ['winniepoo']), ('address', ['honeytree']),
                    ('use_ssl', [False]), ('port', [80])]
        domain_details = self.fastly_response.create_backend(
            url_data=url_data,
            service_id=self.service_id,
            service_version=self.version_id)

        self.assertEqual(200, response.code)
        self.assertEqual(sorted(json_body), sorted(domain_details))

    def test_create_condition(self):
        """
        ``POST /service/{service_id}/version/{version_id}/condition`` against
        Fastly mock creates a condition (rule) for a particular service and
        version and returns JSON-serialized response.
        """
        uri = self.uri + '/service/{0}/version/{1}/condition' \
            '?name=testcondition&statement=req.url~+"index.html"&priority=10'.format(
                self.service_id, self.version_id)

        (response, json_body) = self.successResultOf(json_request(
            self, self.root, "POST", uri))

        url_data = [
            ('name', ['testcondition']),
            ('statement', ['req.url~+"index.html"']),
            ('priority', [10])
        ]
        condition = self.fastly_response.create_condition(
            url_data=url_data,
            service_id=self.service_id,
            service_version=self.version_id)

        self.assertEqual(200, response.code)
        self.assertEqual(sorted(json_body), sorted(condition))

    def test_create_cache_settings(self):
        """
        ``POST /service/{service_id}/version/{version_id}/cache_settings`` against
        Fastly mock creates a caching setting (rule) for a particular service and
        version and returns JSON-serialized response.
        """
        uri = self.uri + '/service/{0}/version/{1}/cache_settings' \
            '?name=testcache&stale_ttl=1000&ttl=1000&action=cache'.format(
                self.service_id, self.version_id)

        (response, json_body) = self.successResultOf(json_request(
            self, self.root, "POST", uri))

        url_data = [
            ('name', ['testcache']),
            ('stale_ttl', ['1000']),
            ('ttl', ['1000']),
            ('action', ['cache'])
        ]
        cache_settings = self.fastly_response.create_cache_settings(
            url_data=url_data,
            service_id=self.service_id,
            service_version=self.version_id)

        self.assertEqual(200, response.code)
        self.assertEqual(sorted(json_body), sorted(cache_settings))

    def test_create_response_object(self):
        """
        ``POST /service/{service_id}/version/{version_id}/response_object`` against
        Fastly mock creates a response_object for a particular service and
        version and returns JSON-serialized response.
        """
        uri = self.uri + '/service/{0}/version/{1}/response_object' \
            '?status=200&response=Ok&name=testresponse&content=this+message+means+all+is+okay'.format(
                self.service_id, self.version_id)

        (response, json_body) = self.successResultOf(json_request(
            self, self.root, "POST", uri))

        url_data = [
            ('status', ['200']),
            ('response', ['Ok']),
            ('cache_condition', [""]),
            ('request_condition', [""]),
            ('name', ['testresponse']),
            ('content', ['this+message+means+all+is+okay']),
            ('content_type', ["text/plain"]),
            ('service_id', [self.service_id])
        ]

        response_object = self.fastly_response.create_response_object(
            url_data=url_data,
            service_id=self.service_id,
            service_version=self.version_id)

        self.assertEqual(200, response.code)
        self.assertEqual(sorted(json_body), sorted(response_object))

    def test_create_settings(self):
        """
        ``POST /service/{service_id}/version/{version_id}/settings`` against
        Fastly mock creates a settings object for a particular service and
        version and returns JSON-serialized response.
        """
        uri = self.uri + '/service/{0}/version/{1}/settings' \
            '?general.default_ttl=4242&general.default_host=www.mydomain.com'.format(
                self.service_id, self.version_id)

        (response, json_body) = self.successResultOf(json_request(
            self, self.root, "PUT", uri))

        url_data = [
            ('general.default_ttl', ['4242']),
            ('general.default_host', ['www.mydomain.com'])
        ]
        settings = self.fastly_response.create_settings(
            url_data=url_data,
            service_id=self.service_id,
            service_version=self.version_id)

        self.assertEqual(200, response.code)
        self.assertEqual(sorted(json_body), sorted(settings))

    def test_list_versions(self):
        """
        ``GET /service/{service_id}/version)`` against Fastly mock returns all
        versions associated with the service and returns a JSON-serialized
        response.
        """
        (response, version_json) = self.successResultOf(json_request(
            self, self.root, "GET",
            self.uri + '/service/{0}/version'.format(self.service_id)))

        version_details = self.fastly_response.list_versions(
            service_id=self.service_id)
        self.assertEqual(200, response.code)
        self.assertEqual(sorted(version_json), sorted(version_details))

    def test_activate_version(self):
        """
        ``PUT /service/{service_id}/version/{version_number}/activate)`` against
        Fastly mock activates the specified version of the service and returns
        a JSON-serialized response.
        """
        (response, version_json) = self.successResultOf(json_request(
            self, self.root, "PUT",
            self.uri + '/service/{0}/version/{1}/activate'.format
                       (self.service_id, self.version_id)))

        version_details = self.fastly_response.activate_version(
            service_id=self.service_id, version_number=self.version_id)
        self.assertEqual(200, response.code)
        self.assertEqual(sorted(version_json), sorted(version_details))

    def test_deactivate_version(self):
        """
        ``PUT /service/{service_id}/version/{version_number}/deactivate)``
        against Fastly mock deactivates the specified version of the service
        and returns a JSON-serialized response.
        """
        (response, version_json) = self.successResultOf(json_request(
            self, self.root, "PUT",
            self.uri + '/service/{0}/version/{1}/deactivate'.format
                       (self.service_id, self.version_id)))

        version_details = self.fastly_response.deactivate_version(
            service_id=self.service_id, version_number=self.version_id)
        self.assertEqual(200, response.code)
        self.assertEqual(sorted(version_json), sorted(version_details))

    def test_get_service_details(self):
        """
        ``GET /service/{service_id}/details`` against Fastly mock list detailed
        information on a specified service and returns a JSON-serialized
        response.
        """
        (response, service_json) = self.successResultOf(json_request(
            self, self.root, "GET",
            self.uri + '/service/{0}/details'.format(self.service_id)))

        service_details = self.fastly_response.get_service_details(
            service_id=self.service_id)
        self.assertEqual(200, response.code)
        self.assertEqual(sorted(service_json), sorted(service_details))

    def test_delete_service(self):
        """
        ``DELETE /service/{service_id}`` against Fastly mock deletes the
        specified service and returns a JSON-serialized response.
        """
        (response, delete_json) = self.successResultOf(json_request(
            self, self.root, "DELETE",
            self.uri + '/service/{0}'.format(self.service_id)))

        self.assertEqual(200, response.code)
        self.assertEqual(delete_json, {'status': 'ok'})

    def test_health(self):
        """
        ``GET /`` against Fastly mock checks if the server is up/down
        and returns a JSON-serialized response.
        """
        (response, delete_json) = self.successResultOf(json_request(
            self, self.root, "GET", self.uri))

        self.assertEqual(200, response.code)
        self.assertEqual(delete_json, {'status': 'ok'})
