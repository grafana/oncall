from migrator.resources.escalation_policies import (
    match_escalation_policy,
    match_escalation_policy_for_integration,
)
from migrator.resources.integrations import match_integration, match_integration_type
from migrator.resources.schedules import match_schedule
from migrator.resources.users import (
    match_user,
    match_users_and_schedules_for_escalation_policy,
    match_users_for_schedule,
)

pd_users_payload = [
    {
        "id": "TESTUSER1",
        "name": "Test User",
        "email": "test1@test.com",
        "time_zone": "America/Lima",
        "color": "green",
        "role": "admin",
        "description": "I'm the boss",
        "invitation_sent": False,
        "contact_methods": [
            {
                "id": "PTDVERC",
                "type": "email_contact_method_reference",
                "summary": "Default",
                "self": "https://api.pagerduty.com/users/PXPGF42/contact_methods/PTDVERC",
            }
        ],
        "notification_rules": [
            {
                "id": "P8GRWKK",
                "type": "assignment_notification_rule_reference",
                "summary": "Default",
                "self": "https://api.pagerduty.com/users/PXPGF42/notification_rules/P8GRWKK",
                "html_url": None,
            }
        ],
        "job_title": "Director of Engineering",
        "teams": [],
    },
    {
        "id": "TESTUSER2",
        "name": "Another User",
        "email": "test2@test.com",
        "time_zone": "Asia/Hong_Kong",
        "color": "red",
        "role": "admin",
        "description": "Actually, I am the boss",
        "invitation_sent": False,
        "contact_methods": [
            {
                "id": "PVMGSML",
                "type": "email_contact_method_reference",
                "summary": "Work",
                "self": "https://api.pagerduty.com/users/PAM4FGS/contact_methods/PVMGSMLL",
            }
        ],
        "notification_rules": [
            {
                "id": "P8GRWKK",
                "type": "assignment_notification_rule_reference",
                "summary": "Default",
                "self": "https://api.pagerduty.com/users/PXPGF42/notification_rules/P8GRWKK",
                "html_url": None,
            }
        ],
        "job_title": "Senior Engineer",
        "teams": [],
    },
]
pd_schedules_payload = [
    {
        "id": "TESTSCH1",
        "type": "schedule",
        "summary": "TestSchedule1",
        "self": "https://api.pagerduty.com/schedules/TESTSCH1",
        "html_url": "https://subdomain.pagerduty.com/schedules/TESTSCH1",
        "name": "TestSchedule1",
        "time_zone": "Europe/London",
        "description": None,
        "web_cal_url": "webcal://subdomain.pagerduty.com/private/f28ddb81a7e0dac7d904631c1d121194c3bbcb3c6772a771a1d8f51fcf80d9d8/feed/TESTSCH1",
        "http_cal_url": "https://subdomain.pagerduty.com/private/f28ddb81a7e0dac7d904631c1d121194c3bbcb3c6772a771a1d8f51fcf80d9d8/feed/TESTSCH1",
        "users": [
            {
                "id": "TESTUSER1",
                "type": "user_reference",
                "summary": "Test User",
                "self": "https://api.pagerduty.com/users/TESTUSER1",
                "html_url": "https://subdomain.pagerduty.com/users/TESTUSER1",
            },
            {
                "id": "TESTUSER2",
                "type": "user_reference",
                "summary": "Another User",
                "self": "https://api.pagerduty.com/users/TESTUSER2",
                "html_url": "https://subdomain.pagerduty.com/users/TESTUSER2",
            },
        ],
        "escalation_policies": [],
        "teams": [],
    },
    {
        "id": "TESTSCH2",
        "type": "schedule",
        "summary": "TestSchedule2",
        "self": "https://api.pagerduty.com/schedules/TESTSCH2",
        "html_url": "https://subdomain.pagerduty.com/schedules/TESTSCH2",
        "name": "TestSchedule2",
        "time_zone": "Europe/London",
        "description": None,
        "web_cal_url": "webcal://subdomain.pagerduty.com/private/f28ddb81a7e0dac7d904631c1d121194c3bbcb3c6772a771a1d8f51fcf80d9d8/feed/TESTSCH2",
        "http_cal_url": "https://subdomain.pagerduty.com/private/f28ddb81a7e0dac7d904631c1d121194c3bbcb3c6772a771a1d8f51fcf80d9d8/feed/TESTSCH2",
        "users": [
            {
                "id": "TESTUSER1",
                "type": "user_reference",
                "summary": "Test User",
                "self": "https://api.pagerduty.com/users/TESTUSER1",
                "html_url": "https://subdomain.pagerduty.com/users/TESTUSER1",
            },
        ],
        "escalation_policies": [],
        "teams": [],
    },
    {
        "id": "TESTSCH3",
        "type": "schedule",
        "summary": "TestSchedule3",
        "self": "https://api.pagerduty.com/schedules/TESTSCH3",
        "html_url": "https://subdomain.pagerduty.com/schedules/TESTSCH3",
        "name": "TestSchedule3",
        "time_zone": "Europe/London",
        "description": None,
        "web_cal_url": "webcal://subdomain.pagerduty.com/private/f28ddb81a7e0dac7d904631c1d121194c3bbcb3c6772a771a1d8f51fcf80d9d8/feed/TESTSCH3",
        "http_cal_url": "https://subdomain.pagerduty.com/private/f28ddb81a7e0dac7d904631c1d121194c3bbcb3c6772a771a1d8f51fcf80d9d8/feed/TESTSCH3",
        "users": [
            {
                "id": "TESTUSER2",
                "type": "user_reference",
                "summary": "Another User",
                "self": "https://api.pagerduty.com/users/TESTUSER2",
                "html_url": "https://subdomain.pagerduty.com/users/TESTUSER2",
            },
        ],
        "escalation_policies": [],
        "teams": [],
    },
    {
        "id": "TESTSCH4",
        "type": "schedule",
        "summary": "TestSchedule4",
        "self": "https://api.pagerduty.com/schedules/TESTSCH4",
        "html_url": "https://subdomain.pagerduty.com/schedules/TESTSCH4",
        "name": "TestSchedule4",
        "time_zone": "Europe/London",
        "description": None,
        "web_cal_url": "webcal://subdomain.pagerduty.com/private/f28ddb81a7e0dac7d904631c1d121194c3bbcb3c6772a771a1d8f51fcf80d9d8/feed/TESTSCH4",
        "http_cal_url": "https://subdomain.pagerduty.com/private/f28ddb81a7e0dac7d904631c1d121194c3bbcb3c6772a771a1d8f51fcf80d9d8/feed/TESTSCH4",
        "users": [
            {
                "id": "TESTUSER3",
                "type": "user_reference",
                "summary": "Inactive User",
                "self": None,
                "html_url": "https://subdomain.pagerduty.com/users/TESTUSER3",
                "deleted_at": "2022-03-22T13:00:15-04:00",
            },
        ],
        "escalation_policies": [],
        "teams": [],
    },
]
pd_escalation_policies_payload = [
    {
        "id": "TESTPOL1",
        "type": "escalation_policy",
        "summary": "Test Escalation 1",
        "on_call_handoff_notifications": "if_has_services",
        "self": "https://api.pagerduty.com/escalation_policies/TESTPOL1",
        "html_url": "https://subdomain.pagerduty.com/escalation_policies/TESTPOL1",
        "name": "Test Escalation 1",
        "escalation_rules": [
            {
                "id": "PANZZEQ",
                "escalation_delay_in_minutes": 30,
                "targets": [
                    {
                        "id": "TESTSCH2",
                        "summary": "Daily Engineering Rotation",
                        "type": "schedule_reference",
                        "self": "https://api.pagerduty.com/schedules/TESTSCH2",
                        "html_url": "https://subdomain.pagerduty.com/schedules/TESTSCH2",
                    }
                ],
            }
        ],
        "services": [],
        "num_loops": 0,
        "teams": [],
    },
    {
        "id": "TESTPOL2",
        "type": "escalation_policy",
        "summary": "Test Escalation Policy 2",
        "on_call_handoff_notifications": "if_has_services",
        "self": "https://api.pagerduty.com/escalation_policies/TESTPOL2",
        "html_url": "https://subdomain.pagerduty.com/escalation_policies/TESTPOL2",
        "name": "Engineering Escalation Policy",
        "escalation_rules": [
            {
                "id": "PANZZEQ",
                "escalation_delay_in_minutes": 30,
                "targets": [
                    {
                        "id": "TESTSCH1",
                        "summary": "Daily Engineering Rotation",
                        "type": "schedule_reference",
                        "self": "https://api.pagerduty.com/schedules/PI7DH85",
                        "html_url": "https://subdomain.pagerduty.com/schedules/PI7DH85",
                    }
                ],
            }
        ],
        "services": [],
        "num_loops": 0,
        "teams": [],
    },
    {
        "id": "TESTPOL3",
        "type": "escalation_policy",
        "summary": "Test Escalation Policy 3",
        "on_call_handoff_notifications": "if_has_services",
        "self": "https://api.pagerduty.com/escalation_policies/TESTPOL3",
        "html_url": "https://subdomain.pagerduty.com/escalation_policies/TESTPOL3",
        "name": "Engineering Escalation Policy",
        "escalation_rules": [
            {
                "id": "PANZZEQ",
                "escalation_delay_in_minutes": 30,
                "targets": [
                    {
                        "id": "PI7DH85",
                        "summary": "Daily Engineering Rotation",
                        "type": "schedule_reference",
                        "self": None,
                        "html_url": "https://subdomain.pagerduty.com/schedules/PI7DH85",
                        "deleted_at": "2022-03-22T13:00:15-04:00",
                    }
                ],
            }
        ],
        "services": [],
        "num_loops": 0,
        "teams": [],
    },
    {
        "id": "TESTPOL4",
        "type": "escalation_policy",
        "summary": "Test Escalation Policy 4",
        "on_call_handoff_notifications": "if_has_services",
        "self": "https://api.pagerduty.com/escalation_policies/TESTPOL4",
        "html_url": "https://subdomain.pagerduty.com/escalation_policies/TESTPOL4",
        "name": "Engineering Escalation Policy",
        "escalation_rules": [
            {
                "id": "PANZZEQ",
                "escalation_delay_in_minutes": 30,
                "targets": [
                    {
                        "id": "TESTUSER1",
                        "summary": "PagerDuty Admin",
                        "type": "user_reference",
                        "self": "https://api.pagerduty.com/users/TESTUSER1",
                        "html_url": "https://subdomain.pagerduty.com/users/TESTUSER1",
                    },
                ],
            }
        ],
        "services": [],
        "num_loops": 0,
        "teams": [],
    },
    {
        "id": "TESTPOL5",
        "type": "escalation_policy",
        "summary": "Test Escalation Policy 5",
        "on_call_handoff_notifications": "if_has_services",
        "self": "https://api.pagerduty.com/escalation_policies/TESTPOL5",
        "html_url": "https://subdomain.pagerduty.com/escalation_policies/TESTPOL5",
        "name": "Engineering Escalation Policy",
        "escalation_rules": [
            {
                "id": "PANZZEQ",
                "escalation_delay_in_minutes": 30,
                "targets": [
                    {
                        "id": "TESTUSER2",
                        "summary": "PagerDuty Admin",
                        "type": "user_reference",
                        "self": "https://api.pagerduty.com/users/TESTUSER2",
                        "html_url": "https://subdomain.pagerduty.com/users/TESTUSER2",
                    },
                ],
            }
        ],
        "services": [],
        "num_loops": 0,
        "teams": [],
    },
    {
        "id": "TESTPOL6",
        "type": "escalation_policy",
        "summary": "Test Escalation Policy 6",
        "on_call_handoff_notifications": "if_has_services",
        "self": "https://api.pagerduty.com/escalation_policies/TESTPOL6",
        "html_url": "https://subdomain.pagerduty.com/escalation_policies/TESTPOL6",
        "name": "Engineering Escalation Policy",
        "escalation_rules": [
            {
                "id": "PANZZEQ",
                "escalation_delay_in_minutes": 30,
                "targets": [
                    {
                        "id": "TESTUSER3",
                        "summary": "PagerDuty Admin",
                        "type": "user_reference",
                        "self": None,
                        "html_url": "https://subdomain.pagerduty.com/users/TESTUSER3",
                        "deleted_at": "2022-03-22T13:00:15-04:00",
                    },
                ],
            }
        ],
        "services": [],
        "num_loops": 0,
        "teams": [],
    },
]
pd_services_payload = [
    {
        "id": "TESTSERVICE1",
        "summary": "Service",
        "type": "service",
        "self": "https://api.pagerduty.com/services/TESTSERVICE1",
        "html_url": "https://subdomain.pagerduty.com/services/TESTSERVICE1",
        "name": "Service",
        "auto_resolve_timeout": 14400,
        "acknowledgement_timeout": 600,
        "created_at": "2015-11-06T11:12:51-05:00",
        "status": "active",
        "alert_creation": "create_alerts_and_incidents",
        "alert_grouping_parameters": {"type": "intelligent"},
        "integrations": [
            {
                "id": "TESTINT1",
                "type": "generic_events_api_inbound_integration",
                "summary": "Test Integration",
                "self": "https://api.pagerduty.com/services/TESTSERVICE1/integrations/TESTINT1",
                "html_url": "https://subdomain.pagerduty.com/services/TESTSERVICE1/integrations/TESTINT1",
                "name": "Test Integration Datadog",
                "created_at": "2021-04-27T09:34:17-04:00",
                "vendor": {
                    "id": "TESTVENDOR1",
                    "type": "vendor_reference",
                    "summary": "Events API v1",
                    "self": "https://api.pagerduty.com/vendors/TESTVENDOR1",
                    "html_url": None,
                },
            },
            {
                "id": "TESTINT2",
                "type": "generic_events_api_inbound_integration",
                "summary": "Test Integration 2",
                "self": "https://api.pagerduty.com/services/TESTSERVICE1/integrations/TESTINT2",
                "html_url": "https://subdomain.pagerduty.com/services/TESTSERVICE1/integrations/TESTINT2",
                "name": "Test Integration 2",
                "created_at": "2021-04-27T09:34:17-04:00",
                "vendor": {
                    "id": "TESTVENDOR2",
                    "type": "vendor_reference",
                    "summary": "Events API v1",
                    "self": "https://api.pagerduty.com/vendors/TESTVENDOR2",
                    "html_url": None,
                },
            },
        ],
        "escalation_policy": {
            "id": "TESTPOL1",
            "type": "escalation_policy_reference",
            "summary": "Another Escalation Policy",
            "self": "https://api.pagerduty.com/escalation_policies/TESTPOL1",
            "html_url": "https://subdomain.pagerduty.com/escalation_policies/TESTPOL1",
        },
        "teams": [],
        "incident_urgency_rule": {"type": "constant", "urgency": "high"},
        "support_hours": None,
        "scheduled_actions": [],
    },
    {
        "id": "TESTSERVICE2",
        "summary": "My Application Service",
        "type": "service",
        "self": "https://api.pagerduty.com/services/TESTSERVICE2",
        "html_url": "https://subdomain.pagerduty.com/services/TESTSERVICE2",
        "name": "My Application Service",
        "auto_resolve_timeout": 14400,
        "acknowledgement_timeout": 600,
        "created_at": "2015-11-06T11:12:51-05:00",
        "status": "active",
        "alert_creation": "create_alerts_and_incidents",
        "alert_grouping_parameters": {"type": "intelligent"},
        "integrations": [
            {
                "id": "TESTINT3",
                "type": "generic_events_api_inbound_integration",
                "summary": "Test Integration",
                "self": "https://api.pagerduty.com/services/TESTSERVICE1/integrations/TESTINT3",
                "html_url": "https://subdomain.pagerduty.com/services/TESTSERVICE1/integrations/TESTINT3",
                "name": "Test Integration",
                "created_at": "2021-04-27T09:34:17-04:00",
                "vendor": {
                    "id": "TESTVENDOR1",
                    "type": "vendor_reference",
                    "summary": "Events API v1",
                    "self": "https://api.pagerduty.com/vendors/TESTVENDOR1",
                    "html_url": None,
                },
            },
            {
                "id": "TESTINT4",
                "type": "generic_events_api_inbound_integration",
                "summary": "Test Integration 2",
                "self": "https://api.pagerduty.com/services/TESTSERVICE1/integrations/TESTINT4",
                "html_url": "https://subdomain.pagerduty.com/services/TESTSERVICE1/integrations/TESTINT4",
                "name": "Test Integration 2",
                "created_at": "2021-04-27T09:34:17-04:00",
                "vendor": {
                    "id": "TESTVENDOR2",
                    "type": "vendor_reference",
                    "summary": "Events API v1",
                    "self": "https://api.pagerduty.com/vendors/TESTVENDOR2",
                    "html_url": None,
                },
            },
        ],
        "escalation_policy": {
            "id": "TESTPOL2",
            "type": "escalation_policy_reference",
            "summary": "Another Escalation Policy",
            "self": "https://api.pagerduty.com/escalation_policies/TESTPOL2",
            "html_url": "https://subdomain.pagerduty.com/escalation_policies/TESTPOL2",
        },
        "teams": [],
        "incident_urgency_rule": {"type": "constant", "urgency": "high"},
        "support_hours": None,
        "scheduled_actions": [],
    },
    {
        "id": "TESTSERVICE2",
        "summary": "My Application Service",
        "type": "service",
        "self": "https://api.pagerduty.com/services/TESTSERVICE2",
        "html_url": "https://subdomain.pagerduty.com/services/TESTSERVICE2",
        "name": "My Application Service",
        "auto_resolve_timeout": 14400,
        "acknowledgement_timeout": 600,
        "created_at": "2015-11-06T11:12:51-05:00",
        "status": "active",
        "alert_creation": "create_alerts_and_incidents",
        "alert_grouping_parameters": {"type": "intelligent"},
        "integrations": [
            {
                "id": "TESTINT5",
                "type": "generic_events_api_inbound_integration",
                "summary": "Test Integration",
                "self": "https://api.pagerduty.com/services/TESTSERVICE1/integrations/TESTINT5",
                "html_url": "https://subdomain.pagerduty.com/services/TESTSERVICE1/integrations/TESTINT5",
                "name": "Test Integration",
                "created_at": "2021-04-27T09:34:17-04:00",
                "vendor": {
                    "id": "TESTVENDOR1",
                    "type": "vendor_reference",
                    "summary": "Events API v1",
                    "self": "https://api.pagerduty.com/vendors/TESTVENDOR1",
                    "html_url": None,
                },
            },
            {
                "id": "TESTINT6",
                "type": "generic_events_api_inbound_integration",
                "summary": "Test Integration 2",
                "self": "https://api.pagerduty.com/services/TESTSERVICE1/integrations/TESTINT6",
                "html_url": "https://subdomain.pagerduty.com/services/TESTSERVICE1/integrations/TESTINT6",
                "name": "Test Integration 2",
                "created_at": "2021-04-27T09:34:17-04:00",
                "vendor": {
                    "id": "TESTVENDOR2",
                    "type": "vendor_reference",
                    "summary": "Events API v1",
                    "self": "https://api.pagerduty.com/vendors/TESTVENDOR2",
                    "html_url": None,
                },
            },
        ],
        "escalation_policy": {
            "id": "TESTPOL5",
            "type": "escalation_policy_reference",
            "summary": "Another Escalation Policy",
            "self": "https://api.pagerduty.com/escalation_policies/TESTPOL5",
            "html_url": "https://subdomain.pagerduty.com/escalation_policies/TESTPOL5",
        },
        "teams": [],
        "incident_urgency_rule": {"type": "constant", "urgency": "high"},
        "support_hours": None,
        "scheduled_actions": [],
    },
    {
        "id": "TESTSERVICE1",
        "summary": "My Application Service",
        "type": "service",
        "self": "https://api.pagerduty.com/services/TESTSERVICE1",
        "html_url": "https://subdomain.pagerduty.com/services/TESTSERVICE1",
        "name": "My Application Service",
        "auto_resolve_timeout": 14400,
        "acknowledgement_timeout": 600,
        "created_at": "2015-11-06T11:12:51-05:00",
        "status": "active",
        "alert_creation": "create_alerts_and_incidents",
        "alert_grouping_parameters": {"type": "intelligent"},
        "integrations": [
            {
                "id": "TESTINT7",
                "type": "generic_email_inbound_integration_reference",
                "summary": "Email Integration",
                "self": "https://api.pagerduty.com/services/TESTSERVICE1/integrations/TESTINT7",
                "html_url": "https://subdomain.pagerduty.com/services/TESTSERVICE1/integrations/TESTINT7",
                "name": "Email Integration",
                "created_at": "2021-04-27T09:34:17-04:00",
                "vendor": {
                    "id": "TESTVENDOR3",
                    "type": "vendor_reference",
                    "summary": "Email",
                    "self": "https://api.pagerduty.com/vendors/TESTVENDOR3",
                    "html_url": None,
                },
            },
        ],
        "escalation_policy": {
            "id": "TESTPOL1",
            "type": "escalation_policy_reference",
            "summary": "Another Escalation Policy",
            "self": "https://api.pagerduty.com/escalation_policies/TESTPOL1",
            "html_url": "https://subdomain.pagerduty.com/escalation_policies/TESTPOL1",
        },
        "teams": [],
        "incident_urgency_rule": {"type": "constant", "urgency": "high"},
        "support_hours": None,
        "scheduled_actions": [],
    },
]
pd_vendors_payload = [
    {
        "id": "TESTVENDOR1",
        "type": "vendor",
        "summary": "Datadog",
        "self": "https://api.pagerduty.com/vendors/TESTVENDOR1",
        "name": "Datadog",
        "website_url": "https://example.com",
        "logo_url": None,
        "thumbnail_url": None,
        "description": "",
        "integration_guide_url": "https://example.com",
    },
    {
        "id": "TESTVENDOR2",
        "type": "vendor",
        "summary": "Amazon CloudWatch",
        "self": "https://api.pagerduty.com/vendors/TESTVENDOR2",
        "name": "Amazon CloudWatch",
        "website_url": "https://example.com",
        "logo_url": None,
        "thumbnail_url": None,
        "description": "",
        "integration_guide_url": "https://example.com",
    },
    {
        "id": "TESTVENDOR3",
        "type": "vendor",
        "summary": "Email",
        "self": "https://api.pagerduty.com/vendors/TESTVENDOR3",
        "name": "Email",
        "description": "",
        "integration_guide_url": "https://example.com",
    },
]

