from pathlib import PurePath

from apps.integrations.metadata.heartbeat._heartbeat_text_creator import HearBeatTextCreator

integration_verbal = PurePath(__file__).stem
creator = HearBeatTextCreator(integration_verbal)
heartbeat_text = creator.get_heartbeat_texts()

heartbeat_instruction_template = heartbeat_text.heartbeat_instruction_template

heartbeat_expired_title = heartbeat_text.heartbeat_expired_title
heartbeat_expired_message = heartbeat_text.heartbeat_expired_message

heartbeat_expired_payload = {
    "alert_uid": "191eac7a-d7c1-43a0-8821-eef5afe41367",
    "title": heartbeat_expired_title,
    "image_url": None,
    "state": "alerting",
    "link_to_upstream_details": None,
    "message": heartbeat_expired_message,
    "is_amixr_heartbeat": True,
    "is_amixr_heartbeat_restored": False,
}

heartbeat_restored_title = heartbeat_text.heartbeat_restored_title
heartbeat_restored_message = heartbeat_text.heartbeat_restored_message

heartbeat_restored_payload = {
    "alert_uid": "191eac7a-d7c1-43a0-8821-eef5afe41367",
    "title": heartbeat_restored_title,
    "image_url": None,
    "state": "ok",
    "link_to_upstream_details": None,
    "message": heartbeat_restored_message,
    "is_amixr_heartbeat": True,
    "is_amixr_heartbeat_restored": True,
}
