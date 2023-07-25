from apps.integrations.metadata import heartbeat


def test_heartbeat_metadata_presence():
    necessary_attrs = [
        "heartbeat_expired_title",
        "heartbeat_expired_message",
        "heartbeat_expired_payload",
        "heartbeat_restored_title",
        "heartbeat_restored_message",
        "heartbeat_restored_payload",
    ]
    modules = [x for x in dir(heartbeat) if not x.startswith("_") and x != "apps"]
    for m in modules:
        m = getattr(heartbeat, m)
        for attr in necessary_attrs:
            assert getattr(m, attr) is not None
