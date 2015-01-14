"""
Canned responses for MAAS alarm examples.
"""


def alarm_examples():
    """
    Canned response for the /alarm_examples call.
    """
    return [{
        "id": "remote.http_body_match_1",
        "label": "Body match - string found",
        "description": "Alarm which returns CRITICAL if the provided string is found in the body",
        "check_type": "remote.http",
        "criteria": "if (metric['body_match'] regex '${string}') {\n  return new AlarmStatus(CRITICAL," +
        " '${string} found, returning CRITICAL.');\n}\n",
        "fields": [{
            "name": "string",
            "description": "String to check for in the body",
            "type": "string"
        }]
    }, {
        "id": "remote.http_body_match_missing_string",
        "label": "Body match - string not found",
        "description": "Alarm which returns CRITICAL if the provided string is not found in the body",
        "check_type": "remote.http",
        "criteria": "if (metric['body_match'] == '') {\n  return new AlarmStatus(CRITICAL, 'HTTP " +
        "response did not contain the correct content.');\n}\n\nreturn new AlarmStatus(OK, 'HTTP " +
        "response contains the correct content');\n",
        "fields": []
    }, {
        "id": "remote.http_connection_time",
        "label": "Connection time",
        "description": "Alarm which returns WARNING or CRITICAL based on the connection time",
        "check_type": "remote.http",
        "criteria": "if (metric['duration'] > ${critical_threshold}) {\n  return new AlarmStatus(" +
        "CRITICAL, 'HTTP request took more than ${critical_threshold} milliseconds.');\n}\n\nif (" +
        "metric['duration'] > ${warning_threshold}) {\n  return new AlarmStatus(WARNING, 'HTTP " +
        "request took more than ${warning_threshold} milliseconds.');\n}\n\nreturn new " +
        "AlarmStatus(OK, 'HTTP connection time is normal');\n",
        "fields": [{
            "name": "warning_threshold",
            "description": "Warning threshold (in milliseconds) for the connection time",
            "type": "integer"
        }, {
            "name": "critical_threshold",
            "description": "Critical threshold (in milliseconds) for the connection time",
            "type": "integer"
        }]
    }, {
        "id": "remote.http_status_code",
        "label": "Status code",
        "description": "Alarm which returns WARNING if the server responses with 4xx status code or " +
        "CRITICAL if it responds with 5xx status code",
        "check_type": "remote.http",
        "criteria": "if (metric['code'] regex '4[0-9][0-9]') {\n  return new AlarmStatus(CRITICAL, " +
        "'HTTP server responding with 4xx status');\n}\n\nif (metric['code'] regex '5[0-9][0-9]') {\n" +
        "return new AlarmStatus(CRITICAL, 'HTTP server responding with 5xx status');\n}\n\nreturn " +
        "new AlarmStatus(OK, 'HTTP server is functioning normally');\n",
        "fields": []
    }, {
        "id": "remote.http_cert_expiration",
        "label": "SSL certificate expiration time",
        "description": "Alarm which returns WARNING or CRITICAL based on the certificate expiration " +
        "date",
        "check_type": "remote.http",
        "criteria": "if (metric['cert_end_in'] < ${critical_threshold}) {\n  return new " +
        "AlarmStatus(CRITICAL, 'Cert expiring in less than ${critical_threshold} seconds.');\n}\n\nif " +
        "(metric['cert_end_in'] < ${warning_threshold}) {\n  return new AlarmStatus(WARNING, 'Cert " +
        "expiring in less than ${warning_threshold} seconds.');\n}\n\nreturn new AlarmStatus(OK, " +
        "'HTTP certificate doesn\\'t expire soon.');\n",
        "fields": [{
            "name": "warning_threshold",
            "description": "Warning threshold (in seconds) for the certificate expiration",
            "type": "integer"
        }, {
            "name": "critical_threshold",
            "description": "Critical threshold (in seconds) for the certificate expiration",
            "type": "integer"
        }]
    }, {
        "id": "remote.dns_address_match",
        "label": "DNS record address match",
        "description": "Alarm which returns CRITICAL if the DNS record is not resolved to the " +
        "provided address",
        "check_type": "remote.dns",
        "criteria": "# Match if the 127... address was in the resolution\n# if it wasn't than " +
        "default to CRITICAL\n\nif (metric['answer'] regex '.*${address}.*') {\n  return new " +
        "AlarmStatus(OK, 'Resolved the correct address!');\n}\nreturn new AlarmStatus(CRITICAL);\n",
        "fields": [{
            "name": "address",
            "description": "Address to which the DNS record must resolve to",
            "type": "string"
        }]
    }, {
        "id": "remote.ssh_fingerprint_match",
        "label": "SSH fingerprint match",
        "description": "Alarm which returns CRITICAL if the SSH fingerprint doesn't match the "
        "provided one",
        "check_type": "remote.ssh",
        "criteria": "if (metric['fingerprint'] != '${fingerprint}') {\n  return new " +
        "AlarmStatus(CRITICAL, 'SSH fingerprint didn\\'t match the expected one ${fingerprint}');" +
        "\n}\n\nreturn new AlarmStatus(OK, 'Got expected SSH fingerprint (${fingerprint})');\n",
        "fields": [{
            "name": "fingerprint",
            "description": "Expected SSH fingerprint",
            "type": "string"
        }]
    }, {
        "id": "remote.ping_packet_loss",
        "label": "Ping packet loss",
        "description": "Alarm which returns WARNING if the packet loss is greater than 5% and " +
        "CRITICAL if it's greater than 20%",
        "check_type": "remote.ping",
        "criteria": "if (metric['available'] < 80) {\n  return new AlarmStatus(CRITICAL, 'Packet loss" +
        " is greater than 20%');\n}\n\nif (metric['available'] < 95) {\n  return new " +
        "AlarmStatus(WARNING, 'Packet loss is greater than 5%');\n}\n\nreturn new AlarmStatus(OK, " +
        "'Packet loss is normal');\n",
        "fields": []
    }, {
        "id": "remote.tcp_connection_time",
        "label": "Connection time",
        "description": "Alarm which returns WARNING or CRITICAL based on the connection time",
        "check_type": "remote.tcp",
        "criteria": "if (metric['duration'] > ${critical_threshold}) {\n  return new AlarmStatus(" +
        "CRITICAL, 'TCP Connection took more than ${critical_threshold} milliseconds.');\n}\n\nif " +
        "(metric['duration'] > ${warning_threshold}) {\n  return new AlarmStatus(WARNING, 'TCP " +
        "Connection took more than ${warning_threshold} milliseconds.');\n}\n\nreturn new " +
        "AlarmStatus(OK, 'TCP connection time is normal');\n",
        "fields": [{
            "name": "warning_threshold",
            "description": "Warning threshold (in seconds) for the connection time",
            "type": "integer"
        }, {
            "name": "critical_threshold",
            "description": "Critical threshold (in seconds) for the connection time",
            "type": "integer"
        }]
    }, {
        "id": "remote.dns_spf_record_include_match",
        "label": "SPF TXT record",
        "description": "Alarm which returns CRITICAL if the SPF record doesn't contain an include " +
        "clause with the provided domain.",
        "check_type": "remote.dns",
        "criteria": "if (metric['answer'] regex 'v=spf1.* include:${domain} .*[~|-]all') {\n  return " +
        "new AlarmStatus(OK, 'SPF record with include clause for domain ${domain} exists');\n}\n\n" +
        "return new AlarmStatus(CRITICAL, 'SPF record doesn\\'t contain an include clause for domain " +
        "${domain}');\n",
        "fields": [{
            "name": "domain",
            "description": "Domain to check for",
            "type": "string"
        }]
    }, {
        "id": "remote.dns_dkim_public_key_match",
        "label": "DKIM TXT record",
        "description": "Alarm which returns CRITICAL if the DKIM record doesn't contain or match the " +
        "provided public key.",
        "check_type": "remote.dns",
        "criteria": "if (metric['answer'] regex '.*p=${public_key}$') {\n  return new AlarmStatus(OK," +
        " 'DKIM record contains a provided public key');\n}\n\nreturn new AlarmStatus(CRITICAL, 'DKIM " +
        "record doesn\\'t contain a provided public key');\n",
        "fields": [{
            "name": "public_key",
            "description": "Public key to check for. Note: Special characters must be escaped.",
            "type": "string"
        }]
    }, {
        "id": "agent.cpu_usage_average",
        "label": "CPU Usage",
        "description": "Alarm which returns CRITICAL, WARNING or OK based upon average CPU usage",
        "check_type": "agent.cpu",
        "criteria": "if (metric['usage_average'] > ${critical_threshold}) {\n  return new " +
        "AlarmStatus(CRITICAL, 'CPU usage is #{usage_average}%, above your critical threshold of " +
        "${critical_threshold}%');\n}\n\nif (metric['usage_average'] > ${warning_threshold}) {\n  " +
        "return new AlarmStatus(WARNING, 'CPU usage is #{usage_average}%, above your warning threshold" +
        " of ${warning_threshold}%');\n}\n\nreturn new AlarmStatus(OK, 'CPU usage is " +
        "#{usage_average}%, below your warning threshold of ${warning_threshold}%');\n",
        "fields": [{
            "name": "critical_threshold",
            "description": "CPU usage percentage above which CRITICAL is returned",
            "type": "whole number (may be zero padded)"
        }, {
            "name": "warning_threshold",
            "description": "CPU usage percentage above which WARNING is returned",
            "type": "whole number (may be zero padded)"
        }]
    }, {
        "id": "agent.memory_usage",
        "label": "Memory usage",
        "description": "Alarm which returns CRITICAL, WARNING or OK based upon memory usage",
        "check_type": "agent.memory",
        "criteria": "if (percentage(metric['actual_used'], metric['total']) > 90) {\n  return new " +
        "AlarmStatus(CRITICAL, \"Memory usage is above your critical threshold of 90%\");\n}\n\nif " +
        "(percentage(metric['actual_used'], metric['total']) > 80) {\n  return new AlarmStatus(" +
        "WARNING, \"Memory usage is above your warning threshold of 80%\");\n}\n\nreturn new " +
        "AlarmStatus(OK, \"Memory usage is below your warning threshold of 80%\");\n",
        "fields": []
    }, {
        "id": "agent.filesystem_usage",
        "label": "Filesystem usage",
        "description": "Alarm which returns CRITICAL, WARNING or OK based upon filesystem usage",
        "check_type": "agent.filesystem",
        "criteria": "if (percentage(metric['used'], metric['total']) > 90) {\n  return new " +
        "AlarmStatus(CRITICAL, \"Disk usage is above your critical threshold of 90%\");\n}\n\nif " +
        "(percentage(metric['used'], metric['total']) > 80) {\n  return new AlarmStatus(WARNING, " +
        "\"Disk usage is above your warning threshold of 80%\");\n}\n\nreturn new AlarmStatus(OK, " +
        "\"Disk usage is below your warning threshold of 80%\");\n",
        "fields": []
    }, {
        "id": "agent.high_load_average",
        "label": "High Load Average",
        "description": "Alarm which returns CRITICAL, WARNING or OK based on load average",
        "check_type": "agent.load_average",
        "criteria": "if (metric['5m'] > ${critical_threshold}) {\n  return new AlarmStatus(CRITICAL," +
        " '5 minute load average is #{5m}, above your critical threshold of ${critical_threshold}');" +
        "\n}\n\nif (metric['5m'] > ${warning_threshold}) {\n  return new AlarmStatus(WARNING, '5 " +
        "minute load average is #{5m}, above your warning threshold of ${warning_threshold}');\n}\n\n" +
        "return new AlarmStatus(OK, '5 minute load average is #{5m}, below your warning threshold of " +
        "${warning_threshold}');\n",
        "fields": [{
            "name": "critical_threshold",
            "description": "Load average above which CRITICAL is returned",
            "type": "whole number (may be zero padded)"
        }, {
            "name": "warning_threshold",
            "description": "Load average above which WARNING is returned",
            "type": "whole number (may be zero padded)"
        }]
    }, {
        "id": "agent.network_transmit_rate",
        "label": "Network transmit rate",
        "description": "Alarm which returns CRITICAL, WARNING or OK based upon network transmit rate",
        "check_type": "agent.network",
        "criteria": "if (rate(metric['tx_bytes']) > ${critical_threshold}) {\n  return new " +
        "AlarmStatus(CRITICAL, \"Network transmit rate on ${interface} is above your critical " +
        "threshold of ${critical_threshold}B/s\");\n}\n\nif (rate(metric['tx_bytes']) > " +
        "${warning_threshold}) {\n  return new AlarmStatus(WARNING, \"Network transmit rate on " +
        "${interface} is above your warning threshold of ${warning_threshold}B/s\");\n}\n\nreturn new " +
        "AlarmStatus(OK, \"Network transmit rate on ${interface} is below your warning threshold of " +
        "${warning_threshold}B/s\");\n",
        "fields": [{
            "name": "interface",
            "description": "The network interface to alert on",
            "type": "string"
        }, {
            "name": "critical_threshold",
            "description": "Network transmit rate, in bytes per second, above which CRITICAL is " +
            "returned",
            "type": "whole number (may be zero padded)"
        }, {
            "name": "warning_threshold",
            "description": "Network transmit rate, in bytes per second, above which WARNING is returned",
            "type": "whole number (may be zero padded)"
        }]
    }, {
        "id": "agent.network_receive_rate",
        "label": "Network receive rate",
        "description": "Alarm which returns CRITICAL, WARNING or OK based upon network receive rate",
        "check_type": "agent.network",
        "criteria": "if (rate(metric['rx_bytes']) > ${critical_threshold}) {\n  return new " +
        "AlarmStatus(CRITICAL, \"Network receive rate on ${interface} is above your critical " +
        "threshold of ${critical_threshold}B/s\");\n}\n\nif (rate(metric['rx_bytes']) > " +
        "${warning_threshold}) {\n  return new AlarmStatus(WARNING, \"Network receive rate on " +
        "${interface} is above your warning threshold of ${warning_threshold}B/s\");\n}\n\nreturn new " +
        "AlarmStatus(OK, \"Network receive rate on ${interface} is below your warning threshold of " +
        "${warning_threshold}B/s\");\n",
        "fields": [{
            "name": "interface",
            "description": "The network interface to alert on",
            "type": "string"
        }, {
            "name": "critical_threshold",
            "description": "Network receive rate, in bytes per second, above which CRITICAL is returned",
            "type": "whole number (may be zero padded)"
        }, {
            "name": "warning_threshold",
            "description": "Network receive rate, in bytes per second, above which WARNING is returned",
            "type": "whole number (may be zero padded)"
        }]
    }, {
        "id": "agent.mysql_threads_connected_threshold",
        "label": "Connected Threads",
        "description": "Alarm which returns WARNING if the threads connected is over the specified " +
        "threshold and OK if it is under the specified threshold.",
        "check_type": "agent.mysql",
        "criteria": "if (metric['threads.connected'] > ${threads.connected.threshold}) {\n\treturn " +
        "new AlarmStatus(WARNING, 'Total number of threads connected are above your threshold of " +
        "${threads.connected.threshold}');\n}\nreturn new AlarmStatus(OK, 'Total number of threads " +
        "connected are below your warning threshold of ${threads.connected.threshold}');\n",
        "fields": [{
            "name": "threads.connected.threshold",
            "description": "Warning threshold for the number of connections",
            "type": "whole number (may be zero padded)"
        }]
    }]