oncall_users_payload = [
    {
        "id": "USERTESTID1",
        "email": "test1@test.com",
        "slack": None,
        "username": "Testuser",
        "role": "admin",
        "notification_rules": [
            {
                "id": "NOTIFTESTID1",
                "user_id": "USERTESTID1",
                "position": 0,
                "important": False,
                "type": "notify_by_slack",
            },
        ],
    },
    {
        "id": "USERTESTID2",
        "email": "othertest1@test.com",
        "slack": None,
        "username": "Other",
        "role": "admin",
        "notification_rules": [
            {
                "id": "NOTIFTESTID4",
                "user_id": "USERTESTID2",
                "position": 0,
                "important": False,
                "type": "notify_by_slack",
            }
        ],
    },
]
oncall_schedules_payload = [
    {
        "id": "SBM7DV7BKFUYU",
        "name": "TestSchedule1",
        "type": "ical",
        "time_zone": "America/New_York",
        "ical_url": "https://example.com/meow_calendar.ics",
        "on_call_now": [],
        "slack": None,
    }
]
oncall_escalation_chains = [
    {
        "id": "TESTCHAIN",
        "name": "Test Escalation 1",
        "team_id": None,
    }
]
oncall_integrations = [
    {
        "id": "TESTINTEGRATION",
        "name": "Service - Test Integration Datadog",
        "link": "https://app.amixr.io/integrations/v1/datadog/mReAoNwDm0eMwKo1mTeTwYo/",
        "incidents_count": 1,
        "type": "datadog",
        "default_route_id": "TESTROUTEID",
        "templates": {
            "grouping_key": None,
            "resolve_signal": None,
            "slack": {"title": None, "message": None, "image_url": None},
            "web": {"title": None, "message": None, "image_url": None},
            "email": {"title": None, "message": None},
            "sms": {"title": None},
            "phone_call": {"title": None},
            "telegram": {"title": None, "message": None, "image_url": None},
        },
    }
]

