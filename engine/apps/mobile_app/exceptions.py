class DeviceNotSet(Exception):
    """
    Indicates that user has no connected fcm device.
    Introduced only for test_push_notification handler.
    We should have generic test notifications system across all messaging backends.
    """
