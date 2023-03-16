"""
Canned response for fastly
"""



import random
import string
import uuid


class FastlyResponse(object):
    """
    Canned response for fastly.
    See docs here https://docs.fastly.com/api/config
    """

    fastly_cache = {}

    def get_current_customer(self):
        """
        Returns the current customer with response code 200.

        :return: a JSON-serializable dictionary matching the format of the JSON
                 response for fastly_client.get_current_customer()
                 ("/current_customer") request.
        """
        def _random_string():
            random_string = ''.join(random.choice(
                string.ascii_uppercase + string.ascii_uppercase)
                for _ in range(20))
            return random_string

        id = _random_string()
        owner_id = _random_string()

        current_customer = {
            'can_edit_matches': '0',
            'can_read_public_ip_list': '0',
            'can_upload_vcl': '1',
            'updated_at': '2014-11-03T23:37:44+00:00',
            'has_config_panel': '1',
            'has_improved_ssl_config': False,
            'id': id,
            'has_historical_stats': '1',
            'has_openstack_logging': '0',
            'can_configure_wordpress': '0',
            'has_improved_logging': '1',
            'readonly': '',
            'ip_whitelist': '0.0.0.0/0',
            'owner_id': owner_id,
            'phone_number': '770-123-1749',
            'postal_address': None,
            'billing_ref': None,
            'can_reset_passwords': True,
            'has_improved_security': '1',
            'stripe_account': None,
            'name': 'Poppy - Test',
            'created_at': '2014-11-03T23:37:43+00:00',
            'can_stream_syslog': '1',
            'pricing_plan': 'developer',
            'billing_contact_id': None,
            'has_streaming': '1'}
        return current_customer

    def create_service(self, url_data):
        """
        Returns POST service with response json.

        :return: a JSON-serializable dictionary matching the format of the JSON
                 response for fastly_client.create_service()
                 ("/service") request.
        """
        data = {key: value[0] for key, value in url_data}

        publish_key = uuid.uuid4().hex
        service_id = uuid.uuid4().hex
        service_name = data['name']

        self.fastly_cache[service_name] = {
            'service_details': {
                'comment': '',
                'locked': False,
                'updated_at': '2014-11-13T14:29:10+00:00',
                'created_at': '2014-11-13T14:29:10+00:00',
                'testing': None,
                'number': 1,
                'staging': None,
                'active': None,
                'service_id': service_id,
                'deleted_at': None,
                'inherit_service_id': None,
                'deployed': None},
            'service_name': service_name
        }
        self.fastly_cache[service_id] = self.fastly_cache[service_name]

        create_service = {
            'comment': '',
            'publish_key': publish_key,
            'name': service_name,
            'versions': [{'comment': '', 'locked': '0',
                           'service': service_id,
                           'updated_at': '2014-11-12T18:43:21',
                           'created_at': '2014-11-12T18:43:21',
                           'testing': None, 'number': '1',
                           'staging': None,
                           'active': None,
                           'service_id': service_id,
                           'deleted_at': None,
                           'inherit_service_id': None,
                           'deployed': None,
                           'backend': 0}],
            'created_at': '2014-11-12T18:43:21+00:00',
            'updated_at': '2014-11-12T18:43:21+00:00',
            'customer_id': data['customer_id'],
            'id': service_id}
        return create_service

    def get_service_by_name(self, service_name):
        """Returns the details of the CDN service.

        :return: a JSON-serializable dictionary matching the format of the JSON
                 response for fastly_client.get_service_by_name()
                 ("/service/version") request.
        """
        return self.fastly_cache[service_name]

    def create_version(self, service_id):
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

    def create_domain(self, url_data, service_id, service_version):
        """
        Returns POST create_domain with response json.

        :return: a JSON-serializable dictionary matching the format of the JSON
                 response for fastly_client.create_domain()
                 ("/service/<service_id>/version/<service_version>/domain")
                 request.
        """
        request_dict = {k: v[0] for k, v in url_data}
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

    def check_domains(self, service_id, service_version):
        """
        Returns GET check_domains with response json.

        :return: a JSON-serializable dictionary matching the format of the JSON
                 response for fastly_client.check_domain()
                 ("/service/%s/version/%d/domain/check_all")
                 request.
        """
        domain_list = self.fastly_cache[service_id]['domain_list']

        return domain_list

    def create_backend(self, url_data, service_id, service_version):
        """
        Returns create_backend response json.

        :return: a JSON-serializable dictionary matching the format of the JSON
                 response for fastly_client.create_backend()
                 ("/service/<service_id>/version/<service_version>/backend")
                 request.
        """
        request_dict = {k: v[0] for k, v in url_data}

        create_backend = {
            'comment': '',
            'shield': None,
            'weight': 100,
            'ssl_client_key': None,
            'first_byte_timeout': 15000,
            'auto_loadbalance': False,
            'use_ssl': request_dict['use_ssl'],
            'port': request_dict['port'],
            'ssl_hostname': None,
            'hostname': request_dict['name'],
            'error_threshold': 0,
            'max_conn': 20,
            'version': service_version,
            'ipv4': None,
            'ipv6': None,
            'client_cert': None,
            'ssl_ca_cert': None,
            'request_condition': '',
            'healthcheck': None,
            'address': request_dict['address'],
            'ssl_client_cert': None,
            'name': request_dict['name'],
            'connect_timeout': 1000,
            'between_bytes_timeout': 10000,
            'service_id': service_id}

        if 'origin_list' not in self.fastly_cache[service_id]:
            self.fastly_cache[service_id]['origin_list'] = []

        self.fastly_cache[service_id]['origin_list'].append(create_backend)
        return create_backend

    def create_condition(self, url_data, service_id, service_version):
        """
        Returns create_condition response json.

        :return: a JSON-serializable dictionary matching the format of the JSON
                 response for fastly_client.create_condition()
                 ("/service/<service_id>/version/<service_version>/condition")
                 request.
        """
        request_dict = {k: v[0] for k, v in url_data}

        create_condition = {
            "type": "REQUEST",
            "comment": "",
            "name": "condition",
            "version": service_version,
            "service_id": service_id,
            "statement": request_dict['statement'],
            "priority": request_dict['priority']
        }

        if 'condition_list' not in self.fastly_cache[service_id]:
            self.fastly_cache[service_id]['condition_list'] = []

        self.fastly_cache[service_id][
            'condition_list'].append(create_condition)
        return create_condition

    def create_cache_settings(self, url_data, service_id, service_version):
        """
        Returns create_cache_settings response json.

        :return: a JSON-serializable dictionary matching the format of the JSON
                 response for fastly_client.create_cache_settings()
                 ("/service/<service_id>/version/<service_version>/cache_settings")
                 request.
        """
        request_dict = {k: v[0] for k, v in url_data}

        create_cache_settings = {
            "stale_ttl": request_dict.get("stale_ttl", 0),
            "ttl": request_dict.get("ttl", 0),
            "action": request_dict.get("action", ""),
            "cache_condition": "",
            "name": "cache_setting",
            "version": service_version,
            "service_id": service_id
        }

        if 'cache_settings_list' not in self.fastly_cache[service_id]:
            self.fastly_cache[service_id]['cache_settings_list'] = []

        self.fastly_cache[service_id][
            'cache_settings_list'].append(create_cache_settings)
        return create_cache_settings

    def create_response_object(self, url_data, service_id, service_version):
        """
        Returns response_object response json.

        :return: a JSON-serializable dictionary matching the format of the JSON
                 response for fastly_client.create_response_object()
                 ("/service/<service_id>/version/<service_version>/response_object)
                 request.
        """
        request_dict = {k: v[0] for k, v in url_data}

        create_response_object = {
            "status": request_dict["status"],
            "response": request_dict["response"],
            "cache_condition": request_dict.get("cache_condition", ""),
            "request_condition": request_dict.get("request_condition", ""),
            "name": request_dict["name"],
            "version": service_version,
            "content": request_dict["content"],
            "content_type": "text/plain",
            "service_id": service_id
        }

        if 'response_object_list' not in self.fastly_cache[service_id]:
            self.fastly_cache[service_id]['response_object_list'] = []

        self.fastly_cache[service_id][
            'response_object_list'].append(create_response_object)
        return create_response_object

    def create_settings(self, url_data, service_id, service_version):
        """
        Returns settings response json.

        :return: a JSON-serializable dictionary matching the format of the JSON
                 response for fastly_client.create_settings()
                 ("/service/<service_id>/version/<service_version>/settings)
                 request.
        """
        request_dict = {k: v[0] for k, v in url_data}

        create_settings = {
            "service_id": service_id,
            "version": service_version,
            "general.default_ttl": request_dict.get("general.default_ttl", 0),
            "general.default_host": request_dict.get("general.default_host", "")
        }

        if 'settings_list' not in self.fastly_cache[service_id]:
            self.fastly_cache[service_id]['settings_list'] = []

        self.fastly_cache[service_id][
            'settings_list'].append(create_settings)
        return create_settings

    def list_versions(self, service_id):
        """
        Returns GET list_versions with response json.

        :return: a JSON-serializable dictionary matching the format of the JSON
                 response for fastly_client.list_versions()
                 ("/service/%s/version") request.
        """
        return [self.fastly_cache[service_id]['service_details']]

    def activate_version(self, service_id, version_number):
        """
        Returns activate_version response json.

        :return: a JSON-serializable dictionary matching the format of the JSON
                 response for fastly_client.activate_version()
                 ("/service/%s/version/%d/activate") request.
        """
        self.fastly_cache[service_id]['service_details']['active'] = True
        return self.fastly_cache[service_id]['service_details']

    def deactivate_version(self, service_id, version_number):
        """
        Returns deactivate_version response json.

        :return: a JSON-serializable dictionary matching the format of the JSON
                 response for fastly_client.deactivate_version()
                 ("/service/%s/version/%d/deactivate") request.
        """
        self.fastly_cache[service_id]['service_details']['active'] = False
        return self.fastly_cache[service_id]['service_details']

    def get_service_details(self, service_id):
        """
        Returns get_service_details response json.
        :return: a JSON-serializable dictionary matching the format of the JSON
                 response for fastly_client.get_service_details()
                 ("/service/%s/details") request.
        """
        version_details = self.fastly_cache[service_id]['service_details']
        service_details = {
            'id': service_id,
            'name': self.fastly_cache[service_id]['service_name'],
            'customer_id': "hTE5dRlSBICGPJxJwCH4M",
            'comment': "",
            "updated_at": "2012-06-14T21:20:19+00:00",
            "created_at": "2012-06-14T21:20:19+00:00",
            "publish_key": "xgdbdd93h5066f8d330c276fDe00f9d293abfex7",
            'versions': [version_details]}

        return service_details

    def delete_service(self, service_id):
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

    def get_health(self):
        """
        Returns 200 with response json.

        """
        return {'status': 'ok'}
