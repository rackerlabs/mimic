"""
Canned response for fastly
"""
import uuid


class FastlyResponse(object):

    """
    Canned response for fastly.
    See docs here https://docs.fastly.com/api/config
    """

    fastly_cache = {}

    def get_current_customer(self, request):
        """
        Returns the current customer with response code 200.

        :return: a JSON-serializable dictionary matching the format of the JSON
                 response for fastly_client.get_current_customer()
                 ("/current_customer") request.
        """
        current_customer = {
            u'can_edit_matches': u'0',
            u'can_read_public_ip_list': u'0',
            u'can_upload_vcl': u'1',
            u'updated_at': u'2014-11-03T23:37:44+00:00',
            u'has_config_panel': u'1',
            u'has_improved_ssl_config': False,
            u'id': u'3bKRHISECARTtoUMxW6',
            u'has_historical_stats': u'1',
            u'has_openstack_logging': u'0',
            u'can_configure_wordpress': u'0',
            u'has_improved_logging': u'1',
            u'readonly': '',
            u'ip_whitelist': u'0.0.0.0/0',
            u'owner_id': u'asewQWEwdRnLnCKyMztZqkQvy',
            u'phone_number': u'770-123-1749',
            u'postal_address': None,
            u'billing_ref': None,
            u'can_reset_passwords': True,
            u'has_improved_security': u'1',
            u'stripe_account': None,
            u'name': u'Poppy - Test',
            u'created_at': u'2014-11-03T23:37:43+00:00',
            u'can_stream_syslog': u'1',
            u'pricing_plan': u'developer',
            u'billing_contact_id': None,
            u'has_streaming': u'1'}
        return current_customer

    def create_service(self, request, url_data):
        """
        Returns POST service with response json.

        :return: a JSON-serializable dictionary matching the format of the JSON
                 response for fastly_client.create_service()
                 ("/service") request.
        """
        data = dict((key, value[0]) for key, value in url_data)

        publish_key = uuid.uuid4().hex
        service_id = uuid.uuid4().hex
        service_name = data['name']

        self.fastly_cache[service_name] = {
            'service_details': {
                u'comment': '',
                u'locked': False,
                u'updated_at': u'2014-11-13T14:29:10+00:00',
                u'created_at': u'2014-11-13T14:29:10+00:00',
                u'testing': None,
                u'number': 1,
                u'staging': None,
                u'active': None,
                u'service_id': service_id,
                u'deleted_at': None,
                u'inherit_service_id': None,
                u'deployed': None},
            'service_name': service_name
        }
        self.fastly_cache[service_id] = self.fastly_cache[service_name]

        create_service = {
            u'comment': '',
            u'publish_key': publish_key,
            u'name': service_name,
            u'versions': [{u'comment': '', u'locked': u'0',
                           u'service': service_id,
                           u'updated_at': u'2014-11-12T18:43:21',
                           u'created_at': u'2014-11-12T18:43:21',
                           u'testing': None, u'number': u'1',
                           u'staging': None,
                           u'active': None,
                           u'service_id': service_id,
                           u'deleted_at': None,
                           u'inherit_service_id': None,
                           u'deployed': None,
                           u'backend': 0}],
            u'created_at': u'2014-11-12T18:43:21+00:00',
            u'updated_at': u'2014-11-12T18:43:21+00:00',
            u'customer_id': data['customer_id'],
            u'id': service_id}
        return create_service

    def get_service_by_name(self, request, service_name):
        """Returns service details json.

        :return: a JSON-serializable dictionary matching the format of the JSON
                 response for fastly_client.get_service_by_name()
                 ("/service/version") request.
        """
        return self.fastly_cache[service_name]

    def create_version(self, request, service_id):
        """
        Returns POST service with response json.

        :return: a JSON-serializable dictionary matching the format of the JSON
                 response for fastly_client.create_version()
                 ("/service/version") request.
        """
        create_version = {
            'service_id': service_id,
            'number': 1}

        return create_version

    def create_domain(self, request, service_id, service_version):
        """
        Returns POST create_domain with response json.

        :return: a JSON-serializable dictionary matching the format of the JSON
                 response for fastly_client.create_domain()
                 ("/service/<service_id>/version/<service_version>/domain")
                 request.
        """
        url_data = request.args.items()
        request_dict = dict((k, v[0]) for k, v in url_data)
        domain_name = request_dict['name']

        create_domain = {
            'comment': '',
            'service_id': service_id,
            'version': service_version,
            'name': domain_name}

        if 'domain_list' not in self.fastly_cache[service_id]:
            self.fastly_cache[service_id]['domain_list'] = []

        self.fastly_cache[service_id]['domain_list'].append(
            [create_domain, 'None', 'False'])
        return create_domain

    def check_domains(self, request, service_id, service_version):
        """
        Returns GET check_domains with response json.

        :return: a JSON-serializable dictionary matching the format of the JSON
                 response for fastly_client.check_domain()
                 ("/service/%s/version/%d/domain/check_all")
                 request.
        """
        domain_list = self.fastly_cache[service_id]['domain_list']

        return domain_list

    def create_backend(self, request, service_id, service_version):
        """
        Returns create_backend response json.

        :return: a JSON-serializable dictionary matching the format of the JSON
                 response for fastly_client.create_backend()
                 ("/service/<service_id>/version/<service_version>/backend")
                 request.
        """
        url_data = request.args.items()
        request_dict = dict((k, v[0]) for k, v in url_data)

        create_backend = {
            u'comment': '',
            u'shield': None,
            u'weight': request_dict['weight'],
            u'ssl_client_key': None,
            u'first_byte_timeout': request_dict['first_byte_timeout'],
            u'auto_loadbalance': request_dict['auto_loadbalance'],
            u'use_ssl': request_dict['use_ssl'],
            u'port': request_dict['port'],
            u'ssl_hostname': None,
            u'hostname': request_dict['name'],
            u'error_threshold': request_dict['error_threshold'],
            u'max_conn': request_dict['max_conn'],
            u'version': service_version,
            u'ipv4': None,
            u'ipv6': None,
            u'client_cert': None,
            u'ssl_ca_cert': None,
            u'request_condition': '',
            u'healthcheck': None,
            u'address': request_dict['address'],
            u'ssl_client_cert': None,
            u'name': request_dict['name'],
            u'connect_timeout': request_dict['connect_timeout'],
            u'between_bytes_timeout': request_dict['between_bytes_timeout'],
            u'service_id': service_id}

        if 'origin_list' not in self.fastly_cache[service_id]:
            self.fastly_cache[service_id]['origin_list'] = []

        self.fastly_cache[service_id]['origin_list'].append(create_backend)
        return create_backend

    def list_versions(self, request, service_id):
        """
        Returns GET list_versions with response json.

        :return: a JSON-serializable dictionary matching the format of the JSON
                 response for fastly_client.list_versions()
                 ("/service/%s/version") request.
        """
        return [self.fastly_cache[service_id]['service_details']]

    def activate_version(self, request, service_id, version_number):
        """
        Returns activate_version response json.

        :return: a JSON-serializable dictionary matching the format of the JSON
                 response for fastly_client.activate_version()
                 ("/service/%s/version/%d/activate") request.
        """
        self.fastly_cache[service_id]['service_details']['active'] = True
        return self.fastly_cache[service_id]['service_details']

    def deactivate_version(self, request, service_id, version_number):
        """
        Returns deactivate_version response json.

        :return: a JSON-serializable dictionary matching the format of the JSON
                 response for fastly_client.deactivate_version()
                 ("/service/%s/version/%d/deactivate") request.
        """
        self.fastly_cache[service_id]['service_details']['active'] = False
        return self.fastly_cache[service_id]['service_details']

    def get_service_details(self, request, service_id):
        """
        Returns get_service_details response json.
        :return: a JSON-serializable dictionary matching the format of the JSON
                 response for fastly_client.get_service_details()
                 ("/service/%s/details") request.
        """
        version_details = self.fastly_cache[service_id]['service_details']
        service_details = {
            u'comment': '',
            u'name': self.fastly_cache[service_id]['service_name'],
            u'versions': [version_details],
            u'active_version': {u'number': 1}}
        return service_details

    def delete_service(self, request, service_id):
        """
        Returns DELETE service with response json.

        :return: a JSON-serializable dictionary matching the format of the JSON
                 response for fastly_client.delete_service()
                 ("/service/%s") request.
        """
        service_name = self.fastly_cache[service_id]['service_name']
        del(self.fastly_cache[service_id])
        del(self.fastly_cache[service_name])

        return {'status': 'ok'}
