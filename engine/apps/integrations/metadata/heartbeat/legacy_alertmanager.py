from pathlib import PurePath

from apps.integrations.metadata.heartbeat._heartbeat_text_creator import HeartBeatTextCreatorForTitleGrouping

integration_verbal = PurePath(__file__).stem
creator = HeartBeatTextCreatorForTitleGrouping(integration_verbal)
heartbeat_text = creator.get_heartbeat_texts()

heartbeat_expired_title = heartbeat_text.heartbeat_expired_title
heartbeat_expired_message = heartbeat_text.heartbeat_expired_message

heartbeat_expired_payload = {
    "endsAt": "",
    "labels": {"alertname": heartbeat_expired_title},
    "status": "firing",
    "startsAt": "",
    "annotations": {
        "message": heartbeat_expired_message,
    },
    "generatorURL": None,
}

heartbeat_restored_title = heartbeat_text.heartbeat_restored_title
heartbeat_restored_message = heartbeat_text.heartbeat_restored_message

heartbeat_restored_payload = {
    "endsAt": "",
    "labels": {"alertname": heartbeat_restored_title},
    "status": "resolved",
    "startsAt": "",
    "annotations": {"message": heartbeat_restored_message},
    "generatorURL": None,
}
