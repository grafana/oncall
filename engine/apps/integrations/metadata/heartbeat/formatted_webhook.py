from pathlib import PurePath

from apps.integrations.metadata.heartbeat._heartbeat_text_creator import HeartBeatTextCreator

integration_verbal = PurePath(__file__).stem
creator = HeartBeatTextCreator(integration_verbal)
heartbeat_text = creator.get_heartbeat_texts()


heartbeat_expired_title = heartbeat_text.heartbeat_expired_title
heartbeat_expired_message = heartbeat_text.heartbeat_expired_message

heartbeat_expired_payload = {
    "alert_uid": "fbdad422-b27d-454a-8553-84d1517e0005",
    "title": heartbeat_expired_title,
    "image_url": None,
    "state": "alerting",
    "link_to_upstream_details": None,
    "message": heartbeat_expired_message,
    "is_oncall_heartbeat": True,
    "is_oncall_heartbeat_restored": False,
    "is_amixr_heartbeat": True,  # Keep for backwards compatibility
    "is_amixr_heartbeat_restored": False,  # Keep for backwards compatibility
}

heartbeat_restored_title = heartbeat_text.heartbeat_restored_title
heartbeat_restored_message = heartbeat_text.heartbeat_restored_message

heartbeat_restored_payload = {
    "alert_uid": "fbdad422-b27d-454a-8553-84d1517e0005",
    "title": heartbeat_restored_title,
    "image_url": None,
    "state": "ok",
    "link_to_upstream_details": None,
    "message": heartbeat_restored_message,
    "is_oncall_heartbeat": True,
    "is_oncall_heartbeat_restored": True,
    "is_amixr_heartbeat": True,  # Keep for backwards compatibility
    "is_amixr_heartbeat_restored": True,  # Keep for backwards compatibility
}
