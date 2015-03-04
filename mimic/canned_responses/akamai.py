"""
Canned response for Akamai
"""
import json
import random
import string
import uuid

from mimic.util.akamai_helper import (policy_not_found,
                                      missing_either_matches_behaviors,
                                      malformed_json_input,
                                      missing_field,
                                      name_not_string,
                                      value_not_string,
                                      type_not_valid)


class AkamaiResponse(object):

    """Akamai API Responses."""

    akamai_cache = {}

    def create_policy(self, request_body, customer_id, policy_name):
        """
        Returns PUT policy with response json.

        :return: a JSON-serializable dictionary matching the format of the JSON
                 response for
                 ("/partner-api/v1/network/production/properties/customer_id/'
                  'sub-properties/policy_name/policy'") request.
        """
        # Method Constants
        dict_error = {'description': "Input Json Validation Errors. refer to 'errors' "
                                     "field.",
                      'errorCode': 4000,
                      'errorInstanceId': u'be70a55917',
                      'error': [],
                      'message': 'Invalid Json input',
                      'helpLink': 'https://developer.akamai.com/api/delivery-policies/'
                                  'errors.html#4000'}
        bln_errors = False
        responses = []
        matches = []
        behaviors = []
        valid_match_names = ['host-name', 'http-method', 'url-scheme', 'url-path', 'url-extension',
                             'url-filename', 'header', 'url-wildcard']
        valid_behavior_names = ['referer-whitelist', 'referer-blacklist', 'ip-whitelist',
                                'ip-blacklist', 'geo-whitelist', 'geo-blacklist', 'content-refresh',
                                'cachekey-query-args', 'modify-outgoing-request-path', 'caching',
                                'origin']
        valid_behavior_cache_types = ['no-store', 'bypass-cache', 'fixed', 'honor', 'honor-cc',
                                      'honor-expires']

        try:
            req = json.loads(request_body)
        except:
            response = malformed_json_input()
            return response, 400

        if (len(req['rules']) > 0):
            for rule in req['rules']:
                rule_index = req['rules'].index(rule)
                bln_rule_errors = False
                if (not('matches' in rule)) and \
                   (not('behaviors' in rule)):
                    response = missing_either_matches_behaviors(rule_index, 'matches')
                    responses.append(response)
                    response = missing_either_matches_behaviors(rule_index, 'behaviors')
                    responses.append(response)
                    bln_errors = True
                    bln_rule_errors = True
                    continue

                if not('matches' in rule):
                    response = missing_either_matches_behaviors(rule_index, 'matches')
                    responses.append(response)
                    bln_errors = True
                    bln_rule_errors = True

                if not('behaviors' in rule):
                    response = missing_either_matches_behaviors(rule_index, 'behaviors')
                    responses.append(response)
                    bln_errors = True
                    bln_rule_errors = True

                if (len(rule['matches']) > 0):
                    for match in rule['matches']:
                        match_index = req['rules'][rule_index]['matches'].index(match)
                        bln_match_error = False
                        if (not('name' in match)) and \
                           (not('value' in match)):
                            response = missing_field(rule_index, 'matches', match_index, 'name')
                            responses.append(response)
                            response = missing_field(rule_index, 'matches', match_index, 'value')
                            responses.append(response)
                            bln_errors = True
                            bln_match_error = True
                            bln_rule_errors = True
                            continue

                        if not('name' in match):
                            response = missing_field(rule_index, 'matches', match_index, 'name')
                            responses.append(response)
                            bln_errors = True
                            bln_match_error = True
                            bln_rule_errors = True

                        if not('value' in match):
                            response = missing_field(rule_index, 'matches', match_index, 'value')
                            responses.append(response)
                            bln_errors = True
                            bln_match_error = True
                            bln_rule_errors = True

                        if ('name' in match) and ((not(match['name'] == 0)) and (not(match['name']))):
                            resp1, resp2 = name_not_string(rule_index, 'matches', match_index, 'None')
                            responses.append(resp1)
                            responses.append(resp2)
                            bln_errors = True
                            bln_match_error = True
                            bln_rule_errors = True
                        elif ('name' in match) and (not(type(match['name']) is unicode)):
                            resp1, resp2 = name_not_string(rule_index, 'matches', match_index,
                                                           match['name'])
                            responses.append(resp1)
                            responses.append(resp2)
                            bln_errors = True
                            bln_match_error = True
                            bln_rule_errors = True
                        elif ('name' in match) and (not(match['name'] in valid_match_names)):
                            resp1, resp2 = name_not_string(rule_index, 'matches', match_index,
                                                           match['name'])
                            responses.append(resp1)
                            bln_errors = True
                            bln_match_error = True
                            bln_rule_errors = True

                        if ('value' in match) and ((not(match['value'] == 0)) and (not(match['value']))):
                            response = value_not_string(rule_index, 'matches', match_index, 'None')
                            responses.append(response)
                            bln_errors = True
                            bln_match_error = True
                            bln_rule_errors = True
                        elif ('value' in match) and (not(type(match['value']) is unicode)):
                            response = value_not_string(rule_index, 'matches', match_index,
                                                        match['value'])
                            responses.append(response)
                            bln_errors = True
                            bln_match_error = True
                            bln_rule_errors = True

                        if not(bln_match_error):
                            matches.append(match)

                if len(rule['behaviors']) > 0:
                    for behavior in rule['behaviors']:
                        behavior_index = req['rules'][rule_index]['behaviors'].index(behavior)
                        bln_behavior_error = False
                        if (not('name' in behavior)) and \
                           (not('value' in behavior)):
                            response = missing_field(rule_index, 'behaviors', behavior_index, 'name')
                            responses.append(response)
                            response = missing_field(rule_index, 'behaviors', behavior_index, 'value')
                            responses.append(response)
                            bln_errors = True
                            bln_behavior_error = True
                            bln_rule_errors = True
                            continue

                        if not('name' in behavior):
                            response = missing_field(rule_index, 'behaviors', behavior_index, 'name')
                            responses.append(response)
                            bln_errors = True
                            bln_behavior_error = True
                            bln_rule_errors = True

                        if ('name' in behavior) and\
                           ((not(behavior['name'] == 0)) and (not(behavior['name']))):
                            resp1, resp2 = name_not_string(rule_index, 'behaviors',
                                                           behavior_index, 'None')
                            responses.append(resp1)
                            responses.append(resp2)
                            bln_errors = True
                            bln_behavior_error = True
                            bln_rule_errors = True
                        elif ('name' in behavior) and (not(type(behavior['name']) is unicode)):
                            resp1, resp2 = name_not_string(rule_index, 'behaviors', behavior_index,
                                                           behavior['name'])
                            responses.append(resp1)
                            responses.append(resp2)
                            bln_errors = True
                            bln_behavior_error = True
                            bln_rule_errors = True
                        elif ('name' in behavior) and (not(behavior['name'] in valid_behavior_names)):
                            resp1, resp2 = name_not_string(rule_index, 'behaviors', behavior_index,
                                                           behavior['name'])
                            responses.append(resp1)
                            bln_errors = True
                            bln_behavior_error = True
                            bln_rule_errors = True

                        if not('value' in behavior):
                            response = missing_field(rule_index, 'behaviors', behavior_index, 'value')
                            responses.append(response)
                            bln_errors = True
                            bln_behavior_error = True
                            bln_rule_errors = True

                        if ('value' in behavior) and \
                           ((not(behavior['value'] == 0)) and (not(behavior['value']))):
                            response = value_not_string(rule_index, 'behaviors',
                                                        behavior_index, 'None')
                            responses.append(response)
                            bln_errors = True
                            bln_behavior_error = True
                            bln_rule_errors = True
                        elif ('value' in behavior) and (not(type(behavior['value']) is unicode)):
                            response = value_not_string(rule_index, 'behaviors',
                                                        behavior_index, behavior['value'])
                            responses.append(response)
                            bln_errors = True
                            bln_behavior_error = True
                            bln_rule_errors = True

                        if (behavior['name'] == 'caching') and \
                           ('value' in behavior) and \
                           (type(behavior['value']) is unicode) and \
                           (not('type' in behavior)):
                            response = type_not_valid('')
                            responses.append(response)
                            bln_errors = True
                            bln_behavior_error = True
                            bln_rule_errors = True
                        elif (behavior['name'] == 'caching') and \
                             ('value' in behavior) and \
                             (type(behavior['value']) is unicode) and \
                             ('type' in behavior) and \
                             (not(behavior['type'] in valid_behavior_cache_types)):
                            response = type_not_valid(behavior['type'])
                            responses.append(response)
                            bln_errors = True
                            bln_behavior_error = True
                            bln_rule_errors = True

                        if not(bln_behavior_error):
                            behaviors.append(behavior)

                if not(bln_rule_errors):
                    rule['matches'] = matches
                    rule['behaviors'] = behaviors
                    self.akamai_cache[policy_name] = rule
        else:
            self.akamai_cache[policy_name] = req

        if bln_errors:
            dict_error['error'] = responses
            return dict_error, 400
        else:
            return self.akamai_cache[policy_name], 200

    def get_policy(self, customer_id, policy_name):
        """Returns service details json.

        :return: a JSON-serializable dictionary matching the format of the JSON
                 response for Akamai GET policy
                 ("/partner-api/v1/network/production/properties/customer_id/'
                  'sub-properties/policy_name/policy'") request.
        """
        if policy_name in self.akamai_cache:
            return self.akamai_cache[policy_name], 200

        response_body = policy_not_found(customer_id, policy_name)

        return response_body, 404

    def delete_policy(self, customer_id, policy_name):
        """
        Returns DELETE service with response json.

        :return: a JSON-serializable dictionary matching the format of the JSON
                 response for Akamai DELETE policy
                 ("/partner-api/v1/network/production/properties/customer_id/'
                  'sub-properties/policy_name/policy'") request.
        """
        if policy_name in self.akamai_cache:
            del(self.akamai_cache[policy_name])

            description = 'The policy for property_id {0} and ' \
                          'subproperty_id {1} was successfully deleted.' \
                          .format(customer_id, policy_name)

            response_body = {
                "message": "Successfully deleted",
                "description": description}

            response_code = 200

        else:

            response_body = policy_not_found(customer_id, policy_name)

            response_code = 404

        return response_body, response_code

    def purge_content(self):
        """Returns service details json.

        :return: a JSON-serializable dictionary matching the format of the JSON
                 response for Akamai CCU API POST
                 ("/ccu/v2/queues/default") request.
        """
        purgeId = uuid.uuid1()
        supportId = ''.join([random.choice(string.ascii_letters + string.digits)
                             for n in xrange(30)]).upper()
        response_body = {
            "estimatedSeconds": 420,
            "progressUri": "/ccu/v2/purges/%s" % str(purgeId),
            "purgeId": str(purgeId),
            "supportId": supportId,
            "httpStatus": 201,
            "detail": "Request accepted.",
            "pingAfterSeconds": 420
        }

        return response_body
