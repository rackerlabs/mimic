"""
Fixtures for metrics
"""

# Remove this when changing over to object model
# as this is repeated within the check_template

metrics_common_template = {
    "check": {
        "state": {
            "running": "false",
            "killed": "false",
            "configured": "true",
            "disabled": "false",
            "target_ip": "23.253.6.64",
            "last_run": {
                "@now": "1422323039.361",
                "#text": "1422323039.357"
            },
            "runtime": "0.958",
            "availability": "available",
            "state": "good",
            "status": "ok",
            "metrics": [
                {
                    "@type": "inprogress"
                },
                {
                    "@type": "current",
                    "@timestamp": "1422323039.357"
                }
            ]
        }
    }
}


metrics = {
    "selfcheck": {
        "metric": [
            {"@name": "version",
             "@type": "s",
             "#text": "ckdev-stage.8e17ed475b8a80103d11ec29e5e122fe256f8bf7.1416497041"},
            {"@name": "check_cnt",
             "@type": "i",
             "#text": "5"},
            {"@name": "transient_cnt",
             "@type": "i",
             "#text": "0"},
            {"@name": "uptime",
             "@type": "l",
             "#text": "165"},
            {"@name": "metrics_collected",
             "@type": "L",
             "#text": "321"},
            {"@name": "feed_bytes",
             "@type": "l",
             "#text": "23817"},
            {"@name": "default_queue_threads",
             "@type": "i",
             "#text": "10"},
            {"@name": "checks_run",
             "@type": "L",
             "#text": "50"}
        ]
    },
    "ping_icmp": {
        "metric": [
            {"@name": "available",
             "@type": "n",
             "#text": "0.000000000000e+00"},
            {"@name": "count",
             "@type": "i",
             "#text": "2"},
            {"@name": "maximum",
             "@type": "n"},
            {"@name": "minimum",
             "@type": "n"},
            {"@name": "average",
             "@type": "n"}
        ]

    },
    "tcp": {
        "metric": [
            {"@name": "banner",
             "@type": "s",
             "#text": "test"},
            {"@name": "test_banner_match",
             "@type": "s",
             "#text": "test"},
            {"@name": "body_match",
             "@type": "s",
             "#text": "test_body_match"},
            {"@name": "duration",
             "@type": "i",
             "#text": "30"},
            {"@name": "tt_body",
             "@type": "i",
             "#text": "1"},
            {"@name": "tt_connect",
             "@type": "i",
             "#text": "2"},
            {"@name": "tt_firstbyte",
             "@type": "i",
             "#text": "3"}
        ]
    },
    "http": {
        "metric": [
            {
                "@name": "cert_end",
                "@type": "I",
                "#text": "1471910399"
            },
            {
                "@name": "truncated",
                "@type": "I",
                "#text": "0"
            },
            {
                "@name": "cert_subject",
                "@type": "s",
                "#text": ("\/C=US\/ST=Texas\/L=San Antonio\/O=Rackspace US,"
                          " Inc.\/OU=Marketing\/CN=www.rackspace.com")
            },
            {
                "@name": "cert_start",
                "@type": "I",
                "#text": "1415059200"
            },
            {
                "@name": "cert_issuer",
                "@type": "s",
                "#text": ("\/C=US\/O=Symantec Corporation\/OU=Symantec"
                          " Trust Network\/CN=Symantec Class 3 Secure Server CA - G4")
            },
            {
                "@name": "code",
                "@type": "s",
                "#text": "200"
            },
            {
                "@name": "tt_connect",
                "@type": "I",
                "#text": "72"
            },
            {
                "@name": "cert_end_in",
                "@type": "i",
                "#text": "49587360"
            },
            {
                "@name": "tt_firstbyte",
                "@type": "I",
                "#text": "957"
            },
            {
                "@name": "bytes",
                "@type": "i",
                "#text": "44779"
            },
            {
                "@name": "cert_subject_alternative_names",
                "@type": "s",
                "#text": ("wwwp.wip.rackspace.com, ord.wwwp.wip.rackspace.com,"
                          " iad.wwwp.wip.rackspace.com, admin.rackspace.com,"
                          " iad.wip.rackspace.com, ord.wip.rackspace.com, www.rackspace.com")
            },
            {
                "@name": "cert_error",
                "@type": "s",
                "#text": ("No certificate present., host header "
                          "does not match CN or SANs in certificate")
            },
            {
                "@name": "duration",
                "@type": "I",
                "#text": "957"
            }
        ]
    }
}