expected_users_match_result = [
    {
        "id": "TESTUSER1",
        "name": "Test User",
        "email": "test1@test.com",
        "time_zone": "America/Lima",
        "color": "green",
        "role": "admin",
        "description": "I'm the boss",
        "invitation_sent": False,
        "contact_methods": [
            {
                "id": "PTDVERC",
                "type": "email_contact_method_reference",
                "summary": "Default",
                "self": "https://api.pagerduty.com/users/PXPGF42/contact_methods/PTDVERC",
            }
        ],
        "notification_rules": [
            {
                "id": "P8GRWKK",
                "type": "assignment_notification_rule_reference",
                "summary": "Default",
                "self": "https://api.pagerduty.com/users/PXPGF42/notification_rules/P8GRWKK",
                "html_url": None,
            }
        ],
        "job_title": "Director of Engineering",
        "teams": [],
        "oncall_user": {
            "id": "USERTESTID1",
            "email": "test1@test.com",
            "slack": None,
            "username": "Testuser",
            "role": "admin",
            "notification_rules": [
                {
                    "id": "NOTIFTESTID1",
                    "user_id": "USERTESTID1",
                    "position": 0,
                    "important": False,
                    "type": "notify_by_slack",
                },
            ],
        },
    },
    {
        "id": "TESTUSER2",
        "name": "Another User",
        "email": "test2@test.com",
        "time_zone": "Asia/Hong_Kong",
        "color": "red",
        "role": "admin",
        "description": "Actually, I am the boss",
        "invitation_sent": False,
        "contact_methods": [
            {
                "id": "PVMGSML",
                "type": "email_contact_method_reference",
                "summary": "Work",
                "self": "https://api.pagerduty.com/users/PAM4FGS/contact_methods/PVMGSMLL",
            }
        ],
        "notification_rules": [
            {
                "id": "P8GRWKK",
                "type": "assignment_notification_rule_reference",
                "summary": "Default",
                "self": "https://api.pagerduty.com/users/PXPGF42/notification_rules/P8GRWKK",
                "html_url": None,
            }
        ],
        "job_title": "Senior Engineer",
        "teams": [],
        "oncall_user": None,
    },
]
expected_schedules_result = [
    {
        "id": "TESTSCH1",
        "type": "schedule",
        "summary": "TestSchedule1",
        "self": "https://api.pagerduty.com/schedules/TESTSCH1",
        "html_url": "https://subdomain.pagerduty.com/schedules/TESTSCH1",
        "name": "TestSchedule1",
        "time_zone": "Europe/London",
        "description": None,
        "web_cal_url": "webcal://subdomain.pagerduty.com/private/f28ddb81a7e0dac7d904631c1d121194c3bbcb3c6772a771a1d8f51fcf80d9d8/feed/TESTSCH1",
        "http_cal_url": "https://subdomain.pagerduty.com/private/f28ddb81a7e0dac7d904631c1d121194c3bbcb3c6772a771a1d8f51fcf80d9d8/feed/TESTSCH1",
        "users": [
            {
                "id": "TESTUSER1",
                "type": "user_reference",
                "summary": "Test User",
                "self": "https://api.pagerduty.com/users/TESTUSER1",
                "html_url": "https://subdomain.pagerduty.com/users/TESTUSER1",
            },
            {
                "id": "TESTUSER2",
                "type": "user_reference",
                "summary": "Another User",
                "self": "https://api.pagerduty.com/users/TESTUSER2",
                "html_url": "https://subdomain.pagerduty.com/users/TESTUSER2",
            },
        ],
        "escalation_policies": [],
        "teams": [],
        "oncall_schedule": {
            "id": "SBM7DV7BKFUYU",
            "name": "TestSchedule1",
            "type": "ical",
            "time_zone": "America/New_York",
            "ical_url": "https://example.com/meow_calendar.ics",
            "on_call_now": [],
            "slack": None,
        },
        "migration_errors": [],
        "unmatched_users": [
            {
                "id": "TESTUSER2",
                "name": "Another User",
                "email": "test2@test.com",
                "time_zone": "Asia/Hong_Kong",
                "color": "red",
                "role": "admin",
                "description": "Actually, I am the boss",
                "invitation_sent": False,
                "contact_methods": [
                    {
                        "id": "PVMGSML",
                        "type": "email_contact_method_reference",
                        "summary": "Work",
                        "self": "https://api.pagerduty.com/users/PAM4FGS/contact_methods/PVMGSMLL",
                    }
                ],
                "notification_rules": [
                    {
                        "id": "P8GRWKK",
                        "type": "assignment_notification_rule_reference",
                        "summary": "Default",
                        "self": "https://api.pagerduty.com/users/PXPGF42/notification_rules/P8GRWKK",
                        "html_url": None,
                    }
                ],
                "job_title": "Senior Engineer",
                "teams": [],
                "oncall_user": None,
            }
        ],
    },
    {
        "id": "TESTSCH2",
        "type": "schedule",
        "summary": "TestSchedule2",
        "self": "https://api.pagerduty.com/schedules/TESTSCH2",
        "html_url": "https://subdomain.pagerduty.com/schedules/TESTSCH2",
        "name": "TestSchedule2",
        "time_zone": "Europe/London",
        "description": None,
        "web_cal_url": "webcal://subdomain.pagerduty.com/private/f28ddb81a7e0dac7d904631c1d121194c3bbcb3c6772a771a1d8f51fcf80d9d8/feed/TESTSCH2",
        "http_cal_url": "https://subdomain.pagerduty.com/private/f28ddb81a7e0dac7d904631c1d121194c3bbcb3c6772a771a1d8f51fcf80d9d8/feed/TESTSCH2",
        "users": [
            {
                "id": "TESTUSER1",
                "type": "user_reference",
                "summary": "Test User",
                "self": "https://api.pagerduty.com/users/TESTUSER1",
                "html_url": "https://subdomain.pagerduty.com/users/TESTUSER1",
            },
        ],
        "escalation_policies": [],
        "teams": [],
        "oncall_schedule": None,
        "unmatched_users": [],
        "migration_errors": [],
    },
    {
        "id": "TESTSCH3",
        "type": "schedule",
        "summary": "TestSchedule3",
        "self": "https://api.pagerduty.com/schedules/TESTSCH3",
        "html_url": "https://subdomain.pagerduty.com/schedules/TESTSCH3",
        "name": "TestSchedule3",
        "time_zone": "Europe/London",
        "description": None,
        "web_cal_url": "webcal://subdomain.pagerduty.com/private/f28ddb81a7e0dac7d904631c1d121194c3bbcb3c6772a771a1d8f51fcf80d9d8/feed/TESTSCH3",
        "http_cal_url": "https://subdomain.pagerduty.com/private/f28ddb81a7e0dac7d904631c1d121194c3bbcb3c6772a771a1d8f51fcf80d9d8/feed/TESTSCH3",
        "users": [
            {
                "id": "TESTUSER2",
                "type": "user_reference",
                "summary": "Another User",
                "self": "https://api.pagerduty.com/users/TESTUSER2",
                "html_url": "https://subdomain.pagerduty.com/users/TESTUSER2",
            },
        ],
        "escalation_policies": [],
        "teams": [],
        "oncall_schedule": None,
        "migration_errors": [],
        "unmatched_users": [
            {
                "id": "TESTUSER2",
                "name": "Another User",
                "email": "test2@test.com",
                "time_zone": "Asia/Hong_Kong",
                "color": "red",
                "role": "admin",
                "description": "Actually, I am the boss",
                "invitation_sent": False,
                "contact_methods": [
                    {
                        "id": "PVMGSML",
                        "type": "email_contact_method_reference",
                        "summary": "Work",
                        "self": "https://api.pagerduty.com/users/PAM4FGS/contact_methods/PVMGSMLL",
                    }
                ],
                "notification_rules": [
                    {
                        "id": "P8GRWKK",
                        "type": "assignment_notification_rule_reference",
                        "summary": "Default",
                        "self": "https://api.pagerduty.com/users/PXPGF42/notification_rules/P8GRWKK",
                        "html_url": None,
                    }
                ],
                "job_title": "Senior Engineer",
                "teams": [],
                "oncall_user": None,
            }
        ],
    },
    {
        "id": "TESTSCH4",
        "type": "schedule",
        "summary": "TestSchedule4",
        "self": "https://api.pagerduty.com/schedules/TESTSCH4",
        "html_url": "https://subdomain.pagerduty.com/schedules/TESTSCH4",
        "name": "TestSchedule4",
        "time_zone": "Europe/London",
        "description": None,
        "web_cal_url": "webcal://subdomain.pagerduty.com/private/f28ddb81a7e0dac7d904631c1d121194c3bbcb3c6772a771a1d8f51fcf80d9d8/feed/TESTSCH4",
        "http_cal_url": "https://subdomain.pagerduty.com/private/f28ddb81a7e0dac7d904631c1d121194c3bbcb3c6772a771a1d8f51fcf80d9d8/feed/TESTSCH4",
        "users": [
            {
                "id": "TESTUSER3",
                "type": "user_reference",
                "summary": "Inactive User",
                "self": None,
                "html_url": "https://subdomain.pagerduty.com/users/TESTUSER3",
                "deleted_at": "2022-03-22T13:00:15-04:00",
            },
        ],
        "escalation_policies": [],
        "teams": [],
        "oncall_schedule": None,
        "unmatched_users": [],
        "migration_errors": [],
    },
]
expected_escalation_policies_result = [
    {
        "id": "TESTPOL1",
        "type": "escalation_policy",
        "summary": "Test Escalation 1",
        "on_call_handoff_notifications": "if_has_services",
        "self": "https://api.pagerduty.com/escalation_policies/TESTPOL1",
        "html_url": "https://subdomain.pagerduty.com/escalation_policies/TESTPOL1",
        "name": "Test Escalation 1",
        "escalation_rules": [
            {
                "id": "PANZZEQ",
                "escalation_delay_in_minutes": 30,
                "targets": [
                    {
                        "id": "TESTSCH2",
                        "summary": "Daily Engineering Rotation",
                        "type": "schedule_reference",
                        "self": "https://api.pagerduty.com/schedules/TESTSCH2",
                        "html_url": "https://subdomain.pagerduty.com/schedules/TESTSCH2",
                    }
                ],
            }
        ],
        "services": [],
        "num_loops": 0,
        "teams": [],
        "oncall_escalation_chain": {
            "id": "TESTCHAIN",
            "name": "Test Escalation 1",
            "team_id": None,
        },
        "unmatched_users": [],
        "flawed_schedules": [],
    },
    {
        "id": "TESTPOL2",
        "type": "escalation_policy",
        "summary": "Test Escalation Policy 2",
        "on_call_handoff_notifications": "if_has_services",
        "self": "https://api.pagerduty.com/escalation_policies/TESTPOL2",
        "html_url": "https://subdomain.pagerduty.com/escalation_policies/TESTPOL2",
        "name": "Engineering Escalation Policy",
        "escalation_rules": [
            {
                "id": "PANZZEQ",
                "escalation_delay_in_minutes": 30,
                "targets": [
                    {
                        "id": "TESTSCH1",
                        "summary": "Daily Engineering Rotation",
                        "type": "schedule_reference",
                        "self": "https://api.pagerduty.com/schedules/PI7DH85",
                        "html_url": "https://subdomain.pagerduty.com/schedules/PI7DH85",
                    }
                ],
            }
        ],
        "services": [],
        "num_loops": 0,
        "teams": [],
        "oncall_escalation_chain": None,
        "unmatched_users": [],
        "flawed_schedules": [
            {
                "id": "TESTSCH1",
                "type": "schedule",
                "summary": "TestSchedule1",
                "self": "https://api.pagerduty.com/schedules/TESTSCH1",
                "html_url": "https://subdomain.pagerduty.com/schedules/TESTSCH1",
                "name": "TestSchedule1",
                "time_zone": "Europe/London",
                "description": None,
                "web_cal_url": "webcal://subdomain.pagerduty.com/private/f28ddb81a7e0dac7d904631c1d121194c3bbcb3c6772a771a1d8f51fcf80d9d8/feed/TESTSCH1",
                "http_cal_url": "https://subdomain.pagerduty.com/private/f28ddb81a7e0dac7d904631c1d121194c3bbcb3c6772a771a1d8f51fcf80d9d8/feed/TESTSCH1",
                "users": [
                    {
                        "id": "TESTUSER1",
                        "type": "user_reference",
                        "summary": "Test User",
                        "self": "https://api.pagerduty.com/users/TESTUSER1",
                        "html_url": "https://subdomain.pagerduty.com/users/TESTUSER1",
                    },
                    {
                        "id": "TESTUSER2",
                        "type": "user_reference",
                        "summary": "Another User",
                        "self": "https://api.pagerduty.com/users/TESTUSER2",
                        "html_url": "https://subdomain.pagerduty.com/users/TESTUSER2",
                    },
                ],
                "escalation_policies": [],
                "teams": [],
                "oncall_schedule": {
                    "id": "SBM7DV7BKFUYU",
                    "name": "TestSchedule1",
                    "type": "ical",
                    "time_zone": "America/New_York",
                    "ical_url": "https://example.com/meow_calendar.ics",
                    "on_call_now": [],
                    "slack": None,
                },
                "migration_errors": [],
                "unmatched_users": [
                    {
                        "id": "TESTUSER2",
                        "name": "Another User",
                        "email": "test2@test.com",
                        "time_zone": "Asia/Hong_Kong",
                        "color": "red",
                        "role": "admin",
                        "description": "Actually, I am the boss",
                        "invitation_sent": False,
                        "contact_methods": [
                            {
                                "id": "PVMGSML",
                                "type": "email_contact_method_reference",
                                "summary": "Work",
                                "self": "https://api.pagerduty.com/users/PAM4FGS/contact_methods/PVMGSMLL",
                            }
                        ],
                        "notification_rules": [
                            {
                                "id": "P8GRWKK",
                                "type": "assignment_notification_rule_reference",
                                "summary": "Default",
                                "self": "https://api.pagerduty.com/users/PXPGF42/notification_rules/P8GRWKK",
                                "html_url": None,
                            }
                        ],
                        "job_title": "Senior Engineer",
                        "teams": [],
                        "oncall_user": None,
                    }
                ],
            },
        ],
    },
    {
        "id": "TESTPOL3",
        "type": "escalation_policy",
        "summary": "Test Escalation Policy 3",
        "on_call_handoff_notifications": "if_has_services",
        "self": "https://api.pagerduty.com/escalation_policies/TESTPOL3",
        "html_url": "https://subdomain.pagerduty.com/escalation_policies/TESTPOL3",
        "name": "Engineering Escalation Policy",
        "escalation_rules": [
            {
                "id": "PANZZEQ",
                "escalation_delay_in_minutes": 30,
                "targets": [
                    {
                        "id": "PI7DH85",
                        "summary": "Daily Engineering Rotation",
                        "type": "schedule_reference",
                        "self": None,
                        "html_url": "https://subdomain.pagerduty.com/schedules/PI7DH85",
                        "deleted_at": "2022-03-22T13:00:15-04:00",
                    }
                ],
            }
        ],
        "services": [],
        "num_loops": 0,
        "teams": [],
        "oncall_escalation_chain": None,
        "unmatched_users": [],
        "flawed_schedules": [],
    },
    {
        "id": "TESTPOL4",
        "type": "escalation_policy",
        "summary": "Test Escalation Policy 4",
        "on_call_handoff_notifications": "if_has_services",
        "self": "https://api.pagerduty.com/escalation_policies/TESTPOL4",
        "html_url": "https://subdomain.pagerduty.com/escalation_policies/TESTPOL4",
        "name": "Engineering Escalation Policy",
        "escalation_rules": [
            {
                "id": "PANZZEQ",
                "escalation_delay_in_minutes": 30,
                "targets": [
                    {
                        "id": "TESTUSER1",
                        "summary": "PagerDuty Admin",
                        "type": "user_reference",
                        "self": "https://api.pagerduty.com/users/TESTUSER1",
                        "html_url": "https://subdomain.pagerduty.com/users/TESTUSER1",
                    },
                ],
            }
        ],
        "services": [],
        "num_loops": 0,
        "teams": [],
        "oncall_escalation_chain": None,
        "unmatched_users": [],
        "flawed_schedules": [],
    },
    {
        "id": "TESTPOL5",
        "type": "escalation_policy",
        "summary": "Test Escalation Policy 5",
        "on_call_handoff_notifications": "if_has_services",
        "self": "https://api.pagerduty.com/escalation_policies/TESTPOL5",
        "html_url": "https://subdomain.pagerduty.com/escalation_policies/TESTPOL5",
        "name": "Engineering Escalation Policy",
        "escalation_rules": [
            {
                "id": "PANZZEQ",
                "escalation_delay_in_minutes": 30,
                "targets": [
                    {
                        "id": "TESTUSER2",
                        "summary": "PagerDuty Admin",
                        "type": "user_reference",
                        "self": "https://api.pagerduty.com/users/TESTUSER2",
                        "html_url": "https://subdomain.pagerduty.com/users/TESTUSER2",
                    },
                ],
            }
        ],
        "services": [],
        "num_loops": 0,
        "teams": [],
        "oncall_escalation_chain": None,
        "unmatched_users": [
            {
                "id": "TESTUSER2",
                "name": "Another User",
                "email": "test2@test.com",
                "time_zone": "Asia/Hong_Kong",
                "color": "red",
                "role": "admin",
                "description": "Actually, I am the boss",
                "invitation_sent": False,
                "contact_methods": [
                    {
                        "id": "PVMGSML",
                        "type": "email_contact_method_reference",
                        "summary": "Work",
                        "self": "https://api.pagerduty.com/users/PAM4FGS/contact_methods/PVMGSMLL",
                    }
                ],
                "notification_rules": [
                    {
                        "id": "P8GRWKK",
                        "type": "assignment_notification_rule_reference",
                        "summary": "Default",
                        "self": "https://api.pagerduty.com/users/PXPGF42/notification_rules/P8GRWKK",
                        "html_url": None,
                    }
                ],
                "job_title": "Senior Engineer",
                "teams": [],
                "oncall_user": None,
            },
        ],
        "flawed_schedules": [],
    },
    {
        "id": "TESTPOL6",
        "type": "escalation_policy",
        "summary": "Test Escalation Policy 6",
        "on_call_handoff_notifications": "if_has_services",
        "self": "https://api.pagerduty.com/escalation_policies/TESTPOL6",
        "html_url": "https://subdomain.pagerduty.com/escalation_policies/TESTPOL6",
        "name": "Engineering Escalation Policy",
        "escalation_rules": [
            {
                "id": "PANZZEQ",
                "escalation_delay_in_minutes": 30,
                "targets": [
                    {
                        "id": "TESTUSER3",
                        "summary": "PagerDuty Admin",
                        "type": "user_reference",
                        "self": None,
                        "html_url": "https://subdomain.pagerduty.com/users/TESTUSER3",
                        "deleted_at": "2022-03-22T13:00:15-04:00",
                    },
                ],
            }
        ],
        "services": [],
        "num_loops": 0,
        "teams": [],
        "oncall_escalation_chain": None,
        "unmatched_users": [],
        "flawed_schedules": [],
    },
]
expected_integrations_result = [
    {
        "id": "TESTINT1",
        "type": "generic_events_api_inbound_integration",
        "summary": "Test Integration",
        "self": "https://api.pagerduty.com/services/TESTSERVICE1/integrations/TESTINT1",
        "html_url": "https://subdomain.pagerduty.com/services/TESTSERVICE1/integrations/TESTINT1",
        "name": "Test Integration Datadog",
        "created_at": "2021-04-27T09:34:17-04:00",
        "vendor": {
            "id": "TESTVENDOR1",
            "type": "vendor_reference",
            "summary": "Events API v1",
            "self": "https://api.pagerduty.com/vendors/TESTVENDOR1",
            "html_url": None,
        },
        "vendor_name": "Datadog",
        "service": {
            "id": "TESTSERVICE1",
            "summary": "Service",
            "type": "service",
            "self": "https://api.pagerduty.com/services/TESTSERVICE1",
            "html_url": "https://subdomain.pagerduty.com/services/TESTSERVICE1",
            "name": "Service",
            "auto_resolve_timeout": 14400,
            "acknowledgement_timeout": 600,
            "created_at": "2015-11-06T11:12:51-05:00",
            "status": "active",
            "alert_creation": "create_alerts_and_incidents",
            "alert_grouping_parameters": {"type": "intelligent"},
            "escalation_policy": {
                "id": "TESTPOL1",
                "type": "escalation_policy_reference",
                "summary": "Another Escalation Policy",
                "self": "https://api.pagerduty.com/escalation_policies/TESTPOL1",
                "html_url": "https://subdomain.pagerduty.com/escalation_policies/TESTPOL1",
            },
            "teams": [],
            "incident_urgency_rule": {"type": "constant", "urgency": "high"},
            "support_hours": None,
            "scheduled_actions": [],
        },
        "oncall_integration": {
            "id": "TESTINTEGRATION",
            "name": "Service - Test Integration Datadog",
            "link": "https://app.amixr.io/integrations/v1/datadog/mReAoNwDm0eMwKo1mTeTwYo/",
            "incidents_count": 1,
            "type": "datadog",
            "default_route_id": "TESTROUTEID",
            "templates": {
                "grouping_key": None,
                "resolve_signal": None,
                "slack": {"title": None, "message": None, "image_url": None},
                "web": {"title": None, "message": None, "image_url": None},
                "email": {"title": None, "message": None},
                "sms": {"title": None},
                "phone_call": {"title": None},
                "telegram": {"title": None, "message": None, "image_url": None},
            },
        },
        "oncall_type": "datadog",
        "is_escalation_policy_flawed": False,
    },
    {
        "id": "TESTINT2",
        "type": "generic_events_api_inbound_integration",
        "summary": "Test Integration 2",
        "self": "https://api.pagerduty.com/services/TESTSERVICE1/integrations/TESTINT2",
        "html_url": "https://subdomain.pagerduty.com/services/TESTSERVICE1/integrations/TESTINT2",
        "name": "Test Integration 2",
        "created_at": "2021-04-27T09:34:17-04:00",
        "vendor": {
            "id": "TESTVENDOR2",
            "type": "vendor_reference",
            "summary": "Events API v1",
            "self": "https://api.pagerduty.com/vendors/TESTVENDOR2",
            "html_url": None,
        },
        "vendor_name": "Amazon CloudWatch",
        "service": {
            "id": "TESTSERVICE1",
            "summary": "Service",
            "type": "service",
            "self": "https://api.pagerduty.com/services/TESTSERVICE1",
            "html_url": "https://subdomain.pagerduty.com/services/TESTSERVICE1",
            "name": "Service",
            "auto_resolve_timeout": 14400,
            "acknowledgement_timeout": 600,
            "created_at": "2015-11-06T11:12:51-05:00",
            "status": "active",
            "alert_creation": "create_alerts_and_incidents",
            "alert_grouping_parameters": {"type": "intelligent"},
            "escalation_policy": {
                "id": "TESTPOL1",
                "type": "escalation_policy_reference",
                "summary": "Another Escalation Policy",
                "self": "https://api.pagerduty.com/escalation_policies/TESTPOL1",
                "html_url": "https://subdomain.pagerduty.com/escalation_policies/TESTPOL1",
            },
            "teams": [],
            "incident_urgency_rule": {"type": "constant", "urgency": "high"},
            "support_hours": None,
            "scheduled_actions": [],
        },
        "oncall_integration": None,
        "oncall_type": None,
        "is_escalation_policy_flawed": False,
    },
    {
        "id": "TESTINT3",
        "type": "generic_events_api_inbound_integration",
        "summary": "Test Integration",
        "self": "https://api.pagerduty.com/services/TESTSERVICE1/integrations/TESTINT3",
        "html_url": "https://subdomain.pagerduty.com/services/TESTSERVICE1/integrations/TESTINT3",
        "name": "Test Integration",
        "created_at": "2021-04-27T09:34:17-04:00",
        "vendor": {
            "id": "TESTVENDOR1",
            "type": "vendor_reference",
            "summary": "Events API v1",
            "self": "https://api.pagerduty.com/vendors/TESTVENDOR1",
            "html_url": None,
        },
        "vendor_name": "Datadog",
        "service": {
            "id": "TESTSERVICE2",
            "summary": "My Application Service",
            "type": "service",
            "self": "https://api.pagerduty.com/services/TESTSERVICE2",
            "html_url": "https://subdomain.pagerduty.com/services/TESTSERVICE2",
            "name": "My Application Service",
            "auto_resolve_timeout": 14400,
            "acknowledgement_timeout": 600,
            "created_at": "2015-11-06T11:12:51-05:00",
            "status": "active",
            "alert_creation": "create_alerts_and_incidents",
            "alert_grouping_parameters": {"type": "intelligent"},
            "escalation_policy": {
                "id": "TESTPOL2",
                "type": "escalation_policy_reference",
                "summary": "Another Escalation Policy",
                "self": "https://api.pagerduty.com/escalation_policies/TESTPOL2",
                "html_url": "https://subdomain.pagerduty.com/escalation_policies/TESTPOL2",
            },
            "teams": [],
            "incident_urgency_rule": {"type": "constant", "urgency": "high"},
            "support_hours": None,
            "scheduled_actions": [],
        },
        "oncall_integration": None,
        "oncall_type": "datadog",
        "is_escalation_policy_flawed": True,
    },
    {
        "id": "TESTINT4",
        "type": "generic_events_api_inbound_integration",
        "summary": "Test Integration 2",
        "self": "https://api.pagerduty.com/services/TESTSERVICE1/integrations/TESTINT4",
        "html_url": "https://subdomain.pagerduty.com/services/TESTSERVICE1/integrations/TESTINT4",
        "name": "Test Integration 2",
        "created_at": "2021-04-27T09:34:17-04:00",
        "vendor": {
            "id": "TESTVENDOR2",
            "type": "vendor_reference",
            "summary": "Events API v1",
            "self": "https://api.pagerduty.com/vendors/TESTVENDOR2",
            "html_url": None,
        },
        "vendor_name": "Amazon CloudWatch",
        "service": {
            "id": "TESTSERVICE2",
            "summary": "My Application Service",
            "type": "service",
            "self": "https://api.pagerduty.com/services/TESTSERVICE2",
            "html_url": "https://subdomain.pagerduty.com/services/TESTSERVICE2",
            "name": "My Application Service",
            "auto_resolve_timeout": 14400,
            "acknowledgement_timeout": 600,
            "created_at": "2015-11-06T11:12:51-05:00",
            "status": "active",
            "alert_creation": "create_alerts_and_incidents",
            "alert_grouping_parameters": {"type": "intelligent"},
            "escalation_policy": {
                "id": "TESTPOL2",
                "type": "escalation_policy_reference",
                "summary": "Another Escalation Policy",
                "self": "https://api.pagerduty.com/escalation_policies/TESTPOL2",
                "html_url": "https://subdomain.pagerduty.com/escalation_policies/TESTPOL2",
            },
            "teams": [],
            "incident_urgency_rule": {"type": "constant", "urgency": "high"},
            "support_hours": None,
            "scheduled_actions": [],
        },
        "oncall_integration": None,
        "oncall_type": None,
        "is_escalation_policy_flawed": True,
    },
    {
        "id": "TESTINT5",
        "type": "generic_events_api_inbound_integration",
        "summary": "Test Integration",
        "self": "https://api.pagerduty.com/services/TESTSERVICE1/integrations/TESTINT5",
        "html_url": "https://subdomain.pagerduty.com/services/TESTSERVICE1/integrations/TESTINT5",
        "name": "Test Integration",
        "created_at": "2021-04-27T09:34:17-04:00",
        "vendor": {
            "id": "TESTVENDOR1",
            "type": "vendor_reference",
            "summary": "Events API v1",
            "self": "https://api.pagerduty.com/vendors/TESTVENDOR1",
            "html_url": None,
        },
        "vendor_name": "Datadog",
        "service": {
            "id": "TESTSERVICE2",
            "summary": "My Application Service",
            "type": "service",
            "self": "https://api.pagerduty.com/services/TESTSERVICE2",
            "html_url": "https://subdomain.pagerduty.com/services/TESTSERVICE2",
            "name": "My Application Service",
            "auto_resolve_timeout": 14400,
            "acknowledgement_timeout": 600,
            "created_at": "2015-11-06T11:12:51-05:00",
            "status": "active",
            "alert_creation": "create_alerts_and_incidents",
            "alert_grouping_parameters": {"type": "intelligent"},
            "escalation_policy": {
                "id": "TESTPOL5",
                "type": "escalation_policy_reference",
                "summary": "Another Escalation Policy",
                "self": "https://api.pagerduty.com/escalation_policies/TESTPOL5",
                "html_url": "https://subdomain.pagerduty.com/escalation_policies/TESTPOL5",
            },
            "teams": [],
            "incident_urgency_rule": {"type": "constant", "urgency": "high"},
            "support_hours": None,
            "scheduled_actions": [],
        },
        "oncall_integration": None,
        "oncall_type": "datadog",
        "is_escalation_policy_flawed": True,
    },
    {
        "id": "TESTINT6",
        "type": "generic_events_api_inbound_integration",
        "summary": "Test Integration 2",
        "self": "https://api.pagerduty.com/services/TESTSERVICE1/integrations/TESTINT6",
        "html_url": "https://subdomain.pagerduty.com/services/TESTSERVICE1/integrations/TESTINT6",
        "name": "Test Integration 2",
        "created_at": "2021-04-27T09:34:17-04:00",
        "vendor": {
            "id": "TESTVENDOR2",
            "type": "vendor_reference",
            "summary": "Events API v1",
            "self": "https://api.pagerduty.com/vendors/TESTVENDOR2",
            "html_url": None,
        },
        "vendor_name": "Amazon CloudWatch",
        "service": {
            "id": "TESTSERVICE2",
            "summary": "My Application Service",
            "type": "service",
            "self": "https://api.pagerduty.com/services/TESTSERVICE2",
            "html_url": "https://subdomain.pagerduty.com/services/TESTSERVICE2",
            "name": "My Application Service",
            "auto_resolve_timeout": 14400,
            "acknowledgement_timeout": 600,
            "created_at": "2015-11-06T11:12:51-05:00",
            "status": "active",
            "alert_creation": "create_alerts_and_incidents",
            "alert_grouping_parameters": {"type": "intelligent"},
            "escalation_policy": {
                "id": "TESTPOL5",
                "type": "escalation_policy_reference",
                "summary": "Another Escalation Policy",
                "self": "https://api.pagerduty.com/escalation_policies/TESTPOL5",
                "html_url": "https://subdomain.pagerduty.com/escalation_policies/TESTPOL5",
            },
            "teams": [],
            "incident_urgency_rule": {"type": "constant", "urgency": "high"},
            "support_hours": None,
            "scheduled_actions": [],
        },
        "oncall_integration": None,
        "oncall_type": None,
        "is_escalation_policy_flawed": True,
    },
    {
        "id": "TESTINT7",
        "type": "generic_email_inbound_integration_reference",
        "summary": "Email Integration",
        "self": "https://api.pagerduty.com/services/TESTSERVICE1/integrations/TESTINT7",
        "html_url": "https://subdomain.pagerduty.com/services/TESTSERVICE1/integrations/TESTINT7",
        "name": "Email Integration",
        "created_at": "2021-04-27T09:34:17-04:00",
        "vendor": {
            "id": "TESTVENDOR3",
            "type": "vendor_reference",
            "summary": "Email",
            "self": "https://api.pagerduty.com/vendors/TESTVENDOR3",
            "html_url": None,
        },
        "vendor_name": "Email",
        "service": {
            "id": "TESTSERVICE1",
            "summary": "My Application Service",
            "type": "service",
            "self": "https://api.pagerduty.com/services/TESTSERVICE1",
            "html_url": "https://subdomain.pagerduty.com/services/TESTSERVICE1",
            "name": "My Application Service",
            "auto_resolve_timeout": 14400,
            "acknowledgement_timeout": 600,
            "created_at": "2015-11-06T11:12:51-05:00",
            "status": "active",
            "alert_creation": "create_alerts_and_incidents",
            "alert_grouping_parameters": {"type": "intelligent"},
            "escalation_policy": {
                "id": "TESTPOL1",
                "type": "escalation_policy_reference",
                "summary": "Another Escalation Policy",
                "self": "https://api.pagerduty.com/escalation_policies/TESTPOL1",
                "html_url": "https://subdomain.pagerduty.com/escalation_policies/TESTPOL1",
            },
            "teams": [],
            "incident_urgency_rule": {"type": "constant", "urgency": "high"},
            "support_hours": None,
            "scheduled_actions": [],
        },
        "oncall_integration": None,
        "oncall_type": None,
        "is_escalation_policy_flawed": False,
    },
]


