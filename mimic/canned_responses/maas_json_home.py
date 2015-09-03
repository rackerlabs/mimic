"""
Canned response for monitoring json home
"""


def json_home(url):
    """
    Canned response for the json_home call
    """
    return {
        "resources": {
            url + "/{tenantId}/account": {
                "href-template": "/v1.0/{tenantId}/account",
                "href-vars": {
                    "tenantId": "http://docs.rackspace.com/cm/api/v1.0/cm-devguide/params/tenantId"
                },
                "hints": {
                    "docs": ("http://docs.rackspace.com/cm/api/v1.0/cm-devguide"
                             "/content/service-account.html"),
                    "allow": [
                        "GET",
                        "PUT"
                    ],
                    "representations": [
                        "application/json",
                        "application/xml"
                    ],
                    "accept-put": [
                        "application/xml",
                        "application/json"
                    ]
                }
            },
            url + "/{tenantId}/agents": {
                "href-template": "/v1.0/{tenantId}/agents",
                "href-vars": {
                    "tenantId": "http://docs.rackspace.com/cm/api/v1.0/cm-devguide/params/tenantId"
                },
                "hints": {
                    "docs": ("http://docs.rackspace.com/cm/api/v1.0/cm-devguide"
                             "/content/service-agents.html"),
                    "allow": [
                        "GET"
                    ],
                    "representations": [
                        "application/json",
                        "application/xml"
                    ]
                }
            },
            url + "/{tenantId}/agents/{agentId}": {
                "href-template": "/v1.0/{tenantId}/agents/{agentId}",
                "href-vars": {
                    "tenantId": "http://docs.rackspace.com/cm/api/v1.0/cm-devguide/params/tenantId",
                    "agentId": "http://docs.rackspace.com/cm/api/v1.0/cm-devguide/params/agentId"
                },
                "hints": {
                    "docs": ("http://docs.rackspace.com/cm/api/v1.0/cm-devguide"
                             "/content/service-agents.html"),
                    "allow": [
                        "GET"
                    ],
                    "representations": [
                        "application/json",
                        "application/xml"
                    ]
                }
            },
            url + "/{tenantId}/agents/{agentId}/connections": {
                "href-template": "/v1.0/{tenantId}/agents/{agentId}/connections",
                "href-vars": {
                    "tenantId": "http://docs.rackspace.com/cm/api/v1.0/cm-devguide/params/tenantId",
                    "agentId": "http://docs.rackspace.com/cm/api/v1.0/cm-devguide/params/agentId"
                },
                "hints": {
                    "docs": ("http://docs.rackspace.com/cm/api/v1.0/cm-devguide/content/"
                             "service-agent-connections.html"),
                    "allow": [
                        "GET"
                    ],
                    "representations": [
                        "application/json",
                        "application/xml"
                    ]
                }
            },
            url + "/{tenantId}/agents/{agentId}/connections/{connId}": {
                "href-template": "/v1.0/{tenantId}/agents/{agentId}/connections/{connId}",
                "href-vars": {
                    "tenantId": "http://docs.rackspace.com/cm/api/v1.0/cm-devguide/params/tenantId",
                    "agentId": "http://docs.rackspace.com/cm/api/v1.0/cm-devguide/params/agentId",
                    "connId": "http://docs.rackspace.com/cm/api/v1.0/cm-devguide/params/connId"
                },
                "hints": {
                    "docs": ("http://docs.rackspace.com/cm/api/v1.0/cm-devguide"
                             "/content/service-agent-connections.html"),
                    "allow": [
                        "GET"
                    ],
                    "representations": [
                        "application/json",
                        "application/xml"
                    ]
                }
            },
            url + "/{tenantId}/agents/{agentId}/host_info_types": {
                "href-template": "/v1.0/{tenantId}/agents/{agentId}/host_info_types",
                "href-vars": {
                    "tenantId": "http://docs.rackspace.com/cm/api/v1.0/cm-devguide/params/tenantId",
                    "agentId": "http://docs.rackspace.com/cm/api/v1.0/cm-devguide/params/agentId"
                },
                "hints": {
                    "docs": ("http://docs.rackspace.com/cm/api/v1.0/cm-devguide"
                             "/content/service-agents.html"),
                    "allow": [
                        "GET"
                    ],
                    "representations": [
                        "application/json",
                        "application/xml"
                    ]
                }
            },
            url + "/{tenantId}/agents/{agentId}/host_info/{handlerType}": {
                "href-template": "/v1.0/{tenantId}/agents/{agentId}/host_info/{handlerType}",
                "href-vars": {
                    "tenantId": "http://docs.rackspace.com/cm/api/v1.0/cm-devguide/params/tenantId",
                    "agentId": "http://docs.rackspace.com/cm/api/v1.0/cm-devguide/params/agentId",
                    "handlerType": "http://docs.rackspace.com/cm/api/v1.0/cm-devguide/params/handlerType"
                },
                "hints": {
                    "docs": ("http://docs.rackspace.com/cm/api/v1.0/cm-devguide"
                             "/content/service-agents.html"),
                    "allow": [
                        "GET"
                    ],
                    "representations": [
                        "application/json",
                        "application/xml"
                    ]
                }
            },
            url + "/{tenantId}/agent_tokens": {
                "href-template": "/v1.0/{tenantId}/agent_tokens",
                "href-vars": {
                    "tenantId": "http://docs.rackspace.com/cm/api/v1.0/cm-devguide/params/tenantId"
                },
                "hints": {
                    "docs": ("http://docs.rackspace.com/cm/api/v1.0/cm-devguide"
                             "/content/service-agent-tokens.html"),
                    "allow": [
                        "GET",
                        "POST"
                    ],
                    "representations": [
                        "application/json",
                        "application/xml"
                    ],
                    "accept-post": [
                        "application/xml",
                        "application/json"
                    ]
                }
            },
            url + "/{tenantId}/agent_tokens/{tokenId}": {
                "href-template": "/v1.0/{tenantId}/agent_tokens/{tokenId}",
                "href-vars": {
                    "tenantId": "http://docs.rackspace.com/cm/api/v1.0/cm-devguide/params/tenantId",
                    "tokenId": "http://docs.rackspace.com/cm/api/v1.0/cm-devguide/params/tokenId"
                },
                "hints": {
                    "docs": ("http://docs.rackspace.com/cm/api/v1.0/cm-devguide"
                             "/content/service-agent-tokens.html"),
                    "allow": [
                        "GET",
                        "PUT",
                        "DELETE"
                    ],
                    "representations": [
                        "application/json",
                        "application/xml"
                    ],
                    "accept-put": [
                        "application/xml",
                        "application/json"
                    ]
                }
            },
            url + "/{tenantId}/agent_installers": {
                "href-template": "/v1.0/{tenantId}/agent_installers",
                "href-vars": {
                    "tenantId": "http://docs.rackspace.com/cm/api/v1.0/cm-devguide/params/tenantId"
                },
                "hints": {
                    "docs": ("http://docs.rackspace.com/cm/api/v1.0/cm-devguide"
                             "/content/service-agent-installers.html"),
                    "allow": [
                        "POST"
                    ],
                    "representations": [
                        "application/json",
                        "application/xml"
                    ],
                    "accept-post": [
                        "application/xml",
                        "application/json"
                    ]
                }
            },
            url + "/{tenantId}/agent_installers/{installerId.sh}": {
                "href-template": "/v1.0/{tenantId}/agent_installers/{installerId.sh}",
                "href-vars": {
                    "tenantId": "http://docs.rackspace.com/cm/api/v1.0/cm-devguide/params/tenantId",
                    "installerId.sh": ("http://docs.rackspace.com/cm/api/v1.0/cm-devguide"
                                       "/params/installerId.sh")
                },
                "hints": {
                    "docs": ("http://docs.rackspace.com/cm/api/v1.0/cm-devguide"
                             "/content/service-agent-installers.html"),
                    "allow": [
                        "GET"
                    ],
                    "representations": [
                        "application/json",
                        "application/xml"
                    ]
                }
            },
            url + "/{tenantId}/agent_installers/{installerId}": {
                "href-template": "/v1.0/{tenantId}/agent_installers/{installerId}",
                "href-vars": {
                    "tenantId": "http://docs.rackspace.com/cm/api/v1.0/cm-devguide/params/tenantId",
                    "installerId": "http://docs.rackspace.com/cm/api/v1.0/cm-devguide/params/installerId"
                },
                "hints": {
                    "docs": ("http://docs.rackspace.com/cm/api/v1.0/cm-devguide"
                             "/content/service-agent-installers.html"),
                    "allow": [
                        "GET"
                    ],
                    "representations": [
                        "application/json",
                        "application/xml"
                    ]
                }
            },
            url + "/{tenantId}/monitoring_zones": {
                "href-template": "/v1.0/{tenantId}/monitoring_zones",
                "href-vars": {
                    "tenantId": "http://docs.rackspace.com/cm/api/v1.0/cm-devguide/params/tenantId"
                },
                "hints": {
                    "docs": ("http://docs.rackspace.com/cm/api/v1.0/cm-devguide"
                             "/content/service-monitoring-zones.html"),
                    "allow": [
                        "GET"
                    ],
                    "representations": [
                        "application/json",
                        "application/xml"
                    ]
                }
            },
            url + "/{tenantId}/monitoring_zones/{monitoringZoneId}": {
                "href-template": "/v1.0/{tenantId}/monitoring_zones/{monitoringZoneId}",
                "href-vars": {
                    "tenantId": "http://docs.rackspace.com/cm/api/v1.0/cm-devguide/params/tenantId",
                    "monitoringZoneId": ("http://docs.rackspace.com/cm/api/v1.0/"
                                         "cm-devguide/params/monitoringZoneId")
                },
                "hints": {
                    "docs": ("http://docs.rackspace.com/cm/api/v1.0/cm-devguide"
                             "/content/service-monitoring-zones.html"),
                    "allow": [
                        "GET"
                    ],
                    "representations": [
                        "application/json",
                        "application/xml"
                    ]
                }
            },
            url + "/{tenantId}/monitoring_zones/{monitoringZoneId}/traceroute": {
                "href-template": "/v1.0/{tenantId}/monitoring_zones/{monitoringZoneId}/traceroute",
                "href-vars": {
                    "tenantId": "http://docs.rackspace.com/cm/api/v1.0/cm-devguide/params/tenantId",
                    "monitoringZoneId": ("http://docs.rackspace.com/cm/api/v1.0/cm-devguide"
                                         "/params/monitoringZoneId")
                },
                "hints": {
                    "docs": ("http://docs.rackspace.com/cm/api/v1.0/cm-devguide"
                             "/content/service-monitoring-zones.html"),
                    "allow": [
                        "POST"
                    ],
                    "representations": [
                        "application/json",
                        "application/xml"
                    ],
                    "accept-post": [
                        "application/xml",
                        "application/json"
                    ]
                }
            },
            url + "/{tenantId}/changelogs/alarms": {
                "href-template": "/v1.0/{tenantId}/changelogs/alarms",
                "href-vars": {
                    "tenantId": "http://docs.rackspace.com/cm/api/v1.0/cm-devguide/params/tenantId"
                },
                "hints": {
                    "docs": ("http://docs.rackspace.com/cm/api/v1.0/cm-devguide"
                             "/content/service-alarms.html"),
                    "allow": [
                        "GET"
                    ],
                    "representations": [
                        "application/json",
                        "application/xml"
                    ]
                }
            },
            url + "/{tenantId}/entities": {
                "href-template": "/v1.0/{tenantId}/entities",
                "href-vars": {
                    "tenantId": "http://docs.rackspace.com/cm/api/v1.0/cm-devguide/params/tenantId"
                },
                "hints": {
                    "docs": ("http://docs.rackspace.com/cm/api/v1.0/cm-devguide"
                             "/content/service-entities.html"),
                    "allow": [
                        "GET",
                        "POST"
                    ],
                    "representations": [
                        "application/json",
                        "application/xml"
                    ],
                    "accept-post": [
                        "application/xml",
                        "application/json"
                    ]
                }
            },
            url + "/{tenantId}/entities/{entityId}": {
                "href-template": "/v1.0/{tenantId}/entities/{entityId}",
                "href-vars": {
                    "tenantId": "http://docs.rackspace.com/cm/api/v1.0/cm-devguide/params/tenantId",
                    "entityId": "http://docs.rackspace.com/cm/api/v1.0/cm-devguide/params/entityId"
                },
                "hints": {
                    "docs": ("http://docs.rackspace.com/cm/api/v1.0/cm-devguide"
                             "/content/service-entities.html"),
                    "allow": [
                        "GET",
                        "PUT",
                        "DELETE"
                    ],
                    "representations": [
                        "application/json",
                        "application/xml"
                    ],
                    "accept-put": [
                        "application/xml",
                        "application/json"
                    ]
                }
            },
            url + "/{tenantId}/entities/{entityId}/checks": {
                "href-template": "/v1.0/{tenantId}/entities/{entityId}/checks",
                "href-vars": {
                    "tenantId": "http://docs.rackspace.com/cm/api/v1.0/cm-devguide/params/tenantId",
                    "entityId": "http://docs.rackspace.com/cm/api/v1.0/cm-devguide/params/entityId"
                },
                "hints": {
                    "docs": ("http://docs.rackspace.com/cm/api/v1.0/cm-devguide"
                             "/content/service-checks.html"),
                    "allow": [
                        "GET",
                        "POST"
                    ],
                    "representations": [
                        "application/json",
                        "application/xml"
                    ],
                    "accept-post": [
                        "application/xml",
                        "application/json"
                    ]
                }
            },
            url + "/{tenantId}/entities/{entityId}/checks/{checkId}": {
                "href-template": "/v1.0/{tenantId}/entities/{entityId}/checks/{checkId}",
                "href-vars": {
                    "tenantId": "http://docs.rackspace.com/cm/api/v1.0/cm-devguide/params/tenantId",
                    "entityId": "http://docs.rackspace.com/cm/api/v1.0/cm-devguide/params/entityId",
                    "checkId": "http://docs.rackspace.com/cm/api/v1.0/cm-devguide/params/checkId"
                },
                "hints": {
                    "docs": ("http://docs.rackspace.com/cm/api/v1.0/cm-devguide"
                             "/content/service-checks.html"),
                    "allow": [
                        "GET",
                        "PUT",
                        "DELETE"
                    ],
                    "representations": [
                        "application/json",
                        "application/xml"
                    ],
                    "accept-put": [
                        "application/xml",
                        "application/json"
                    ]
                }
            },
            url + "/{tenantId}/entities/{entityId}/checks/{checkId}/test": {
                "href-template": "/v1.0/{tenantId}/entities/{entityId}/checks/{checkId}/test",
                "href-vars": {
                    "tenantId": "http://docs.rackspace.com/cm/api/v1.0/cm-devguide/params/tenantId",
                    "entityId": "http://docs.rackspace.com/cm/api/v1.0/cm-devguide/params/entityId",
                    "checkId": "http://docs.rackspace.com/cm/api/v1.0/cm-devguide/params/checkId"
                },
                "hints": {
                    "docs": ("http://docs.rackspace.com/cm/api/v1.0/cm-devguide"
                             "/content/service-checks.html"),
                    "allow": [
                        "POST"
                    ],
                    "representations": [
                        "application/json",
                        "application/xml"
                    ],
                    "accept-post": [
                        "application/xml",
                        "application/json"
                    ]
                }
            },
            url + "/{tenantId}/entities/{entityId}/test-check": {
                "href-template": "/v1.0/{tenantId}/entities/{entityId}/test-check",
                "href-vars": {
                    "tenantId": "http://docs.rackspace.com/cm/api/v1.0/cm-devguide/params/tenantId",
                    "entityId": "http://docs.rackspace.com/cm/api/v1.0/cm-devguide/params/entityId"
                },
                "hints": {
                    "docs": ("http://docs.rackspace.com/cm/api/v1.0/cm-devguide"
                             "/content/service-checks.html"),
                    "allow": [
                        "POST"
                    ],
                    "representations": [
                        "application/json",
                        "application/xml"
                    ],
                    "accept-post": [
                        "application/xml",
                        "application/json"
                    ]
                }
            },
            url + "/{tenantId}/entities/{entityId}/alarms": {
                "href-template": "/v1.0/{tenantId}/entities/{entityId}/alarms",
                "href-vars": {
                    "tenantId": "http://docs.rackspace.com/cm/api/v1.0/cm-devguide/params/tenantId",
                    "entityId": "http://docs.rackspace.com/cm/api/v1.0/cm-devguide/params/entityId"
                },
                "hints": {
                    "docs": ("http://docs.rackspace.com/cm/api/v1.0/cm-devguide"
                             "/content/service-alarms.html"),
                    "allow": [
                        "GET",
                        "POST"
                    ],
                    "representations": [
                        "application/json",
                        "application/xml"
                    ],
                    "accept-post": [
                        "application/xml",
                        "application/json"
                    ]
                }
            },
            url + "/{tenantId}/entities/{entityId}/alarms/{alarmId}": {
                "href-template": "/v1.0/{tenantId}/entities/{entityId}/alarms/{alarmId}",
                "href-vars": {
                    "tenantId": "http://docs.rackspace.com/cm/api/v1.0/cm-devguide/params/tenantId",
                    "entityId": "http://docs.rackspace.com/cm/api/v1.0/cm-devguide/params/entityId",
                    "alarmId": "http://docs.rackspace.com/cm/api/v1.0/cm-devguide/params/alarmId"
                },
                "hints": {
                    "docs": ("http://docs.rackspace.com/cm/api/v1.0/cm-devguide"
                             "/content/service-alarms.html"),
                    "allow": [
                        "GET",
                        "PUT",
                        "DELETE"
                    ],
                    "representations": [
                        "application/json",
                        "application/xml"
                    ],
                    "accept-put": [
                        "application/xml",
                        "application/json"
                    ]
                }
            },
            url + "/{tenantId}/entities/{entityId}/test-alarm": {
                "href-template": "/v1.0/{tenantId}/entities/{entityId}/test-alarm",
                "href-vars": {
                    "tenantId": "http://docs.rackspace.com/cm/api/v1.0/cm-devguide/params/tenantId",
                    "entityId": "http://docs.rackspace.com/cm/api/v1.0/cm-devguide/params/entityId"
                },
                "hints": {
                    "docs": ("http://docs.rackspace.com/cm/api/v1.0/cm-devguide"
                             "/content/service-alarms.html"),
                    "allow": [
                        "POST"
                    ],
                    "representations": [
                        "application/json",
                        "application/xml"
                    ],
                    "accept-post": [
                        "application/xml",
                        "application/json"
                    ]
                }
            },
            url + "/{tenantId}/entities/{entityId}/agent/host_info/{handlerType}": {
                "href-template": "/v1.0/{tenantId}/entities/{entityId}/agent/host_info/{handlerType}",
                "href-vars": {
                    "tenantId": "http://docs.rackspace.com/cm/api/v1.0/cm-devguide/params/tenantId",
                    "entityId": "http://docs.rackspace.com/cm/api/v1.0/cm-devguide/params/entityId",
                    "handlerType": "http://docs.rackspace.com/cm/api/v1.0/cm-devguide/params/handlerType"
                },
                "hints": {
                    "docs": ("http://docs.rackspace.com/cm/api/v1.0/cm-devguide"
                             "/content/service-agents.html"),
                    "allow": [
                        "GET"
                    ],
                    "representations": [
                        "application/json",
                        "application/xml"
                    ]
                }
            },
            url + "/{tenantId}/entities/{entityId}/agent/check_types/{checkType}/targets": {
                "href-template": ("/v1.0/{tenantId}/entities/{entityId}/agent/"
                                  "check_types/{checkType}/targets"),
                "href-vars": {
                    "tenantId": "http://docs.rackspace.com/cm/api/v1.0/cm-devguide/params/tenantId",
                    "entityId": "http://docs.rackspace.com/cm/api/v1.0/cm-devguide/params/entityId",
                    "checkType": "http://docs.rackspace.com/cm/api/v1.0/cm-devguide/params/checkType"
                },
                "hints": {
                    "docs": ("http://docs.rackspace.com/cm/api/v1.0/cm-devguide"
                             "/content/service-agents.html"),
                    "allow": [
                        "GET"
                    ],
                    "representations": [
                        "application/json",
                        "application/xml"
                    ]
                }
            },
            url + "/{tenantId}/entities/{entityId}/alarms/{alarmId}/notification_history": {
                "href-template": ("/v1.0/{tenantId}/entities/{entityId}/alarms/"
                                  "{alarmId}/notification_history"),
                "href-vars": {
                    "tenantId": "http://docs.rackspace.com/cm/api/v1.0/cm-devguide/params/tenantId",
                    "entityId": "http://docs.rackspace.com/cm/api/v1.0/cm-devguide/params/entityId",
                    "alarmId": "http://docs.rackspace.com/cm/api/v1.0/cm-devguide/params/alarmId"
                },
                "hints": {
                    "docs": ("http://docs.rackspace.com/cm/api/v1.0/cm-devguide/"
                             "content/service-alarms.html"),
                    "allow": [
                        "GET"
                    ],
                    "representations": [
                        "application/json",
                        "application/xml"
                    ]
                }
            },
            url + "/{tenantId}/entities/{entityId}/alarms/{alarmId}/notification_history/{checkId}": {
                "href-template": ("/v1.0/{tenantId}/entities/{entityId}/alarms/"
                                  "{alarmId}/notification_history/{checkId}"),
                "href-vars": {
                    "tenantId": "http://docs.rackspace.com/cm/api/v1.0/cm-devguide/params/tenantId",
                    "entityId": "http://docs.rackspace.com/cm/api/v1.0/cm-devguide/params/entityId",
                    "alarmId": "http://docs.rackspace.com/cm/api/v1.0/cm-devguide/params/alarmId",
                    "checkId": "http://docs.rackspace.com/cm/api/v1.0/cm-devguide/params/checkId"
                },
                "hints": {
                    "docs": ("http://docs.rackspace.com/cm/api/v1.0/cm-devguide"
                             "/content/service-alarms.html"),
                    "allow": [
                        "GET"
                    ],
                    "representations": [
                        "application/json",
                        "application/xml"
                    ]
                }
            },
            url + ("/{tenantId}/entities/{entityId}/alarms/{alarmId}"
                   "/notification_history/{checkId}/{uuid}"): {
                "href-template": ("/v1.0/{tenantId}/entities/{entityId}/alarms/"
                                  "{alarmId}/notification_history/{checkId}/{uuid}"),
                "href-vars": {
                    "tenantId": "http://docs.rackspace.com/cm/api/v1.0/cm-devguide/params/tenantId",
                    "entityId": "http://docs.rackspace.com/cm/api/v1.0/cm-devguide/params/entityId",
                    "alarmId": "http://docs.rackspace.com/cm/api/v1.0/cm-devguide/params/alarmId",
                    "checkId": "http://docs.rackspace.com/cm/api/v1.0/cm-devguide/params/checkId",
                    "uuid": "http://docs.rackspace.com/cm/api/v1.0/cm-devguide/params/uuid"
                },
                "hints": {
                    "docs": ("http://docs.rackspace.com/cm/api/v1.0/cm-devguide"
                             "/content/service-alarms.html"),
                    "allow": [
                        "GET"
                    ],
                    "representations": [
                        "application/json",
                        "application/xml"
                    ]
                }
            },
            url + "/{tenantId}/check_types": {
                "href-template": "/v1.0/{tenantId}/check_types",
                "href-vars": {
                    "tenantId": "http://docs.rackspace.com/cm/api/v1.0/cm-devguide/params/tenantId"
                },
                "hints": {
                    "docs": ("http://docs.rackspace.com/cm/api/v1.0/cm-devguide"
                             "/content/service-check-types.html"),
                    "allow": [
                        "GET"
                    ],
                    "representations": [
                        "application/json",
                        "application/xml"
                    ]
                }
            },
            url + "/{tenantId}/check_types/{checkTypeId}": {
                "href-template": "/v1.0/{tenantId}/check_types/{checkTypeId}",
                "href-vars": {
                    "tenantId": "http://docs.rackspace.com/cm/api/v1.0/cm-devguide/params/tenantId",
                    "checkTypeId": "http://docs.rackspace.com/cm/api/v1.0/cm-devguide/params/checkTypeId"
                },
                "hints": {
                    "docs": ("http://docs.rackspace.com/cm/api/v1.0/cm-devguide"
                             "/content/service-check-types.html"),
                    "allow": [
                        "GET"
                    ],
                    "representations": [
                        "application/json",
                        "application/xml"
                    ]
                }
            },
            url + "/{tenantId}/notification_types": {
                "href-template": "/v1.0/{tenantId}/notification_types",
                "href-vars": {
                    "tenantId": "http://docs.rackspace.com/cm/api/v1.0/cm-devguide/params/tenantId"
                },
                "hints": {
                    "docs": ("http://docs.rackspace.com/cm/api/v1.0/cm-devguide"
                             "/content/service-notification-types.html"),
                    "allow": [
                        "GET"
                    ],
                    "representations": [
                        "application/json",
                        "application/xml"
                    ]
                }
            },
            url + "/{tenantId}/notification_types/{notificationTypeId}": {
                "href-template": "/v1.0/{tenantId}/notification_types/{notificationTypeId}",
                "href-vars": {
                    "tenantId": "http://docs.rackspace.com/cm/api/v1.0/cm-devguide/params/tenantId",
                    "notificationTypeId": ("http://docs.rackspace.com/cm/api/v1.0/cm-devguide"
                                           "/params/notificationTypeId")
                },
                "hints": {
                    "docs": ("http://docs.rackspace.com/cm/api/v1.0/cm-devguide"
                             "/content/service-notification-types.html"),
                    "allow": [
                        "GET"
                    ],
                    "representations": [
                        "application/json",
                        "application/xml"
                    ]
                }
            },
            url + "/{tenantId}/notifications": {
                "href-template": "/v1.0/{tenantId}/notifications",
                "href-vars": {
                    "tenantId": "http://docs.rackspace.com/cm/api/v1.0/cm-devguide/params/tenantId"
                },
                "hints": {
                    "docs": ("http://docs.rackspace.com/cm/api/v1.0/cm-devguide"
                             "/content/service-notifications.html"),
                    "allow": [
                        "GET",
                        "POST"
                    ],
                    "representations": [
                        "application/json",
                        "application/xml"
                    ],
                    "accept-post": [
                        "application/xml",
                        "application/json"
                    ]
                }
            },
            url + "/{tenantId}/notifications/{notificationId}": {
                "href-template": "/v1.0/{tenantId}/notifications/{notificationId}",
                "href-vars": {
                    "tenantId": "http://docs.rackspace.com/cm/api/v1.0/cm-devguide/params/tenantId",
                    "notificationId": ("http://docs.rackspace.com/cm/api/v1.0/cm-devguide"
                                       "/params/notificationId")
                },
                "hints": {
                    "docs": ("http://docs.rackspace.com/cm/api/v1.0/cm-devguide"
                             "/content/service-notifications.html"),
                    "allow": [
                        "GET",
                        "PUT",
                        "DELETE"
                    ],
                    "representations": [
                        "application/json",
                        "application/xml"
                    ],
                    "accept-put": [
                        "application/xml",
                        "application/json"
                    ]
                }
            },
            url + "/{tenantId}/notifications/{notificationId}/test": {
                "href-template": "/v1.0/{tenantId}/notifications/{notificationId}/test",
                "href-vars": {
                    "tenantId": "http://docs.rackspace.com/cm/api/v1.0/cm-devguide/params/tenantId",
                    "notificationId": ("http://docs.rackspace.com/cm/api/v1.0/cm-devguide"
                                       "/params/notificationId")
                },
                "hints": {
                    "docs": ("http://docs.rackspace.com/cm/api/v1.0/cm-devguide"
                             "/content/service-notifications.html"),
                    "allow": [
                        "POST"
                    ],
                    "representations": [
                        "application/json",
                        "application/xml"
                    ],
                    "accept-post": [
                        "application/xml",
                        "application/json"
                    ]
                }
            },
            url + "/{tenantId}/test-notification": {
                "href-template": "/v1.0/{tenantId}/test-notification",
                "href-vars": {
                    "tenantId": "http://docs.rackspace.com/cm/api/v1.0/cm-devguide/params/tenantId"
                },
                "hints": {
                    "docs": ("http://docs.rackspace.com/cm/api/v1.0/cm-devguide"
                             "/content/service-notifications.html"),
                    "allow": [
                        "POST"
                    ],
                    "representations": [
                        "application/json",
                        "application/xml"
                    ],
                    "accept-post": [
                        "application/xml",
                        "application/json"
                    ]
                }
            },
            url + "/{tenantId}/notification_plans": {
                "href-template": "/v1.0/{tenantId}/notification_plans",
                "href-vars": {
                    "tenantId": "http://docs.rackspace.com/cm/api/v1.0/cm-devguide/params/tenantId"
                },
                "hints": {
                    "docs": ("http://docs.rackspace.com/cm/api/v1.0/cm-devguide"
                             "/content/service-notification-plans.html"),
                    "allow": [
                        "GET",
                        "POST"
                    ],
                    "representations": [
                        "application/json",
                        "application/xml"
                    ],
                    "accept-post": [
                        "application/xml",
                        "application/json"
                    ]
                }
            },
            url + "/{tenantId}/notification_plans/{notificationPlanId}": {
                "href-template": "/v1.0/{tenantId}/notification_plans/{notificationPlanId}",
                "href-vars": {
                    "tenantId": "http://docs.rackspace.com/cm/api/v1.0/cm-devguide/params/tenantId",
                    "notificationPlanId": ("http://docs.rackspace.com/cm/api/v1.0/cm-devguide"
                                           "/params/notificationPlanId")
                },
                "hints": {
                    "docs": ("http://docs.rackspace.com/cm/api/v1.0/cm-devguide"
                             "/content/service-notification-plans.html"),
                    "allow": [
                        "GET",
                        "PUT",
                        "DELETE"
                    ],
                    "representations": [
                        "application/json",
                        "application/xml"
                    ],
                    "accept-put": [
                        "application/xml",
                        "application/json"
                    ]
                }
            },
            url + "/{tenantId}/audits": {
                "href-template": "/v1.0/{tenantId}/audits",
                "href-vars": {
                    "tenantId": "http://docs.rackspace.com/cm/api/v1.0/cm-devguide/params/tenantId"
                },
                "hints": {
                    "docs": ("http://docs.rackspace.com/cm/api/v1.0/cm-devguide"
                             "/content/service-audits.html"),
                    "allow": [
                        "GET"
                    ],
                    "representations": [
                        "application/json",
                        "application/xml"
                    ]
                }
            },
            url + "/{tenantId}/limits": {
                "href-template": "/v1.0/{tenantId}/limits",
                "href-vars": {
                    "tenantId": "http://docs.rackspace.com/cm/api/v1.0/cm-devguide/params/tenantId"
                },
                "hints": {
                    "docs": ("http://docs.rackspace.com/cm/api/v1.0/cm-devguide"
                             "/content/service-limits.html"),
                    "allow": [
                        "GET"
                    ],
                    "representations": [
                        "application/json",
                        "application/xml"
                    ]
                }
            },
            url + "/{tenantId}/usage": {
                "href-template": "/v1.0/{tenantId}/usage",
                "href-vars": {
                    "tenantId": "http://docs.rackspace.com/cm/api/v1.0/cm-devguide/params/tenantId"
                },
                "hints": {
                    "docs": ("http://docs.rackspace.com/cm/api/v1.0/cm-devguide"
                             "/content/service-usage.html"),
                    "allow": [
                        "GET"
                    ],
                    "representations": [
                        "application/json",
                        "application/xml"
                    ]
                }
            },
            url + "/{tenantId}/suppressions/{suppressionId}": {
                "href-template": "/v1.0/{tenantId}/suppressions/{suppressionId}",
                "href-vars": {
                    "tenantId": "http://docs.rackspace.com/cm/api/v1.0/cm-devguide/params/tenantId",
                    "suppressionId": ("http://docs.rackspace.com/cm/api/v1.0/cm-devguide"
                                      "/params/suppressionId")
                },
                "hints": {
                    "docs": ("http://docs.rackspace.com/cm/api/v1.0/cm-devguide"
                             "/content/service-suppressions.html"),
                    "allow": [
                        "GET",
                        "PUT",
                        "DELETE"
                    ],
                    "representations": [
                        "application/json",
                        "application/xml"
                    ],
                    "accept-put": [
                        "application/xml",
                        "application/json"
                    ]
                }
            },
            url + "/{tenantId}/suppressions": {
                "href-template": "/v1.0/{tenantId}/suppressions",
                "href-vars": {
                    "tenantId": "http://docs.rackspace.com/cm/api/v1.0/cm-devguide/params/tenantId"
                },
                "hints": {
                    "docs": ("http://docs.rackspace.com/cm/api/v1.0/cm-devguide"
                             "/content/service-suppressions.html"),
                    "allow": [
                        "POST",
                        "GET"
                    ],
                    "representations": [
                        "application/json",
                        "application/xml"
                    ],
                    "accept-post": [
                        "application/xml",
                        "application/json"
                    ]
                }
            },
            url + "/{tenantId}/suppression_logs": {
                "href-template": "/v1.0/{tenantId}/suppression_logs",
                "href-vars": {
                    "tenantId": "http://docs.rackspace.com/cm/api/v1.0/cm-devguide/params/tenantId"
                },
                "hints": {
                    "docs": ("http://docs.rackspace.com/cm/api/v1.0/cm-devguide"
                             "/content/service-suppression-log_entries.html"),
                    "allow": [
                        "GET"
                    ],
                    "representations": [
                        "application/json",
                        "application/xml"
                    ]
                }
            },
            url + "/{tenantId}/alarm_examples": {
                "href-template": "/v1.0/{tenantId}/alarm_examples",
                "href-vars": {
                    "tenantId": "http://docs.rackspace.com/cm/api/v1.0/cm-devguide/params/tenantId"
                },
                "hints": {
                    "docs": ("http://docs.rackspace.com/cm/api/v1.0/cm-devguide"
                             "/content/service-alarm-examples.html"),
                    "allow": [
                        "GET"
                    ],
                    "representations": [
                        "application/json",
                        "application/xml"
                    ]
                }
            },
            url + "/{tenantId}/alarm_examples/{alarmExampleId}": {
                "href-template": "/v1.0/{tenantId}/alarm_examples/{alarmExampleId}",
                "href-vars": {
                    "tenantId": "http://docs.rackspace.com/cm/api/v1.0/cm-devguide/params/tenantId",
                    "alarmExampleId": ("http://docs.rackspace.com/cm/api/v1.0/cm-devguide"
                                       "/params/alarmExampleId")
                },
                "hints": {
                    "docs": ("http://docs.rackspace.com/cm/api/v1.0/cm-devguide"
                             "/content/service-alarm-examples.html"),
                    "allow": [
                        "GET",
                        "POST"
                    ],
                    "representations": [
                        "application/json",
                        "application/xml"
                    ],
                    "accept-post": [
                        "application/xml",
                        "application/json"
                    ]
                }
            },
            url + "/{tenantId}/views/overview": {
                "href-template": "/v1.0/{tenantId}/views/overview",
                "href-vars": {
                    "tenantId": "http://docs.rackspace.com/cm/api/v1.0/cm-devguide/params/tenantId"
                },
                "hints": {
                    "docs": ("http://docs.rackspace.com/cm/api/v1.0/cm-devguide"
                             "/content/service-views.html"),
                    "allow": [
                        "GET"
                    ],
                    "representations": [
                        "application/json",
                        "application/xml"
                    ]
                }
            },
            url + "/{tenantId}/views/metric_list": {
                "href-template": "/v1.0/{tenantId}/views/metric_list",
                "href-vars": {
                    "tenantId": "http://docs.rackspace.com/cm/api/v1.0/cm-devguide/params/tenantId"
                },
                "hints": {
                    "docs": ("http://docs.rackspace.com/cm/api/v1.0/cm-devguide"
                             "/content/service-views.html"),
                    "allow": [
                        "GET"
                    ],
                    "representations": [
                        "application/json",
                        "application/xml"
                    ]
                }
            },
            url + "/{tenantId}/views/agent_host_info": {
                "href-template": "/v1.0/{tenantId}/views/agent_host_info",
                "href-vars": {
                    "tenantId": "http://docs.rackspace.com/cm/api/v1.0/cm-devguide/params/tenantId"
                },
                "hints": {
                    "docs": ("http://docs.rackspace.com/cm/api/v1.0/cm-devguide"
                             "/content/service-views.html"),
                    "allow": [
                        "GET"
                    ],
                    "representations": [
                        "application/json",
                        "application/xml"
                    ]
                }
            },
            url + "/{tenantId}/views/latest_alarm_states": {
                "href-template": "/v1.0/{tenantId}/views/latest_alarm_states",
                "href-vars": {
                    "tenantId": "http://docs.rackspace.com/cm/api/v1.0/cm-devguide/params/tenantId"
                },
                "hints": {
                    "docs": ("http://docs.rackspace.com/cm/api/v1.0/cm-devguide"
                             "/content/service-views.html"),
                    "allow": [
                        "GET"
                    ],
                    "representations": [
                        "application/json",
                        "application/xml"
                    ]
                }
            },
            url + "/{tenantId}/__experiments/json_home": {
                "href-template": "/v1.0/{tenantId}/__experiments/json_home",
                "href-vars": {
                    "tenantId": "http://docs.rackspace.com/cm/api/v1.0/cm-devguide/params/tenantId"
                },
                "hints": {
                    "docs": ("http://docs.rackspace.com/cm/api/v1.0/cm-devguide"
                             "/content/service-json-home.html"),
                    "allow": [
                        "GET"
                    ],
                    "representations": [
                        "application/json",
                        "application/xml"
                    ]
                }
            },
            url + "/{tenantId}/__experiments/multiplot": {
                "href-template": "/v1.0/{tenantId}/__experiments/multiplot",
                "href-vars": {
                    "tenantId": "http://docs.rackspace.com/cm/api/v1.0/cm-devguide/params/tenantId"
                },
                "hints": {
                    "docs": ("http://docs.rackspace.com/cm/api/v1.0/cm-devguide"
                             "/content/service-rollups.html"),
                    "allow": [
                        "POST"
                    ],
                    "representations": [
                        "application/json",
                        "application/xml"
                    ],
                    "accept-post": [
                        "application/xml",
                        "application/json"
                    ]
                }
            },
            url + "/{tenantId}/entities/{entityId}/checks/{checkId}/metrics/{metricName}/plot": {
                "href-template": ("/v1.0/{tenantId}/entities/{entityId}/checks"
                                  "/{checkId}/metrics/{metricName}/plot"),
                "href-vars": {
                    "tenantId": "http://docs.rackspace.com/cm/api/v1.0/cm-devguide/params/tenantId",
                    "entityId": "http://docs.rackspace.com/cm/api/v1.0/cm-devguide/params/entityId",
                    "checkId": "http://docs.rackspace.com/cm/api/v1.0/cm-devguide/params/checkId",
                    "metricName": "http://docs.rackspace.com/cm/api/v1.0/cm-devguide/params/metricName"
                },
                "hints": {
                    "docs": ("http://docs.rackspace.com/cm/api/v1.0/cm-devguide"
                             "/content/service-rollups.html"),
                    "allow": [
                        "GET"
                    ],
                    "representations": [
                        "application/json",
                        "application/xml"
                    ]
                }
            },
            url + "/{tenantId}/entities/{entityId}/checks/{checkId}/metrics": {
                "href-template": "/v1.0/{tenantId}/entities/{entityId}/checks/{checkId}/metrics",
                "href-vars": {
                    "tenantId": "http://docs.rackspace.com/cm/api/v1.0/cm-devguide/params/tenantId",
                    "entityId": "http://docs.rackspace.com/cm/api/v1.0/cm-devguide/params/entityId",
                    "checkId": "http://docs.rackspace.com/cm/api/v1.0/cm-devguide/params/checkId"
                },
                "hints": {
                    "docs": ("http://docs.rackspace.com/cm/api/v1.0/cm-devguide"
                             "/content/service-metric-names.html"),
                    "allow": [
                        "GET"
                    ],
                    "representations": [
                        "application/json",
                        "application/xml"
                    ]
                }
            }
        }
    }
