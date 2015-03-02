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
        Test to verify : ``GET /current_customer``
        """
        (response, customer_json) = self.successResultOf(json_request(
            self, self.root, "GET", self.uri + '/current_customer'))
        customer_details = self.fastly_response.get_current_customer()

        self.assertEqual(200, response.code)
        self.assertEqual(sorted(customer_json), sorted(customer_details))

    def test_create_service(self):
        """
        Test to verify : ``POST /service``
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
        Test to verify : ``POST /service/{service_id}/version)``
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
        Test to verify : ``GET /service/search``
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
        Test to verify : ``POST
                           /service/{service_id}/version/{version_id}/domain``
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
        Test to verify : ``GET
            /service/{service_id}/version/{version_id}/domain/check_all'
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
        Test to verify : ``POST
            /service/{service_id}/version/{version_id}/backend'
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

    def test_list_versions(self):
        """
        Test to verify : ``GET /service/{service_id}/version)``
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
        Test to verify : ``PUT /service/{service_id}/version/
                           {version_number}/activate)``
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
        Test to verify : ``PUT /service/{service_id}/version/
                           {version_number}/deactivate)``
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
        Test to verify : ``GET /service/{service_id}/details``
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
        Test to verify : ``DELETE /service/{service_id}``
        """
        (response, delete_json) = self.successResultOf(json_request(
            self, self.root, "DELETE",
            self.uri + '/service/{0}'.format(self.service_id)))

        self.assertEqual(200, response.code)
        self.assertEqual(delete_json, {'status': 'ok'})

    def test_health(self):
        """
        Test to verify : ``GET /``
        """
        (response, delete_json) = self.successResultOf(json_request(
            self, self.root, "GET", self.uri))

        self.assertEqual(200, response.code)
        self.assertEqual(delete_json, {'status': 'ok'})