def test_match_user():
    for user in pd_users_payload:
        match_user(user, oncall_users_payload)

    assert pd_users_payload == expected_users_match_result


def test_match_user_not_found():
    pd_user = {"email": "test@test.com"}
    oncall_users = [{"email": "test1@test.com"}]

    match_user(pd_user, oncall_users)
    assert pd_user["oncall_user"] is None


def test_match_schedule():
    for schedule in pd_schedules_payload:
        match_schedule(schedule, oncall_schedules_payload, user_id_map={})
        match_users_for_schedule(schedule, pd_users_payload)

    assert pd_schedules_payload == expected_schedules_result


def test_match_escalation_policy():
    for policy in pd_escalation_policies_payload:
        match_escalation_policy(policy, oncall_escalation_chains)
        match_users_and_schedules_for_escalation_policy(
            policy, pd_users_payload, pd_schedules_payload
        )

    assert pd_escalation_policies_payload == expected_escalation_policies_result


def test_match_integration():
    integrations = []
    for service in pd_services_payload:
        service_integrations = service.pop("integrations")
        for integration in service_integrations:
            integration["service"] = service
            integrations.append(integration)

    for integration in integrations:
        match_integration(integration, oncall_integrations)
        match_integration_type(integration, pd_vendors_payload)
        match_escalation_policy_for_integration(
            integration, pd_escalation_policies_payload
        )

    assert integrations == expected_integrations_result
