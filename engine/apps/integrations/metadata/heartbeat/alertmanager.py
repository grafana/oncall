from pathlib import PurePath

from apps.integrations.metadata.heartbeat._heartbeat_text_creator import HeartBeatTextCreator

integration_verbal = PurePath(__file__).stem
creator = HeartBeatTextCreator(integration_verbal)
heartbeat_text = creator.get_heartbeat_texts()


heartbeat_expired_title = heartbeat_text.heartbeat_expired_title
heartbeat_expired_message = heartbeat_text.heartbeat_expired_message

heartbeat_expired_payload = {
    "alerts": [
        {
            "endsAt": "",
            "labels": {
                "alertname": "OnCallHeartBeatMissing",
            },
            "status": "firing",
            "startsAt": "",
            "annotations": {
                "title": heartbeat_expired_title,
                "description": heartbeat_expired_message,
            },
            "fingerprint": "fingerprint",
            "generatorURL": "",
        },
    ],
    "status": "firing",
    "version": "4",
    "groupKey": '{}:{alertname="OnCallHeartBeatMissing"}',
    "receiver": "",
    "numFiring": 1,
    "externalURL": "",
    "groupLabels": {"alertname": "OnCallHeartBeatMissing"},
    "numResolved": 0,
    "commonLabels": {"alertname": "OnCallHeartBeatMissing"},
    "truncatedAlerts": 0,
    "commonAnnotations": {
        "title": heartbeat_expired_title,
        "description": heartbeat_expired_message,
    },
}

heartbeat_restored_title = heartbeat_text.heartbeat_restored_title
heartbeat_restored_message = heartbeat_text.heartbeat_restored_message


heartbeat_restored_payload = {
    "alerts": [
        {
            "endsAt": "",
            "labels": {
                "alertname": "OnCallHeartBeatMissing",
            },
            "status": "resolved",
            "startsAt": "",
            "annotations": {
                "title": heartbeat_restored_title,
                "description": heartbeat_restored_message,
            },
            "fingerprint": "fingerprint",
            "generatorURL": "",
        },
    ],
    "status": "resolved",
    "version": "4",
    "groupKey": '{}:{alertname="OnCallHeartBeatMissing"}',
    "receiver": "",
    "numFiring": 0,
    "externalURL": "",
    "groupLabels": {"alertname": "OnCallHeartBeatMissing"},
    "numResolved": 1,
    "commonLabels": {"alertname": "OnCallHeartBeatMissing"},
    "truncatedAlerts": 0,
    "commonAnnotations": {
        "title": heartbeat_restored_title,
        "description": heartbeat_restored_message,
    },
}
