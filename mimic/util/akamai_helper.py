"""Akamai Helper Methods."""


def policy_not_found(customer_id, policy_name):
    """Policy Not Found Response
    :param customer_id: A required string parameter
    :param policy_name: A required string parameter
    :returns: This method returns dictionary for a mimic akamai error response
    """
    discription = (("Policy not found for this property {0}"
                   + " and sub-property {1}. Please verify"
                   + " the property id/sub-property-id.")
                   .format(customer_id, policy_name))

    resp = {
        'errorCode': 404,
        'message': 'Policy not found',
        'errorInstanceId': 'de2f1a4f5f',
        'description': discription,
        'helpLink': 'https://developer.akamai.com/api/delivery-policies/errors.html#404'
    }

    return resp


def missing_either_matches_behaviors(rule, field):
    """ Missing Matches or Behaviors field reponse
    :param rule: A required int parameter
    :param field: A required string parameter
    :returns: This method returns dictionary for a mimic akamai error response
    """
    resp = {
        'field': ['rules', rule, field],
        'message': "'{0}' is a required property".format(field),
        'code': 4010
    }

    return resp


def malformed_json_input():
    """Malformed Json input response
    :returns: This method returns dictionary for a mimic akamai error response
    """
    resp = {
        'description': 'Input Policy Json has a syntax error',
        'errorCode': 4000,
        'errorInstanceId': '5a64d2906d',
        'error': 'Expecting object: line 1 column 1 (char 0)',
        'message': 'Malformed Json input',
        'helpLink': u'https://developer.akamai.com/api/delivery-policies/errors.html#4000'
    }

    return resp


def missing_field(rule, bm_field, field_index, field):
    """Missing the name or value field from either match or behavior rule response
    :param rule: A required int parameter
    :param bm_field: A required string parameter
    :param field_index: A required int parameter
    :param field: A required string parameter
    :returns: This method returns dictionary for a mimic akamai error response
    """
    resp = {
        'field': ['rules', rule, '{0}'.format(bm_field), field_index, field],
        'message': "'{0}' is a required property".format(field),
        'code': 4010
    }

    return resp


def name_not_string(rule, field, subfld_index, value):
    """Value of the name field is not a string response
    :param rule: A required int parameter
    :param field: A required string parameter
    :param subfld_index: A required int parameter
    :param value: A required string parameter
    :returns: This method returns dictionary for a mimic akamai error response
    """
    if field == "behaviors":
        if type(value) is unicode:
            message = (("'{0}' is not one of ['referer-whitelist', "
                        + "'referer-blacklist', 'ip-whitelist', 'ip-blacklist', "
                        + "'geo-whitelist', 'geo-blacklist', 'content-refresh', "
                        + "'cachekey-query-args', 'modify-outgoing-request-path', "
                        + "'caching', 'origin']").format(value))
        else:
            message = (("{0} is not one of ['referer-whitelist', "
                        + "'referer-blacklist', 'ip-whitelist', 'ip-blacklist', "
                        + "'geo-whitelist', 'geo-blacklist', 'content-refresh', "
                        + "'cachekey-query-args', 'modify-outgoing-request-path', "
                        + "'caching', 'origin']").format(value))
    elif field == "matches":
        if type(value) is unicode:
            message = (("'{0}' is not one of ['host-name', "
                        + "'http-method', 'url-scheme', 'url-path', "
                        + "'url-extension', 'url-filename', "
                        + "'header', 'url-wildcard']").format(value))
        else:
            message = (("{0} is not one of ['host-name', "
                        + "'http-method', 'url-scheme', 'url-path', "
                        + "'url-extension', 'url-filename', "
                        + "'header', 'url-wildcard']").format(value))

    resp1 = {
        'field': ['rules', rule, field, subfld_index, 'name'],
        'message': message,
        'code': 4010
    }
    resp2 = {
        'field': ['rules', rule, field, subfld_index, 'name'],
        'message': "{0} is not of type 'string'".format(value),
        'code': 4010
    }

    return resp1, resp2


def value_not_string(rule, field, subfld_index, value):
    """Value of the value filed is not a string response
    :param rule: A required int parameter
    :param field: A required string parameter
    :param subfld_index: A required int parameter
    :param value: A required string parameter
    :returns: This method returns dictionary for a mimic akamai error response
    """
    resp = {
        'field': ['rules', rule, field, subfld_index, 'value'],
        'message': "{0} is not of type 'string'".format(value),
        'code': 4010
    }

    return resp

def type_not_valid(value):
    """Value of the type field is not valid
    :param value: A required string parameter
    :returns: This method returns dictionary for a mimic akamai error response
    """
    resp = {
        'errorCode': 4000,	
        'message': 'BadRequest',
        'errorInstanceId': u'cd472d0e12',
        'helpLink': u'https: //developer.akamai.com/api/delivery-policies/errors.html#4000',
        'error': ("Invalid behavior_type '{0}' for behavior 'caching'. Allowed behavior types : ['no-store', "
                  + "'bypass-cache', 'fixed', 'honor', 'honor-cc', 'honor-expires']")
                 .format(value)
    }

    return resp
